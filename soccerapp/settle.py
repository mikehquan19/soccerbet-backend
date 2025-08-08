"""LOGIC TO SETTLE THE BETS"""

from .models import (
    User, TotalObjectsBetInfo, HandicapBetInfo, UserMoneylineBet, UserHandicapBet, UserTotalObjectsBet
)
from decimal import Decimal


def get_results(bet_info, handicap_cover=None) -> tuple:
    """ Get the result of the bet info from its match. Return team winning the match 
    and total bet objects """

    # if it's goals, determine whether it's full-time or half-time 
    if bet_info.time_type == "full time": 
        target_result = bet_info.match.fulltime_score.split("-")
    elif bet_info.time_type == "half time": 
        target_result = bet_info.match.halftime_score.split("-")
    
    # if it's not goals, determine whether it's Corners or Cards. 
    if bet_info.bet_object == "Corners": 
        target_result = bet_info.match.corners.split("-")
    elif bet_info.bet_object == "Cards": 
        target_result = bet_info.match.cards.split("-")
        
    # total number of objects 
    home_team_result, away_team_result = int(target_result[0]), int(target_result[-1])
    total_objs = home_team_result + away_team_result

    # if there is a handicap cover, apply the handicap cover to the bet team 
    if handicap_cover is not None:  
        if bet_info.bet_team == bet_info.match.home_team: 
            home_team_result += handicap_cover
        elif bet_info.bet_team == bet_info.match.away_team: 
            away_team_result += handicap_cover 
    
    win_team = "Draw" # determine the winning team based on the score, default when both teams draw 

    if home_team_result > away_team_result: 
        win_team = bet_info.match.home_team
    elif home_team_result < away_team_result: 
        win_team = bet_info.match.away_team

    # outcome (including the handicap cover) and total object bets  of the game 
    return win_team, total_objs


def compute_payout(arg_odd, bet_amount): 
    """ Compute the payout of the bet based on the odd of the bet and the bet amount """

    if arg_odd > 0: 
        total_payout = round(bet_amount + (bet_amount * arg_odd) / 100, 2)
    else: 
        # the american odd will have to be less than 0, it can't be 0
        total_payout = round(bet_amount + (bet_amount * 100) / abs(arg_odd), 2)
    return total_payout


def determine_winner_payout(bet_info, bet_amount, handicap_cover=None): 
    """ Determine final payout of the moneyline or handicap bet """

    if handicap_cover != None:
        """
        if it's Asian handicap, recursively settle 2 European bets corresponding to this Asian bet, 
        return the sum of payout
        """
        cover_decimal = abs(float(handicap_cover - int(handicap_cover))) 
        if cover_decimal == 0.25 or cover_decimal == 0.75: 
            payout1 = determine_winner_payout(
                bet_info, bet_amount / 2, handicap_cover - Decimal(0.25)
            )
            payout2 = determine_winner_payout(
                bet_info, bet_amount / 2, handicap_cover + Decimal(0.25)
            )
            return payout1 + payout2 # total payout is the sum of 2 payouts 
    
    # if it's not asian handicap, determine the payout as usual 
    try:
        win_team, _ = get_results(bet_info, handicap_cover)
    except ValueError: 
        # the value error indicates that results not available, there's nothing to settle
        # and we will refund the money back to the user
        total_payout = bet_amount
    else: 
        # default when the win team doesn't match bet team, user loses and get nothing back
        total_payout = 0 
        if win_team == "Draw": 
            # if the 2 teams of the game draw (considering the handicap cover), 
            # we will refund the bet
            total_payout = bet_amount 
        elif win_team == bet_info.bet_team: 
            total_payout = compute_payout(bet_info.odd, bet_amount)
    return total_payout


def determine_total_objs_payout(bet_info: TotalObjectsBetInfo, bet_amount, target_num_objs): 
    """ Determine the final payout of the total objects bet """

    num_decimal = abs(float(target_num_objs - int(target_num_objs)))
    if num_decimal == 0.25 or num_decimal == 0.75: 
        # if it's asian total objects bet, 
        # then recursively settle 2 European bets, return the sum of payout
        first_payout = determine_total_objs_payout(bet_info, bet_amount / 2, target_num_objs - Decimal(0.25))
        second_payout = determine_total_objs_payout(bet_info, bet_amount / 2, target_num_objs + Decimal(0.25)) 

        # return total payout is the sum of 2 payouts
        return first_payout + second_payout 

    # determine the total objects of the match as usual   
    try: 
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
            if win_the_bet: 
                total_payout = compute_payout(bet_info.odd, bet_amount)
                
    return total_payout


def settle_bet_list(bet_type: str, arg_bet_list) -> int: 
    """ The main function: settle the queryset of bets of any type """
    
    arg_bet_list = arg_bet_list.order_by("user") # group the list by users 

    updated_user_list, updated_bet_list = [], []
    user_i = 0
    for i, arg_bet in enumerate(arg_bet_list):  
        updated_bet_list.append(arg_bet) # add the bet to the list of updated bets 

        # add the first user to the list 
        if i == 0: 
            updated_user_list.append(arg_bet.user)
        elif i != 0 and arg_bet.user != updated_user_list[user_i]: 
            updated_user_list.append(arg_bet.user)
            user_i += 1

        bet_info = arg_bet.bet_info # the info of the this moneyline or handicap bet 
        bet_amount = arg_bet.bet_amount # the amount the user bet on this info

        if bet_type == "total_objs": 
            total_payout = determine_total_objs_payout(bet_info, bet_amount, bet_info.target_num_objects)
        else: 
            handicap_cover = None
            if isinstance(bet_info, HandicapBetInfo): 
                handicap_cover = bet_info.handicap_cover
            total_payout = determine_winner_payout(bet_info, bet_amount, handicap_cover)
    
        # update the payout of the bets and balance of the user 
        updated_bet_list[i].payout = total_payout
        updated_user_list[user_i].balance += total_payout

    # update the payout of the list of bets
    if bet_type == "moneyline": 
        num_updated_bets = UserMoneylineBet.objects.bulk_update(updated_bet_list, ["payout"])
    elif bet_type == "handicap": 
        num_updated_bets = UserHandicapBet.objects.bulk_update(updated_bet_list, ["payout"])
    elif bet_type ==  "total_objs": 
        num_updated_bets = UserTotalObjectsBet.objects.bulk_update(updated_bet_list, ["payout"])
    else: 
        raise Exception("The bet type is invalid.")
    
    # update the balance of the list of users
    User.objects.bulk_update(updated_user_list, ["balance"]) 
    return num_updated_bets
