from celery import shared_task, group
from .models import Match, MoneylineBetInfo, HandicapBetInfo, TotalGoalsBetInfo
from django.db import transaction
from .uploaders import upload_matches, upload_match_bets, update_match_scores, settle_bets
from datetime import date, timedelta
import time

LEAGUES = {"Champions League": 2, "Premiere League": 39, "La Liga": 140, "Bundesliga": 78}

@shared_task
def upload_league_matches_and_bets(league_name: str) -> None: 
    league_match_list = upload_matches(league_name, LEAGUES[league_name])
    upload_match_bets(league_match_list)
    

# NESTING THE FUNCTION WITHIN 1 TRANSACTION
# CALLED EVERY WEEK at 0 hours, to be run concurrently with 4 workers 
# retry 5 times in case of failure, each between 5 minutes 
@shared_task(bind=True, max_retries=5, default_retry_delay=5 * 60)
@transaction.atomic
def upload_matches_and_bets(self) -> None: 
    try: 
        start = time.time()
        leagues = group(upload_league_matches_and_bets.s(league) for league in list(LEAGUES.keys()))
        leagues.apply_async()
        end = time.time()
        print(f"Executed in {end - start} seconds")
    except Exception as exc: 
        raise self.retry(exc) # re-execute the task if something's wrong


@shared_task
def update_league_scores_and_settle(league_name) -> None: 
    updated_match_list = update_match_scores(league_name, LEAGUES[league_name])
    settle_bets(updated_match_list)
    print(f"{league_name}'s matches and bets settled successfully!")


# NESTING THE FUNCTION WITHIN 1 TRANSACTION
# CALLED EVERY HOUR AT 0 hours, to be run concurrently with 4 workers 
# retry 2 times in case of failure, each between 2 minutes 
@shared_task(bind=True, max_retries=2, default_retry_delay=2 * 60)
@transaction.atomic
def update_scores_and_settle(self) -> None: 
    try: 
        start = time.time()
        leagues = group(update_league_scores_and_settle.s(league, LEAGUES[league]) for league in list(LEAGUES.keys()))
        leagues.apply_async()
        end = time.time()
        print(f"Executed in {end - start} seconds")
    except Exception as exc: 
        raise self.retry(exc)


# CALLED EVERY DAY AT 0 hours
# delete the queryset of the bet infos and finished matches that have been their past days limit 
# retry 3 times in case of failure, each between 3 minutes 
@shared_task(bind=True, max_retries=3, default_retry_delay=3 * 60)
@transaction.atomic
def delete_past_betinfos_and_matches(self) -> None: 
    try:
        start = time.time()
        # bet info's past day limit is 14 days (2 weeks)
        info_filter_date = date.today() - timedelta(days=15)
        # delete the list of moneyline bet infos 
        past_moneyline_bet_info = MoneylineBetInfo.objects.filter(status="Settled", settled_date__lt=info_filter_date)
        if past_moneyline_bet_info.exists(): 
            past_moneyline_bet_info.delete()
            print("Past moneyline bets deleted successfully!")
        else: 
            print("No moneyline bets to delete")

        # delete the list of handicap bet infos 
        past_handicap_bet_info = HandicapBetInfo.objects.filter(status="Settled", settled_date__lt=info_filter_date)
        if past_handicap_bet_info.exists(): 
            past_handicap_bet_info.delete()
            print("Past handicap bets deleted successfully!")
        else: 
            print("No handicap bets to delete")

        # delete the list of total goals bet infos 
        past_totalgoals_bet_info = TotalGoalsBetInfo.objects.filter(status="Settled", settled_date__lt=info_filter_date)
        if past_totalgoals_bet_info.exists(): 
            past_totalgoals_bet_info.delete()
            print("Past total goals bets deleted successfully!")
        else: 
            print("No total goals bet to delete")

        # matches's past day limit is 1 month 
        match_filter_date = date.today() - timedelta(days=30)
        # delete the list of finished matches 
        past_finished_matches = Match.objects.filter(status="Finished", updated_date__lt=match_filter_date)
        if past_finished_matches.exists(): 
            past_finished_matches.delete() 
            print("Past matches deleted successfully!")
        else: 
            print("No matches to delete.")
        # time the task
        end = time.time()
        print(f"Executed in {end - start} seconds.")
    except Exception as exc: 
        self.retry(exc)