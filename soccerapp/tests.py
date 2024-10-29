from django.test import TestCase
from soccerapp.models import User, Match, UserTotalGoalsBet, UserMoneylineBet, UserHandicapBet
from soccerapp.settle import settle_handicap_bet_list, settle_moneyline_bet_list, settle_total_goals_bet_list

# TODO: TEST THE SETTLED FUNCTIONS 
# the user test data 
test_user_data = {
    "first_name": "test", 
    "last_name": "user", 
    "email": "test.user@gmail.com", 
    "username": "test_username", 
    "password": "test_password", 
    "balance": "1000",
}

test_match_data = {

}

# test settle/settle_moneyline_bet_list
class TestSettleMoneylineBetList(TestCase): 
    def setUp(self): 
        # create the user, the match, bet_info
        test_user = User.objects.create(**test_user_data)
        test_match = Match.objects.create(**test_match_data)


# test settle/settle_handicap_bet_list
class TestSettleHandicapBetList(TestCase): 
    def setUp(self): 
        return UserHandicapBet.objects.none()


# test settle/settle_total_goals_bets_list 
class TestSettleTotalGoalsBetList(TestCase): 
    def setUp(self): 
        return UserTotalGoalsBet.objects.none()


