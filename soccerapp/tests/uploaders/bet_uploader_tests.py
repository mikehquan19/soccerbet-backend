from django.test import TestCase
from unittest.mock import patch
from typing import Type
from django.db.models import Model

from soccerapp.models import (
    Team, Match, 
    MoneylineBetInfo, HandicapBetInfo, TotalObjectsBetInfo
)
from soccerapp.uploaders import get_bets
from soccerapp.uploaders import upload_match_bets

class UploadMatchBetsTests(TestCase):
    """
    This will test ```upload_match_bets(matches: list[Match]), whether it: 
    - Uploads the list of bets of 3 types for each of 2 matches
    - Don't upload the one that already exists in DB
    """

    @patch("soccerapp.uploaders.bet_uploader.get_bets")
    def test_upload_bets_to_db(self, mock_get_bets):
        """Test if the ```upload_match_bets``` uploads the list of bets successfully"""
        # Side effect function to get the list of bets depending on the type
        def fake_get_bets(bet_type, match_id, home_team, away_team): 
            type_to_bet_dict = {
                "moneyline": [{
                    "period": "Full-time", 
                    "bet_object": "Goals", 
                    "bet_team": "A", 
                    "odd": 180
                },
                {
                    "period": "Full-time", 
                    "bet_object": "Goals", 
                    "bet_team": "B", 
                    "odd": 300
                }],
                "handicap": [{
                    "period": "Full-time", 
                    "bet_object": "Goals", 
                    "bet_team": "A", 
                    "odd": 180, 
                    "cover": -2
                }],
                "total_objects": [{
                    "period": "Full-time", 
                    "bet_object": "Goals", 
                    "under_or_over": "Under", 
                    "num_objects": 3, "odd": -150
                }]
            }
            return type_to_bet_dict[bet_type]
        mock_get_bets.side_effect = fake_get_bets

        # Fake teams and matches for testing
        A = Team.objects.create(
            league="Premiere League", name="A", home_stadium="", description="")
        B = Team.objects.create(
            league="Champions League", name="B", home_stadium="", description="")
        match = Match.objects.create(
            league="Champions League", match_id="10000", home_team=A, away_team=B)
        
        # Mapping showing expected results
        class_to_count: dict[type[Model], int] = {
            MoneylineBetInfo: 2, HandicapBetInfo: 1, TotalObjectsBetInfo: 1
        }

        # The function should upload the correct number of bet info
        upload_match_bets([match])
        for info_class, count in class_to_count.items():
            self.assertEqual(info_class.objects.count(), count)

        # The function should not upload any new bet infos because
        # they are already in the DB
        upload_match_bets([match])
        for info_class, count in class_to_count.items():
            self.assertEqual(info_class.objects.count(), count)

