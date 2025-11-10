"""
LOGIC TO SETTLE THE BETS
"""

from .models import (
    User, TotalObjectsBetInfo, HandicapBetInfo, UserMoneylineBet, UserHandicapBet, UserTotalObjectsBet
)
from decimal import Decimal
from typing import Tuple
from collections import defaultdict


def get_results(bet_info, handicap_cover=None) -> tuple:
    """ 
    Get the result of the bet info from its match. 
    Return team winning the match and total bet objects 
    """

    if bet_info.bet_object == "Goals": 
        if bet_info.time_type == "Full-time": 
            result = bet_info.match.fulltime_score.split("-")
        elif bet_info.time_type == "Half-time": 
            result = bet_info.match.halftime_score.split("-")
    else: 
        if bet_info.bet_object == "Corners": 
            result = bet_info.match.corners.split("-")
        elif bet_info.bet_object == "Cards": 
            result = bet_info.match.cards.split("-")
        
    # Total number of objects
    home_result, away_result = int(result[0]), int(result[-1])
    total_objects = home_result + away_result

    # If there is a handicap cover, apply the handicap cover to the bet team 
    if handicap_cover is not None:  
        if bet_info.bet_team == bet_info.match.home_team: 
            home_result += handicap_cover
        elif bet_info.bet_team == bet_info.match.away_team: 
            away_result += handicap_cover 
     
    # Determine the winner based on the score, default when both teams draw
    if home_result > away_result: 
        win_team = bet_info.match.home_team
    elif home_result < away_result: 
        win_team = bet_info.match.away_team
    else: 
        win_team = "Draw" 

    # Outcome (including the handicap cover) and total objects
    return win_team, total_objects


def compute_payout(odd, bet_amount): 
    """ 
    Compute the payout of the bet based on the odd of the bet and the bet amount
    """
    if odd > 0: 
        total_payout = round(bet_amount + (bet_amount * odd) / 100, 2)
    else: 
        # The american odd must be less than 0
        total_payout = round(bet_amount + (bet_amount * 100) / abs(odd), 2)
    return total_payout


def get_winner_payout(bet_info, bet_amount, handicap_cover=None): 
    """ Determine final payout of the moneyline or handicap bet """

    if handicap_cover is not None:
        # For Asian handicap, recursively settle 2 bets corresponding to this Asian bet
        # Return the sum of payout
        decimal = abs(float(handicap_cover - int(handicap_cover))) 
        if decimal == 0.25 or decimal == 0.75: 
            payout1 = get_winner_payout(bet_info, bet_amount / 2, handicap_cover - Decimal(0.25))
            payout2 = get_winner_payout(bet_info, bet_amount / 2, handicap_cover + Decimal(0.25))
            # Total payout is the sum of 2 payouts 
            return payout1 + payout2 
    
    # If it's not Asian handicap, compute the payout as usual 
    try:
        win_team, _ = get_results(bet_info, handicap_cover)
    except ValueError: 
        # Value error indicates that results not available, 
        # there's nothing to settle and we will refund the money back to the user
        total_payout = bet_amount
    else: 
        if win_team == "Draw": 
            # If the 2 teams of the game draw (considering the handicap cover), 
            # Refund the bet
            total_payout = bet_amount 
        elif win_team == bet_info.bet_team: 
            total_payout = compute_payout(bet_info.odd, bet_amount)
        else: 
            # When the win team doesn't match bet team, user loses and get nothing back
            total_payout = Decimal(0.0)

    return total_payout


def get_total_objects_payout(bet_info: TotalObjectsBetInfo, bet_amount, target_num_objs): 
    """ Determine the final payout of the total objects bet """

    num_decimal = abs(float(target_num_objs - int(target_num_objs)))
    if num_decimal == 0.25 or num_decimal == 0.75: 
        # If it's Asian total objects bet, 
        # then recursively settle 2 European bets, return the sum of payout
        payout1 = get_total_objects_payout(
            bet_info, bet_amount / 2, target_num_objs - Decimal(0.25)
        )
        payout2 = get_total_objects_payout(
            bet_info, bet_amount / 2, target_num_objs + Decimal(0.25)
        )
        return payout1 + payout2

    # Determine the total objects of the match as usual   
    try: 
        _, total_bet_objs = get_results(bet_info)
    except ValueError: 
        total_payout = bet_amount
    else: 
        # Determine if the user win the bet based on the number of goals 
        win_the_bet = None 

        # if the number of goals equals target, win_the_bet is still None 
        if total_bet_objs < target_num_objs: 
            win_the_bet = True if bet_info.under_or_over == "Under" else False 
        elif total_bet_objs > target_num_objs: 
            win_the_bet = True if bet_info.under_or_over == "Over" else False 
            
        if win_the_bet is None: 
            # If total objects is equal to target number of objects, 
            # the money will be refunded to the user 
            total_payout = bet_amount 
        else: 
            if win_the_bet: 
                total_payout = compute_payout(bet_info.odd, bet_amount)
            else: 
                total_payout = Decimal(0.0) # the user loses the bet 
    return total_payout


def settle_bet_list(bet_type: str, bet_list) -> Tuple[int, int]: 
    """ The main function: settle the queryset of bets of any type """
    
    bet_list = bet_list.select_related("user", "bet_info", "bet_info__match")
    updated_bet_list = []
    updated_user_dict = defaultdict(Decimal)

    for i, bet in enumerate(bet_list.iterator()):  
        updated_bet_list.append(bet) # Add the bet to the list of updated bets 

        bet_info = bet.bet_info # bet info of the bet
        bet_amount = bet.bet_amount # The amount the user bets on this bet

        if bet_type == "total_objects": 
            total_payout = get_total_objects_payout(bet_info, bet_amount, bet_info.target_num_objects)
        else: 
            if isinstance(bet_info, HandicapBetInfo): 
                handicap_cover = bet_info.handicap_cover
            else:
                handicap_cover = None

            total_payout = get_winner_payout(bet_info, bet_amount, handicap_cover)
    
        # Update the payout of the bets and balance of the user 
        updated_bet_list[i].payout = total_payout
        updated_user_dict[bet.user.id] += total_payout

    updated_user_list = User.objects.filter(id__in=list(updated_user_dict.keys()))
    for user in updated_user_list: 
        user.balance += updated_user_dict[user.id]

    # Update the payout of the list of bets
    if bet_type == "moneyline": 
        num_updated_bets = UserMoneylineBet.objects.bulk_update(
            updated_bet_list, 
            ["payout"], 
            batch_size=250
        )
    elif bet_type == "handicap": 
        num_updated_bets = UserHandicapBet.objects.bulk_update(
            updated_bet_list, 
            ["payout"], 
            batch_size=250
        )
    elif bet_type == "total_objects": 
        num_updated_bets = UserTotalObjectsBet.objects.bulk_update(
            updated_bet_list, 
            ["payout"], 
            batch_size=250
        )
    else: 
        raise ValueError("The bet type is invalid.")
    
    # Update the balance of the list of users
    num_update_users = User.objects.bulk_update(updated_user_list, ["balance"], batch_size=250) 
    return num_updated_bets, num_update_users
