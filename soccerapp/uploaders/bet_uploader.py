from django.db.models import QuerySet, Count
from soccerapp.uploaders.api import get_bets
from soccerapp.settle import settle_bet_list
from soccerapp.models import (
    Match,
    MoneylineBetInfo, HandicapBetInfo, TotalObjectsBetInfo, 
    UserMoneylineBet, UserHandicapBet, UserTotalObjectsBet
) 
from datetime import date


def upload_match_bets(matches: list[Match]) -> None: 
    """Upload the bets that don't exist for the list of matches"""

    def generic_upload_bets(bet_type: str, match: Match):
        """Save the bets of specified types to database"""
        
        bet_info_data = get_bets(
            bet_type, match.match_id, match.home_team.name, match.away_team.name
        )
        if bet_type == "moneyline": 
            compound_fields = ["period", "bet_object", "bet_team", "odd"]
            info_class = MoneylineBetInfo
        elif bet_type == "handicap":
            compound_fields = ["period", "bet_object", "bet_team", "odd", "cover"]
            info_class = HandicapBetInfo
        else:
            compound_fields = ["period", "bet_object", "under_or_over", "num_objects", "odd"]
            info_class = TotalObjectsBetInfo

        # The idea is that we place all bet info of the match in a set, 
        # then checking if the info from API matches existing bets.
        existing_info = set(
            tuple(getattr(bet_info, field) for field in compound_fields)
            for bet_info in info_class.objects.filter(match=match)
        )
        info_list = []
        for item in bet_info_data:
            keys = tuple(item[field] for field in compound_fields)
            if keys not in existing_info:
                info_list.append(info_class(match=match, **item))

        created = info_class.objects.bulk_create(info_list)
        print(f"{len(created)} {bet_type} of {match} uploaded!") 

    # matches is the list of Matches, instead of the queryset,
    # so convert them.
    queryset = Match.objects.filter(id__in=[m.id for m in matches]).select_related(
        "home_team", "away_team")
    for match in queryset:
        for bet_type in ["moneyline", "handicap", "total_objects"]:
            generic_upload_bets(bet_type, match)


def delete_empty_bet_infos(matches: QuerySet[Match]) -> None: 
    """ 
    Delete the bet infos from the queryset of matches that are without user bets 
    """
    for match in matches: 
        # Filter the queryset of bet info that has 0 corresponding user bets 
        MoneylineBetInfo.objects.annotate(bet_count=Count('usermoneylinebet')).filter(
            match=match, bet_count=0
        ).delete()

        HandicapBetInfo.objects.annotate(bet_count=Count('userhandicapbet')).filter(
            match=match, bet_count=0
        ).delete()

        TotalObjectsBetInfo.objects.annotate(bet_count=Count('usertotalobjectsbet')).filter(
            match=match, bet_count=0
        ).delete()
        print(f"Empty bet infos of match {match} deleted!")


def settle_bets(matches: QuerySet[Match]) -> None: 
    """Settle the bets of the matches, and update the bet infos"""

    def generic_settle_bets(bet_type: str, match: Match) -> None:
        """Settle all bets of given bet type of the match"""
        if bet_type == "moneyline":
            bet_class, info_class = UserMoneylineBet, MoneylineBetInfo
        elif bet_type == "handicap":
            bet_class, info_class = UserHandicapBet, HandicapBetInfo
        else:
            bet_class, info_class = UserTotalObjectsBet, TotalObjectsBetInfo
        
        bet_list = bet_class.objects.filter(bet_info__match=match)
        num_bets, num_users = settle_bet_list(bet_type, bet_list)

        # Update the status and settled date of list of bet info
        info_class.objects.filter(match=match).update(
            status="Settled",
            settled_date=date.today()
        )
        print(f"{num_bets} {bet_type} bets of {match} settled from {num_users}!")

    for match in matches: 
        for bet_type in ["moneyline", "handicap", "total_objects"]:
            generic_settle_bets(bet_type, match)

if __name__ == "__main__": 
    None