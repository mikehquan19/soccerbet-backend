from celery import shared_task, group
from .models import Match
from django.db import transaction
from .uploaders import upload_team_rankings, upload_matches, upload_match_bets, update_match_scores, settle_bets, delete_empty_bet_infos
from datetime import date, timedelta
import time

LEAGUES = {"Champions League": 2, "Premiere League": 39, "La Liga": 140, "Bundesliga": 78}


# CALLED EVERY 12 hours, run by only 1 worker 
@shared_task(bind=True, max_retries=3, default_retry_delay=3 * 60)
@transaction.atomic
def update_teams_rankings(self) -> None: 
    try: 
        upload_team_rankings()
    except Exception as exc: 
        raise self.retry(exc=exc)


# retry 5 times in case of failure, each between 5 minutes 
@shared_task(bind=True, max_retries=5, default_retry_delay=5 * 60)
@transaction.atomic
def upload_league_matches_and_bets(self, league_name: str) -> None: 
    try: 
        league_match_list = upload_matches(league_name, LEAGUES[league_name])
        upload_match_bets(league_match_list)
    except Exception as exc: 
        raise self.retry(exc=exc) # re-execute the task if something's wrong
    

# NESTING THE FUNCTION WITHIN 1 TRANSACTION
# CALLED MONDAY AND FRIDAY at 0 hours, to be run concurrently with 4 workers 
@shared_task
def upload_matches_and_bets() -> None: 
        leagues = group(upload_league_matches_and_bets.s(league) for league in list(LEAGUES.keys()))
        leagues.apply_async()


# retry 2 times in case of failure, each between 2 minutes 
@shared_task(bind=True, max_retries=2, default_retry_delay=2 * 60)
@transaction.atomic
def update_league_scores_and_settle(self, league_name) -> None: 
    try: 
        updated_match_list = update_match_scores(league_name, LEAGUES[league_name])
        delete_empty_bet_infos(updated_match_list)
        settle_bets(updated_match_list)
        print(f"{league_name}'s matches and bets settled successfully!")
    except Exception as exc: 
        raise self.retry(exc=exc)


# CALLED EVERY HOUR AT 0 hours, to be run concurrently with 4 workers 
# retry 2 times in case of failure, each between 2 minutes 
@shared_task
def update_scores_and_settle() -> None: 
    leagues = group(update_league_scores_and_settle.s(league) for league in list(LEAGUES.keys()))
    leagues.apply_async()


# CALLED EVERY DAY AT 0 hours
# delete the queryset of the bet infos and finished matches that have been their past days limit 
# retry 3 times in case of failure, each between 3 minutes 
@shared_task(bind=True, max_retries=3, default_retry_delay=3 * 60)
@transaction.atomic
def delete_past_betinfos_and_matches(self) -> None: 
    try:
        start = time.time()
        # bet info's past day limit is 7 days (1 week)
        filter_date = date.today() - timedelta(days=7)
        # delete the list of finished matches 
        Match.objects.filter(status="Finished", updated_date__lt=filter_date).delete()
        print("Past matches and associated bet_infos deleted successfully!")
        # time the task
        end = time.time()
        print(f"Executed in {end - start} seconds.")
    except Exception as exc: 
        self.retry(exc=exc)