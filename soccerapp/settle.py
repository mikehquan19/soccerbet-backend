"""
LOGIC TO SETTLE THE BETs
TODO: WRITE TESTS ON THESE FUNCTIONS  
"""

from django.db.models import QuerySet
from .models import (
    User, Match,  HandicapBetInfo, UserMoneylineBet, UserHandicapBet, UserTotalGoalsBet
)


# get the result of the match 
# return team winning the match (str) and handicap, and total goals 
def get_results(arg_match: Match, arg_bet_info): 
    # determine the appropriate score of the game based on the time type 
    if arg_bet_info.time_type == "full time": 
        target_score = arg_match.fulltime_score.split()
    elif arg_bet_info.time_type == "half time": 
        target_score = arg_match.halftime_score.split()
    else: 
        # if the time type is not either "full time" nor "half time", raise and error 
        raise ValueError("Time type is not found.")
    home_team_score, away_team_score = int(target_score[0]), int(target_score[-1])

    # if the arg_bet is the handicapbet, apply the handicap cover to the bet team 
    if isinstance(arg_bet_info, HandicapBetInfo):  
        home_team_score += arg_bet_info.handicap_cover
        if arg_bet_info.bet_team == arg_match.away_team: 
            away_team_score += arg_bet_info.handicap_cover 
    
    # determine the winning team based on the score 
    if home_team_score > away_team_score: 
        win_team = arg_match.home_team.name
    elif home_team_score < away_team_score: 
        win_team = arg_match.away_team.name 
    else: 
        win_team = "Draw"

    # score handicap and total goals of the game 
    total_goals = home_team_score + away_team_score
    return win_team, total_goals
    

# settle the list of moneyline bets 
def settle_moneyline_bet_list(moneyline_bet_list: QuerySet[UserMoneylineBet]) -> None: 
    updated_user_list = []
    for i, moneyline_bet in enumerate(moneyline_bet_list): 
        updated_user_list.append(moneyline_bet.user) # add the user this bet belongs to, to the list 
        bet_info = moneyline_bet.bet_info # the info of the this moneyline bet 
        bet_amount = moneyline_bet.bet_amount # the amount the user bet on this info

        # determine the winning team of the match 
        this_bet_match = bet_info.match
        win_team, _ = get_results(this_bet_match, bet_info)

        # compute the total payout to the user based on the result 
        # if the bet team is the win team, user wins 
        if win_team == bet_info.bet_team: 
            if bet_info.odd > 0: 
                total_payout = bet_amount + (bet_amount * bet_info.odd) / 100
                total_payout = round(total_payout, 2)
            else: 
                # the american odd will have to be less than 0, it can't be 0
                total_payout = bet_amount + (bet_amount * 100) / abs(bet_info.odd)
                total_payout = round(total_payout, 2)
        else: # otherwise, they lose and they get nothing back 
            total_payout = 0 
        # update the balance of the user 
        updated_user_list[i].balance += total_payout

    if len(updated_user_list) > 0: 
        num_updated_users = User.objects.bulk_update(updated_user_list, ["balance"])
        # notify the user that moneyline bets have been settled 
        print(num_updated_users + " moneyline bets settled!") 
    else: 
        print("No moneyline bets settled!")
    

# settle the list of handicap bets 
# TODO: Please account for handicap draw as well 
def settle_handicap_bet_list(handicap_bet_list: QuerySet[UserHandicapBet]) -> None: 
    updated_user_list = []
    for i, handicap_bet in handicap_bet_list: 
        updated_user_list.append(handicap_bet.user)
        bet_info = handicap_bet.bet_info
        bet_amount = handicap_bet.bet_amount

        # determine the winning team and the score handicap of the match 
        this_bet_match = bet_info.match
        win_team, _ = get_results(this_bet_match, bet_info)

        # determine whether the user wins the bet based on the result and handicap
        # compute the total payout to the user based on the result 
        if win_team == bet_info.bet_team: # if the bet team is the win team, user wins 
            if bet_info.odd > 0: 
                total_payout = bet_amount + (bet_amount * bet_info.odd) / 100
                total_payout = round(total_payout, 2)
            else: 
                # the american odd will have to be less than 0, it can't be 0
                total_payout = bet_amount + (bet_amount * 100) / abs(bet_info.odd)
                total_payout = round(total_payout, 2)
        else: # otherwise, they lose and they get nothing back 
            total_payout = 0 
        # update the user's balance 
        updated_user_list[i].balance += total_payout
    
    if len(updated_user_list) > 0: 
        num_updated_users = User.objects.bulk_update(updated_user_list, ["balance"])
        # notify the user that handicap bets have been settled 
        print(num_updated_users + " handicap bets settled!") 
    else: 
        print("No handicap bets settled!")


# settle the list of total goals bet 
def settle_total_goals_bet_list(total_goals_bet_list: QuerySet[UserTotalGoalsBet]) -> None: 
    updated_user_list = []
    for i, total_goals_bet in total_goals_bet_list: 
        updated_user_list.append(total_goals_bet.user)
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
            # the money will be returned to the user 
            total_payout = bet_amount 
        else: 
            if win_the_bet: 
                if bet_info.odd > 0: 
                    total_payout = bet_amount + (bet_amount * bet_info.odd) / 100
                    total_payout = round(total_payout, 2)
                else: 
                    # the american odd will have to be less than 0, it can't be 0
                    total_payout = bet_amount + (bet_amount * 100) / abs(bet_info.odd)
                    total_payout = round(total_payout, 2)
            else: 
                total_payout = 0
        # update the user's balance 
        updated_user_list[i].balance += total_payout
    
    if len(updated_user_list) > 0: 
        num_updated_users = User.objects.bulk_update(updated_user_list, ["balance"])
        # notify the user that total goals bets have been settled 
        print(num_updated_users + " total goals  bets settled!") 
    else: 
        print("No total goals bets settled!")
