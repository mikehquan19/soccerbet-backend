"""
LOGIC TO SETTLE THE BETs
"""

from .models import (
    User, TotalObjectsBetInfo, HandicapBetInfo, 
    UserMoneylineBet, UserHandicapBet, UserTotalObjectsBet
)

"""
get the result of the bet info from its match
return team winning the match and total bet objects
"""
def get_results(bet_info, handicap_cover=None) -> tuple:
    """
    determine the appropriate score of the game based on the time type 
    the default object to bet is Goals
    """
    if bet_info.time_type == "full time": 
        target_result = bet_info.match.fulltime_score.split("-")
    elif bet_info.time_type == "half time": 
        target_result = bet_info.match.halftime_score.split("-")
    
    if bet_info.bet_object == "Corners": 
        target_result = bet_info.match.corners.split("-")
    elif bet_info.bet_object == "Cards": 
        target_result = bet_info.match.cards.split("-")
        
    home_team_result, away_team_result = int(target_result[0]), int(target_result[-1])
    total_objs = home_team_result + away_team_result

    # if there is a handicap cover, apply the handicap cover to the bet team 
    if handicap_cover is not None:  
        if bet_info.bet_team == bet_info.match.home_team: 
            home_team_result += handicap_cover
        elif bet_info.bet_team == bet_info.match.away_team: 
            away_team_result += handicap_cover 
    
    # determine the winning team based on the score 
    win_team = "Draw" # default when both teams draw 
    if home_team_result > away_team_result: 
        win_team = bet_info.match.home_team
    elif home_team_result < away_team_result: 
        win_team = bet_info.match.away_team

    # outcome (including the handicap cover) and total object bets  of the game 
    return win_team, total_objs


# compute the payout of the bet based on the odd of the bet and the bet amount
def compute_payout(arg_odd, bet_amount): 
    if arg_odd > 0: 
        total_payout = round(bet_amount + (bet_amount * arg_odd) / 100, 2)
    else: # the american odd will have to be less than 0, it can't be 0
        total_payout = round(bet_amount + (bet_amount * 100) / abs(arg_odd), 2)
    return total_payout


# determine final payout of the moneyline or handicap bet
def determine_winner_payout(bet_info, bet_amount, handicap_cover=None): 
    """
        determine if it's Asian handicap, 
        then recursively settle 2 European bets corresponding to this Asian bet, return the sum of payout
    """
    if handicap_cover is not None:
        cover_decimal = handicap_cover - int(handicap_cover) 
        if cover_decimal == 0.25 or cover_decimal == 0.75: 
            first_payout = determine_winner_payout(bet_info, bet_amount / 2, handicap_cover - 0.25)
            second_payout = determine_winner_payout(bet_info, bet_amount / 2, handicap_cover + 0.25)
            # total payout is the sum of 2 payouts 
            return first_payout + second_payout
    
    try: # if it's not asian handicap, determine the payout as usual 
        win_team, _ = get_results(bet_info, handicap_cover)
    except ValueError: 
        total_payout = bet_amount
    else: 
        total_payout = 0 # default when the win team doesn't match bet team, user loses and get nothing back
        if win_team == bet_info.bet_team: 
            total_payout = compute_payout(bet_info.odd, bet_amount)
    return total_payout


# determine the final payout of the total objects bet 
def determine_total_objs_payout(bet_info: TotalObjectsBetInfo, bet_amount, target_num_objs): 
    """
        determine if it's Asian total objs bet, 
        then recursively settle 2 European bets corresponding to this Asian bet, return the sum of payout
    """
    num_decimal = target_num_objs - int(target_num_objs)
    if num_decimal == 0.25 or num_decimal == 0.75: 
        first_payout = determine_total_objs_payout(bet_info, bet_amount / 2, target_num_objs - 0.25)
        second_payout = determine_total_objs_payout(bet_info, bet_amount / 2, target_num_objs + 0.25)
        # total payout is the sum of 2 payouts 
        return first_payout + second_payout
            
    try:  # determine the total objs of the match as usual 
        _, total_bet_objs = get_results(bet_info)
    except ValueError: 
        total_payout = bet_amount
    else: 
        # determine if the user win the bet based on the number of goals 
        win_the_bet = None 
        # if the number of goals equals target, win_the_bet is still None 
        if total_bet_objs < target_num_objs: 
            win_the_bet = True if bet_info.under_or_over == "Under" else False 
        elif total_bet_objs > target_num_objs: 
            win_the_bet = True if bet_info.under_or_over == "Over" else False 
            
        if win_the_bet is None: 
            # total goals is equal to target number of goals, the money will be refunded to the user 
            total_payout = bet_amount 
        else: 
            total_payout = 0 # the user loses the bet 
            if win_the_bet: total_payout = compute_payout(bet_info.odd, bet_amount)
    return total_payout


def settle_bet_list(bet_type: str, arg_bet_list) -> int: 
    arg_bet_list = arg_bet_list.order_by("user") # group the list by users 

    updated_user_list, updated_bet_list, user_ix = [], [], 0
    for i, arg_bet in enumerate(arg_bet_list):  
        updated_bet_list.append(arg_bet) # add the bet to the list of updated bets 
        if i == 0: # add the first user to the list 
            updated_user_list.append(arg_bet.user)
        elif i != 0 and arg_bet.user != updated_user_list[user_ix]: 
            # add the user 
            updated_user_list.append(arg_bet.user)
            user_ix += 1

        bet_info = arg_bet.bet_info # the info of the this moneyline or handicap bet 
        bet_amount = arg_bet.bet_amount # the amount the user bet on this info

        if bet_type == "total_objs": 
            total_payout = determine_total_objs_payout(bet_info, bet_amount, bet_info.target_num_objects)
        else: 
            if isinstance(bet_info, HandicapBetInfo): handicap_cover = bet_info.handicap_cover
            total_payout = determine_winner_payout(bet_info, bet_amount, handicap_cover)
    
        # update the payout of the bets and balance of the user 
        updated_bet_list[i].payout = total_payout
        updated_user_list[user_ix].balance += total_payout

    # update the payout of the bets
    if bet_type == "moneyline": 
        num_updated_bets = UserMoneylineBet.objects.bulk_update(updated_bet_list, ["payout"])
    elif bet_type == "handicap": 
        num_updated_bets = UserHandicapBet.objects.bulk_update(updated_bet_list, ["payout"])
    elif bet_type ==  "total_objs": 
        num_updated_bets = UserTotalObjectsBet.objects.bulk_update(updated_bet_list, ["payout"])
    else: 
        raise Exception("The bet type is invalid.")
    
    # update the balance of the users
    User.objects.bulk_update(updated_user_list, ["balance"]) # update the user's balance
    return num_updated_bets
