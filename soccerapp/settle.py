"""
LOGIC TO SETTLE THE BETs
TODO: WRITE TESTS ON THESE FUNCTIONS  
"""

from django.db.models import QuerySet
from .models import (
    User, Match, HandicapBetInfo,
    UserMoneylineBet, UserHandicapBet, UserTotalGoalsBet
)

# get the result of the bet from the match's outcome and bet info
# return team winning the match (str) and total goals 
def get_results(arg_match: Match, arg_bet_info) -> tuple: 
    # determine the appropriate score of the game based on the time type 
    if arg_bet_info.time_type == "full time": 
        target_score = arg_match.fulltime_score.split("-")
    elif arg_bet_info.time_type == "half time": 
        target_score = arg_match.halftime_score.split("-")
    else: 
        # if the time type is not either "full time" nor "half time", raise and error 
        raise ValueError("Time type is not found.")
    home_team_score, away_team_score = int(target_score[0]), int(target_score[-1])
    total_goals = home_team_score + away_team_score

    # if the arg_bet is the handicapbet, apply the handicap cover to the bet team 
    if isinstance(arg_bet_info, HandicapBetInfo):  
        if arg_bet_info.bet_team == arg_match.home_team: 
            home_team_score += arg_bet_info.handicap_cover
        elif arg_bet_info.bet_team == arg_match.away_team: 
            away_team_score += arg_bet_info.handicap_cover 
    
    # determine the winning team based on the score 
    if home_team_score > away_team_score: 
        win_team = arg_match.home_team
    elif home_team_score < away_team_score: 
        win_team = arg_match.away_team
    else: 
        win_team = "Draw"

    # outcome (including the handicap cover) and total goals of the game 
    return win_team, total_goals
    

# settle the list of moneyline bets grouped by users, return the number of updated bets 
def settle_moneyline_bet_list(moneyline_bet_list: QuerySet[UserMoneylineBet]) -> int: 
    updated_user_list, updated_bet_list, user_ix = [], [], 0
    for i, moneyline_bet in enumerate(moneyline_bet_list):  
        updated_bet_list.append(moneyline_bet) # add the bet to the list of updated bets 
        
        if i == 0: # add the first user to the list 
            updated_user_list.append(moneyline_bet.user)
        elif i != 0 and moneyline_bet.user != updated_user_list[user_ix]: 
            # add the following user 
            updated_user_list.append(moneyline_bet.user)
            user_ix += 1

        bet_info = moneyline_bet.bet_info # the info of the this moneyline bet 
        bet_amount = moneyline_bet.bet_amount # the amount the user bet on this info

        # determine the winning team of the match 
        this_bet_match = bet_info.match
        win_team, _ = get_results(this_bet_match, bet_info)

        # compute the total payout to the user based on the result 
        if win_team == bet_info.bet_team: 
            if bet_info.odd > 0: 
                total_payout = round(bet_amount + (bet_amount * bet_info.odd) / 100, 2)
            else: 
                # the american odd will have to be less than 0, it can't be 0
                total_payout = round(bet_amount + (bet_amount * 100) / abs(bet_info.odd), 2)
        else: # otherwise, they lose and they get nothing back 
            total_payout = 0
        # update the payout of the bets and balance of the user 
        updated_bet_list[i].payout = total_payout
        updated_user_list[user_ix].balance += total_payout

    num_updated_bets = UserMoneylineBet.objects.bulk_update(updated_bet_list, ["payout"])
    User.objects.bulk_update(updated_user_list, ["balance"])
    return num_updated_bets
    

# settle the list of handicap bets grouped by users
def settle_handicap_bet_list(handicap_bet_list: QuerySet[UserHandicapBet]) -> int: 
    updated_user_list, updated_bet_list, user_ix = [], [], 0 # list of user and bet to be updated 
    for i, handicap_bet in enumerate(handicap_bet_list): 
        updated_bet_list.append(handicap_bet)

        if i == 0: # add the first user to the list 
            updated_user_list.append(handicap_bet.user)
        elif i != 0 and handicap_bet.user != updated_user_list[user_ix]: 
            # add the following user 
            updated_user_list.append(handicap_bet.user)
            user_ix += 1

        bet_info = handicap_bet.bet_info
        bet_amount = handicap_bet.bet_amount

        # determine the winning team and the score handicap of the match 
        this_bet_match = bet_info.match
        win_team, _ = get_results(this_bet_match, bet_info)

        # determine whether the user wins the bet based on the result and handicap
        # compute the total payout to the user based on the result 
        if win_team == bet_info.bet_team: # if the bet team is the win team, user wins 
            if bet_info.odd > 0: 
                total_payout = round(bet_amount + (bet_amount * bet_info.odd) / 100, 2)
            else: 
                # the american odd will have to be less than 0, it can't be 0
                total_payout = round(bet_amount + (bet_amount * 100) / abs(bet_info.odd), 2)
        else: # otherwise
            total_payout = bet_amount if win_team == "Draw" else 0
        # update the bet's payout and the user's balance 
        updated_bet_list[i].payout = total_payout
        updated_user_list[user_ix].balance += total_payout

    num_updated_bets = UserHandicapBet.objects.bulk_update(updated_bet_list, ["payout"])
    User.objects.bulk_update(updated_user_list, ["balance"])
    return num_updated_bets

# settle the list of total goals bet 
def settle_total_goals_bet_list(total_goals_bet_list: QuerySet[UserTotalGoalsBet]) -> int: 
    updated_user_list, updated_bet_list, user_ix = [], [], 0
    for i, total_goals_bet in enumerate(total_goals_bet_list): 
        updated_bet_list.append(total_goals_bet)

        if i == 0: # add the first user to the list 
            updated_user_list.append(total_goals_bet.user)
        elif i != 0 and total_goals_bet.user != updated_user_list[user_ix]: 
            # add the following user 
            updated_user_list.append(total_goals_bet.user)
            user_ix += 1

        bet_info = total_goals_bet.bet_info
        bet_amount = total_goals_bet.bet_amount

        # determin the total goals of the match 
        this_bet_match = bet_info.match 
        _, total_goals = get_results(this_bet_match, bet_info)

        # determine if the user wind the bet based on the number of goals 
        win_the_bet = None 
        # if the number of goals = target, win_the_bet is still None 
        if total_goals < bet_info.target_num_goals: 
            win_the_bet = True if bet_info.under_or_over == "Under" else False 
        elif total_goals > bet_info.target_num_goals: 
            win_the_bet = True if bet_info.under_or_over == "Over" else False 
        
        # compute payout 
        if win_the_bet is None: 
            # if win_the_bet = None means that the total goals is equal to target number of goals 
            # the money will be refunded to the user 
            total_payout = bet_amount 
        else: 
            if win_the_bet: 
                if bet_info.odd > 0: 
                    total_payout = round(bet_amount + (bet_amount * bet_info.odd) / 100, 2)
                else: 
                    # the american odd will have to be less than 0, it can't be 0
                    total_payout = round(bet_amount + (bet_amount * 100) / abs(bet_info.odd), 2)
            else: # the user loses the bet 
                total_payout = 0
        # update the user's balance and bet's payout 
        updated_bet_list[i].payout = total_payout
        updated_user_list[user_ix].balance += total_payout
    
    num_updated_bets = User.objects.bulk_update(updated_user_list, ["balance"])
    UserTotalGoalsBet.objects.bulk_update(updated_bet_list, ["payout"])
    return num_updated_bets