from django.db import transaction
from django.db.models import QuerySet
from .models import (
    User, Match,
    MoneylineBetInfo, HandicapBetInfo, TotalObjectsBetInfo, 
    UserMoneylineBet, UserHandicapBet, UserTotalObjectsBet
) 
from .uploaders import ( 
    generic_update_match_scores, settle_bets, get_date_str
)
from datetime import date
import time 


"""
    function to generate the testing bets to the user to test settle functions
    used for testing the speed and accuracy, so run manually 
"""
@transaction.atomic
def test_upload_user_bets(matches: QuerySet[Match]): 
    users = [user for user in User.objects.all()[:5]]

    moneyline_info_list = MoneylineBetInfo.objects.filter(match__in=matches)
    moneyline_bet_list, ix = [], 0
    for bet_info in moneyline_info_list: 
        moneyline_bet_list.append(UserMoneylineBet(
            user=users[ix], bet_info=bet_info, created_date=date.today(), bet_amount=(100 if bet_info.odd > 0 else abs(bet_info.odd)),
        ))
        ix = (ix + 1) % len(users)
    UserMoneylineBet.objects.bulk_create(moneyline_bet_list)
    print("Moneyline bet created successfully")

    handicap_info_list = HandicapBetInfo.objects.filter(match__in=matches)
    handicap_bet_list, ix = [], 0
    for bet_info in handicap_info_list: 
        handicap_bet_list.append(UserHandicapBet(
            user=users[ix], bet_info=bet_info, created_date=date.today(), bet_amount=(100 if bet_info.odd > 0 else abs(bet_info.odd)), 
        ))
        ix = (ix + 1) % len(users)
    UserHandicapBet.objects.bulk_create(handicap_bet_list)
    print("Handicap bet created successfully")

    total_info_list = TotalObjectsBetInfo.objects.filter(match__in=matches)
    total_bet_list, ix = [], 0
    for bet_info in total_info_list: 
        total_bet_list.append(UserTotalObjectsBet(
            user=users[ix], bet_info=bet_info, created_date=date.today(), bet_amount=(100 if bet_info.odd > 0 else abs(bet_info.odd)), 
        ))
        ix = (ix + 1) % len(users)
    UserTotalObjectsBet.objects.bulk_create(total_bet_list)
    print("Total goals bet created successfully")


"""
function to update the scores of the matches in params, and settle the bets 
"""
@transaction.atomic
def test_settle_user_bets(matches: QuerySet[Match]): 
    start = time.time() # time the function to test the speed 
    date_str_list = [get_date_str(match.date) for match in matches]

    leagues = {"Champions League": 2, "Premiere League": 39, "La Liga": 140, "Bundesliga": 78}
    for date_str in date_str_list: 
        for name in leagues: 
            updated_matches = generic_update_match_scores(name, leagues[name], date_str)
            settle_bets(updated_matches)
    end = time.time() # time the function 
    print(f"Executed in {end - start} seconds.")


def test_upload(): 
    matches = Match.objects.filter(league="Champions League")[:3] # get the first ucl matches
    test_upload_user_bets(matches)
    return matches 


def test_settle(matches): 
    test_settle_user_bets(matches)
