from celery import shared_task, group
from .models import Match
from django.db import transaction
from .uploaders import (
    upload_team_rankings, upload_matches, upload_match_bets, 
    update_match_scores, settle_bets, delete_empty_bet_infos
)
from datetime import date, timedelta

LEAGUES = {
    "Champions League": 2, 
    "Premiere League": 39, 
    "La Liga": 140, 
    "Bundesliga": 78,
    "Serie A": 135,
    "League 1": 61,
}

@transaction.atomic
def update_teams_rankings() -> None: 
    """CALLED EVERY 1 hour. Run by only 1 worker"""
    try: 
        upload_team_rankings()
    except Exception as exc: 
        raise exc # re-execute the task if something's wrong
    

@transaction.atomic
def upload_league_matches_and_bets(league_name: str) -> None: 
    """Retry 2 times in case of failure, each between 1 minute"""
    try: 
        league_matches = upload_matches(league_name, LEAGUES[league_name])
        upload_match_bets(league_matches)
    except Exception as exc: 
        raise exc


def upload_matches_and_bets() -> None: 
    """
    Nesting the function within the transaction.
    CALLED MONDAY at 0 hours
    """
    for league in list(LEAGUES.keys()):
        upload_league_matches_and_bets(league)


@transaction.atomic
def upload_new_bets() -> None:
    try: 
        upload_match_bets(Match.objects.filter(status="Not Finished"))
    except Exception as exc:
        raise exc


@transaction.atomic
def update_league_scores_and_settle(league_name) -> None:
    """ Retry 2 times in case of failure, each between 1 minute """
    try: 
        updated_match_list = update_match_scores(league_name, LEAGUES[league_name])
        delete_empty_bet_infos(updated_match_list)
        settle_bets(updated_match_list)
        print(f"{league_name}'s matches and bets settled successfully!")
    except Exception as exc: 
        raise exc


def update_scores_and_settle() -> None: 
    """
    CALLED EVERY HOUR AT 0 hours, to be run concurrently with 4 workers.
    Retry 2 times in case of failure, each between 2 minutes 
    """
    for league in list(LEAGUES.keys()):
        update_league_scores_and_settle(league)


@transaction.atomic
def delete_past_betinfos_and_matches(self) -> None: 
    """
    CALLED EVERY DAY AT 0 hours
    Delete the queryset of the bet infos and finished matches that have been their past 
    days limit.
    retry 2 times in case of failure, each between 1 minute 
    """

    try:
        # bet info's past day limit is 14 days or 2 weeks 
        filter_date = date.today() - timedelta(days=14)
        # delete the list of finished matches 
        Match.objects.filter(
            status="Finished", 
            updated_date__lt=filter_date
        ).delete()
        print("Past matches and associated bet infos deleted successfully!")
    except Exception as exc: 
        self.retry(exc=exc)

if __name__ == "__main__": None