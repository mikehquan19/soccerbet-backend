from django.db.models import QuerySet, Count
from soccerapp.uploaders.api import get_bets
from soccerapp.settle import settle_bet_list
from soccerapp.models import (
    Match,
    MoneylineBetInfo, HandicapBetInfo, TotalObjectsBetInfo, 
    UserMoneylineBet, UserHandicapBet, UserTotalObjectsBet
) 
from datetime import date
from typing import Type
from django.db.models import Model

TYPE_TO_INFO_CLASS: dict[str, Type[Model]] = {
    "moneyline": MoneylineBetInfo,
    "handicap": HandicapBetInfo, 
    "total_objects": TotalObjectsBetInfo
}

def upload_match_bets(matches: list[Match]) -> None: 
    """Upload the bets that don't exist for the list of matches"""
    
    def generic_upload_bets(bet_type: str, match: Match):
        """Save the bets of specified types to database"""
        bet_info_data = get_bets(
            bet_type, match.match_id, match.home_team.name, match.away_team.name
        )
        # The combination of fields that can uniquely identify a bet
        type_to_compound: dict[str, list[str]] = {
            "moneyline": ["bet_team"],
            "handicap": ["bet_team", "cover"],
            "total_objects": ["under_or_over", "num_objects"],
        }
        compound_fields = ["period", "bet_object", "odd"] + type_to_compound[bet_type]
        info_class = TYPE_TO_INFO_CLASS[bet_type]

        # The idea is that we place all bet info of the match in a set, 
        # then check if the info from API matches existing info.
        existing_info = set(
            tuple(getattr(bet_info, field) for field in compound_fields)
            for bet_info in info_class.objects.filter(match=match)
        )
        info_list = []
        for item in bet_info_data:
            keys = tuple(item[field] for field in compound_fields)
            if keys not in existing_info:
                info_list.append(info_class(match=match, **item))

        created_list = info_class.objects.bulk_create(info_list)
        print(f"{len(created_list)} {bet_type} of {match} uploaded!") 

    # matches is the list, instead of the queryset, so convert them.
    # Eager fetch to avoid N+1 query problem.
    queryset = Match.objects.filter(
        id__in=[match.id for match in matches]).select_related("home_team", "away_team")
    for match in queryset:
        for bet_type in ["moneyline", "handicap", "total_objects"]:
            generic_upload_bets(bet_type, match)


def delete_empty_bet_infos(matches: QuerySet[Match]) -> None: 
    """ 
    Delete the bet infos from the queryset of matches without user bets 
    """
    type_to_class: dict[str, Type[Model]] = {
        "moneyline": MoneylineBetInfo,
        "handicap": HandicapBetInfo, 
        "totalobjects": TotalObjectsBetInfo
    }
    for match in matches: 
        for bet_type, info_class in type_to_class.items():
            info_class.objects.annotate(bet_count=Count(f"user{bet_type}bet")).filter(
                match=match, bet_count=0
            ).delete()
        print(f"Empty bet infos of match {match} deleted!")


def settle_bets(matches: QuerySet[Match]) -> None: 
    """Settle the bets of the matches, and update the bet infos"""

    def generic_settle_bets(bet_type: str, match: Match):
        """Settle all bets of given bet type of the match"""
        type_to_bet_class: dict[str, Type[Model]] = {
            "moneyline": UserMoneylineBet,
            "handicap": UserHandicapBet, 
            "total_objects": UserTotalObjectsBet,
        }
        bet_class, info_class = type_to_bet_class[bet_type], TYPE_TO_INFO_CLASS[bet_type]

        bet_list = bet_class.objects.filter(bet_info__match=match)
        num_bets, num_users = settle_bet_list(bet_type, bet_list)

        # Update the status and settled date of list of bet info
        info_class.objects.filter(match=match).update(
            status="Settled",
            settled_date=date.today()
        )
        print(f"{num_bets} {bet_type} bets from {num_users} of {match} settled!")

    for match in matches: 
        for bet_type in ["moneyline", "handicap", "total_objects"]:
            generic_settle_bets(bet_type, match)

if __name__ == "__main__": None