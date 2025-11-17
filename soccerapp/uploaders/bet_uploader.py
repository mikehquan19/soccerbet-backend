from django.db.models import QuerySet, Count
from soccerapp.uploaders.api import get_winner_bets, get_total_bets
from soccerapp.settle import settle_bet_list
from soccerapp.models import (
    Match,
    MoneylineBetInfo, HandicapBetInfo, TotalObjectsBetInfo, 
    UserMoneylineBet, UserHandicapBet, UserTotalObjectsBet
) 
from datetime import date


def upload_match_bets(matches: QuerySet[Match]) -> None: 
    """Upload the bets that don't exist for each match in the list"""
    
    def generic_upload_bets(bet_type: str, match: Match):
        if bet_type == "moneyline": 
            info_data = get_winner_bets(
                "moneyline", match.match_id, match.home_team.name, match.away_team.name
            )
            fields = ["period", "bet_object", "bet_team", "odd"]
            info_class = MoneylineBetInfo
        elif bet_type == "handicap":
            info_data = get_winner_bets(
                "handicap", match.match_id, match.home_team.name, match.away_team.name
            )
            fields = ["period", "bet_object", "bet_team", "odd", "cover"]
            info_class = HandicapBetInfo
        else: 
            info_data = get_total_bets(
                match.match_id, match.home_team.name, match.away_team.name
            )
            fields = ["period", "bet_object", "under_or_over", "num_objects", "odd"]
            info_class = MoneylineBetInfo

        existing_info = set(
            tuple(bet_info.getattr(field) for field in fields)
            for bet_info in info_class.objects.filter(match=match)
        )
        info_list = [
            info_class(match=match, **item_data)
            for item_data in info_data
            if tuple(item_data[field] for field in fields) not in existing_info
        ]
        created = info_class.objects.bulk_create(info_list)
        print(f"{len(created)} {bet_type} of {match} uploaded successfully!") 

    for match in matches:
        for bet_type in ["moneyline", "handicap", "total_objects"]:
            # Save the bets of specified types to database
            generic_upload_bets(bet_type, match)


def delete_empty_bet_infos(matches: QuerySet[Match]) -> None: 
    """ 
    Delete the bet infos from the given queryset of matches that are without user bets 
    """
    for match in matches: 
        # filter the queryset of bet info that has 0 corresponding user bets 
        MoneylineBetInfo.objects.annotate(
            bet_count=Count('usermoneylinebet')
        ).filter(
            match=match, bet_count=0
        ).delete()

        HandicapBetInfo.objects.annotate(
            bet_count=Count('userhandicapbet')
        ).filter(
            match=match, bet_count=0
        ).delete()

        TotalObjectsBetInfo.objects.annotate(
            bet_count=Count('usertotalobjectsbet')
        ).filter(
            match=match, bet_count=0
        ).delete()

        print(f"Empty bet infos of match {match} deleted successfully!")


def settle_bets(matches: QuerySet[Match]) -> None: 
    """
    Settle the bets that are associated with the matches, and update the bet infos 
    """

    for match in matches: 
        # Settle all the moneyline bets of the match 
        moneyline_bet_list = UserMoneylineBet.objects.filter(bet_info__match=match)
        total, _ = settle_bet_list("moneyline", moneyline_bet_list)

        # Update the status and settled date of list of bet info
        MoneylineBetInfo.objects.filter(match=match).update(
            status="Settled", 
            settled_date=date.today()
        )
        print(f"{total} moneyline bets of match {match} settled!")

        # Settle all the handicap bets of the match 
        handicap_bet_list = UserHandicapBet.objects.filter(bet_info__match=match)
        total, _ = settle_bet_list("handicap", handicap_bet_list)

        # Update the status and settled date
        HandicapBetInfo.objects.filter(match=match).update(
            status="Settled", 
            settled_date=date.today()
        )
        print(f"{total} handicap bets of match {match} settled!")

        # Settle all the total goals bets of the match 
        total_goals_bet_list = UserTotalObjectsBet.objects.filter(bet_info__match=match)
        total, _ = settle_bet_list("total_objects", total_goals_bet_list)

        # Update the status and settled date 
        TotalObjectsBetInfo.objects.filter(match=match).update(
            status="Settled", 
            settled_date=date.today()
        )
        print(f"{total} total objects bets of match {match} settled!")

if __name__ == "__main__": None