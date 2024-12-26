from django.test import TestCase
from soccerapp.models import User, Match, UserTotalGoalsBet, UserMoneylineBet, UserHandicapBet
from soccerapp.settle import settle_handicap_bet_list, settle_moneyline_bet_list, settle_total_goals_bet_list
from soccerapp.test_data import *

# TODO: TEST THE SETTLED FUNCTIONS 
# the test data

# test settle/settle_moneyline_bet_list
class TestSettleMoneylineBetList(TestCase): 
    def setUp(self): 
        # create the user, the match, bet_info
        user1 = User.objects.create(**user_data1)
        user2 = User.objects.create(**user_data2)
        # test_match = Match.objects.create(**test_match_data)


# test settle/settle_handicap_bet_list
class TestSettleHandicapBetList(TestCase): 
    def setUp(self): 
        return UserHandicapBet.objects.none()


# test settle/settle_total_goals_bets_list 
class TestSettleTotalGoalsBetList(TestCase): 
    def setUp(self): 
        return UserTotalGoalsBet.objects.none()


