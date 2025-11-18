from django.test import TestCase
from unittest.mock import patch
from django.db.models import Model
from soccerapp.tests.factories import *
from soccerapp.models import *
from soccerapp.uploaders import upload_match_bets, delete_empty_bet_infos, settle_bets
from datetime import date

class BetUploaderTests(TestCase):

    @patch("soccerapp.uploaders.bet_uploader.get_bets")
    def test_upload_bets_to_db(self, mock_get_bets) -> None:
        """
        Test ```upload_match_bets(matches: list[Match]), whether it: 
        - Uploads the list of bets of 3 types for each of 2 matches
        - Don't upload the one that already exists in DB
        """
        def fake_get_bets(bet_type, match_id, home_team, away_team): 
            """Side effect function to get the list of bets depending on the type"""
            type_to_bet_dict = {
                "moneyline": [{
                    "period": "Full-time", "bet_object": "Goals", "bet_team": "A", "odd": 180
                },
                {
                    "period": "Full-time", "bet_object": "Goals", "bet_team": "B", "odd": 300
                }],
                "handicap": [{
                    "period": "Full-time", "bet_object": "Goals", "bet_team": "A", "odd": 180, "cover": -2
                }],
                "total_objects": [{
                    "period": "Full-time", "bet_object": "Goals", "under_or_over": "Under", "num_objects": 3, "odd": -150
                }]
            }
            return type_to_bet_dict[bet_type]
        
        # Mock the function and the instances
        mock_get_bets.side_effect = fake_get_bets
        match = MatchFactory(
            home_team=TeamFactory(name="A"), away_team=TeamFactory(name="B")
        )
        
        # Dictionary mapping the type of bet info to number info it should have
        class_to_count: dict[type[Model], int] = {
            MoneylineBetInfo: 2, 
            HandicapBetInfo: 1, 
            TotalObjectsBetInfo: 1
        }
        # Unit should upload the correct number of bet info
        upload_match_bets([match])
        for info_class, num_infos in class_to_count.items():
            self.assertEqual(info_class.objects.count(), num_infos)

        # Unit should not upload any new bet info because they are already in the DB
        upload_match_bets([match])
        for info_class, num_infos in class_to_count.items():
            self.assertEqual(info_class.objects.count(), num_infos)

    
    def test_delete_empty_bet_infos(self):
        """Test ```delete_empty_bet_infos(matches: QuerySet[Match])"""
        # Mock all of the necessary instances
        user = UserFactory()
        match = MatchFactory(
            home_team=TeamFactory(name="A"), away_team=TeamFactory(name="B")
        )
        
        # Create the list of bet infos
        teams = ["A", "B", "B", "A", "Draw", "B"]
        # Indices of info in teams selected to have user bet (1st, 2nd, 5th)
        selected = [0, 1, 4]

        created_infos = []
        for team in teams:
            created_infos.append(MoneylineBetInfoFactory(
                match=match, bet_team=team
            ))
        self.assertEqual(MoneylineBetInfo.objects.count(), 6)

        # Create a user bet of selected info
        for i in selected:
            _ = UserMoneylineBetFactory(
                user=user, bet_info=created_infos[i]
            )

        delete_empty_bet_infos(Match.objects.filter(id=match.id))
         
        # Unit should remove the 3rd, 4th, & 6th info
        self.assertEqual(MoneylineBetInfo.objects.count(), 3)
        
        # The remaining info should be equal to selected infos
        for info, i in zip(MoneylineBetInfo.objects.all(), selected):
            self.assertEqual(info.bet_team, teams[i])


    @patch("soccerapp.uploaders.bet_uploader.settle_bet_list")
    def test_settle_bets(self, mock_settle_bet_list):
        """Test ```settle_bets(matches: Queryset[Match])```"""

        def fake_settle_bet_list(bet_type, bet_list):
            # We assume that there is only one user in the app,
            # The complex logic within this unit would be tested separately
            return len(bet_list), 1
        mock_settle_bet_list.side_effect = fake_settle_bet_list
        
        # Create a user and a finished match
        user = UserFactory()
        match = MatchFactory(
            home_team=TeamFactory(name="A"), away_team=TeamFactory(name="B"),
            status="Finished"
        )
        
        # Create a list of bet info and their corresponding user bet (not really needed)
        for _ in range(5):
            created_info = MoneylineBetInfoFactory(match=match)
            _ = UserMoneylineBetFactory(user=user, bet_info=created_info)

        settle_bets(Match.objects.filter(id=match.id))

        # The unit should update all the bet info to be settled with recorded time
        for info in MoneylineBetInfo.objects.filter(match=match):
            self.assertEqual(info.status, "Settled")
            self.assertEqual(info.settled_at, date.today())

        