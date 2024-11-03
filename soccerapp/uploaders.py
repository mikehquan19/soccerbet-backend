from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from .api import (
    get_not_started_matches, get_moneyline_bets, 
    get_total_goals_bets, get_match_score, get_teams,
)
from .settle import settle_moneyline_bet_list, settle_handicap_bet_list, settle_total_goals_bet_list
from .models import (
    Match, Team, MoneylineBetInfo, HandicapBetInfo, 
    TotalGoalsBetInfo, UserMoneylineBet, UserHandicapBet, UserTotalGoalsBet
) 
from datetime import date, timedelta
import traceback


# function to upload data about the teams (for the comment and section part of the website)
# CALLED EVERY YEAR 
@transaction.atomic
def upload_teams() -> None: 
    leagues = {"Premiere League": 39, "La Liga": 140, "Bundesliga": 78}
    try: 
        for league_name in list(leagues.keys()): 
            api_teams_data = get_teams(leagues[league_name])

            this_league_teams = []
            for team in api_teams_data: 
                # add the team with the given info the list of teams 
                this_league_teams.append(Team(
                    league=league_name, name=team["name"], logo = team["logo"], 
                    founded_year=team["founded_year"], description=team["description"],
                    home_stadium=team["home_stadium"], stadium_image=team["stadium_image"]
                ))
            if len(this_league_teams) > 0: 
                # one database query, which is much more efficient 
                Team.objects.bulk_create(this_league_teams)
                print(f"{len(this_league_teams)} teams of {league_name} uploaded successfully!")
            else: 
                print(f"There are no teams in {league_name} to upload.")
    # print the exception in case something happened for immediate inspection 
    except Exception as e: 
        traceback.print_exc()


# NESTING THE FUNCTION WITHIN 1 TRANSACTION
LEAGUES = {"Champions League": 2, "Premiere League": 39, "La Liga": 140, "Bundesliga": 78}
# CALLED EVERY WEEK at 0 hours
@transaction.atomic
def upload_matches_and_bets(): 
    for league_name in list(LEAGUES.keys()): 
        print(f"For {league_name}")
        league_match_list = upload_matches(league_name, LEAGUES[league_name])
        upload_match_bets(league_match_list)


# CALLED EVERY HOUR AT 0 hours
@transaction.atomic
def update_scores_and_settle(): 
    for league_name in list(LEAGUES.keys()): 
        # matches are finished, and their associated bets are settled
        updated_match_list = update_match_scores(LEAGUES[league_name])
        settle_bets(updated_match_list)


# CALLED EVERY DAY AT 0 hours
# delete the queryset of the bet infos and finished matches that have been their past days limit 
@transaction.atomic
def delete_past_betinfos_and_matches() -> None: 
    try:
        # bet info's past day limit is 14 days (2 weeks)
        info_filter_date = date.today() - timedelta(weeks=2)
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

    except Exception as e: 
        print("Error occured, ", e)


# process the date and return the string for API calling
def get_date_str(arg_date: date) -> str: 
     # process the first date 
    year, month, day = arg_date.year, arg_date.month, arg_date.day
    if month < 10 and day < 10: 
        date_str = f"{year}-0{month}-0{day}"
    elif month < 10 and day > 10: 
        date_str = f"{year}-0{month}-{day}"
    elif month > 10 and day < 10: 
        date_str = f"{year}-{month}-0{day}"
    else: 
        date_str = f"{year}-{month}-{day}"
    return date_str


# upload data about the matches and bets for each match to the database 
def upload_matches(league_name: str, league_id: int) -> QuerySet[Match]: 
    # process the first date and last date of the week 
    from_date_str = get_date_str(date.today())
    to_date_str = get_date_str(date.today() + timedelta(days=7))

    # from_date_str, to_date_str = "2024-10-22", "2024-10-29" # used for testing 
    try: 
        api_matches_data = get_not_started_matches(league_id, from_date_str, to_date_str)
        not_started_matches= [] # list of Match objects 

        for match in api_matches_data: 
            # process the date a little bit 
            match_date = timezone.datetime.fromisoformat(match["date"])
            # add the new match to the list 
            not_started_matches.append(Match(
                league=league_name, match_id=match["match_id"], date=match_date, 
                home_team=match["home_team"], home_team_logo=match["home_team_logo"],
                away_team=match["away_team"], away_team_logo=match["away_team_logo"]
            ))
        if len(not_started_matches) > 0: 
            # only one database query 
            created_matches = Match.objects.bulk_create(not_started_matches) 
            # notify the user 
            print(f"{len(not_started_matches)} matches of {league_name} uploaded successfully!")
        else: 
            created_matches = Match.objects.none() # an empty queryset 
            print(f"There are not matches in {league_name} to upload.")
    except Exception as e: 
        traceback.print_exc()
    # return the queryset of matches that have been saved to the database
    return created_matches


# upload of the bets for each match in the list of arg_matches
def upload_match_bets(arg_matches: QuerySet[Match]) -> None: 
    try: 
        for match in arg_matches:  
            # save the data about the moneyline bets of the match to database
            moneyline_info_data = get_moneyline_bets("moneyline", match.match_id, match.home_team, match.away_team)
            moneyline_bet_infos = [] # list of MoneylineBetInfo objs 

            for bet_info in moneyline_info_data:
                moneyline_bet_infos.append(MoneylineBetInfo(
                    match=match, time_type=bet_info["time_type"], bet_team=bet_info["bet_team"],
                    odd=bet_info["odd"]
                )) 
            if len(moneyline_bet_infos) > 0:
                MoneylineBetInfo.objects.bulk_create(moneyline_bet_infos) # one database query
                # notify bets have been saved
                print(f"{len(moneyline_bet_infos)} moneyline bets of match {match.match_id} uploaded successfully!") 
            else: 
                print(f"No moneyline bets of match {match.match_id} to upload.")

            # save the data about the handicap bets of the match to the database
            handicap_info_data = get_moneyline_bets("handicap", match.match_id, match.home_team, match.away_team)
            handicap_bet_infos = []

            for bet_info in handicap_info_data: 
                handicap_bet_infos.append(HandicapBetInfo(
                    match=match, time_type=bet_info["time_type"], bet_team=bet_info["bet_team"], 
                    handicap_cover=bet_info["handicap_cover"], odd=bet_info["odd"]
                ))
            if len(handicap_bet_infos) > 0: 
                HandicapBetInfo.objects.bulk_create(handicap_bet_infos)
                print(f"{len(handicap_bet_infos)} handicap bets of match {match.match_id} uploaded successfully!") 
            else: 
                print(f"No handicap bets of match {match.match_id} to upload.")
                                        
            # save the data about the total goals bet of the match to the database
            total_goals_info_data = get_total_goals_bets(match.match_id, match.home_team, match.away_team)
            total_goals_bet_infos = [] 

            for bet_info in total_goals_info_data: 
                total_goals_bet_infos.append(TotalGoalsBetInfo(
                    match=match, time_type=bet_info["time_type"], under_or_over=bet_info["under_or_over"], 
                    target_num_goals=bet_info["num_goals"], odd=bet_info["odd"]
                ))
            if len(total_goals_bet_infos) > 0: 
                TotalGoalsBetInfo.objects.bulk_create(total_goals_bet_infos)
                print(f"{len(total_goals_bet_infos)} total goals bets of match {match.match_id} uploaded successfully!")
            else: 
                print(f"No total goals bets of match {match.match_id} to upload.")
    except Exception as e: 
        traceback.print_exc()


# update the score of the matches 
def update_match_scores(league_id: int) -> QuerySet[Match]: 
    # process the given date 
    given_date_str = get_date_str(date.today())

    # given_date_str = "2024-10-23" # used for testing 
    try: 
        match_scores_data = get_match_score(league_id, given_date_str)
        queried_matches = [] # list of Match objects 

        for i, match_score in enumerate(match_scores_data):
            try: 
                queried_matches.append(Match.objects.get(match_id=match_score["match_id"]))
                # update the required attributes 
                queried_matches[i].status = "Finished"
                queried_matches[i].updated_date = date.today()
                queried_matches[i].halftime_score = match_score["halftime"]
                queried_matches[i].fulltime_score = match_score["fulltime"]
                queried_matches[i].penalty = match_score["penalty"]
            except Match.DoesNotExist: 
                pass # if the match doesn't exist, move to the next score 
    
        # only do the database operation if list is not empty 
        if len(queried_matches) > 0: 
            updated_field_list = ["status", "updated_date", "halftime_score", "fulltime_score", "penalty"]
            num_updated_matches = Match.objects.bulk_update(queried_matches, updated_field_list) # 1 query

            # get the updated queryset 
            updated_matches = Match.objects.filter(match_id__in=[match.match_id for match in queried_matches])
            # notify the user that matches have been updated 
            print(f"{num_updated_matches} finished matches updated successfully!")  
        else: 
            updated_matches = Match.objects.none() 
            print("No matches finished that need to be updated!")         
    # if an error occured , print the error
    except Exception as e: 
        traceback.print_exc()
    # return the list of the matches that have been updated 
    return updated_matches


# Settle all of the bets that are associated 
def settle_bets(arg_matches: QuerySet[Match]) -> None: 
    try: 
        for match in arg_matches: 
            # settle all the moneyline bets of the match 
            moneyline_bet_infos = MoneylineBetInfo.objects.filter(match=match)
            for bet_info in moneyline_bet_infos: 
                moneyline_bets = UserMoneylineBet.objects.filter(bet_info=bet_info)
                # settle the list of moneyline bets 
                settle_moneyline_bet_list(moneyline_bets)
                # update the status and settled date of list of bets 
                moneyline_bets.update({"status": "Settled", "settled_date": date.today()})
                        
            # settle all the handicap bets of the match 
            handicap_bet_infos = HandicapBetInfo.objects.filter(match=match)
            for bet_info in handicap_bet_infos: 
                handicap_bets = UserHandicapBet.objects.filter(bet_info=bet_info)
                settle_handicap_bet_list(handicap_bets)
                handicap_bets.update({"status": "Settled", "settled_date": date.today()})
                            
            # settle all the total goals bets of the match 
            total_goals_bet_infos = TotalGoalsBetInfo.objects.filter(match=match)
            for bet_info in total_goals_bet_infos: 
                total_goals_bets = UserTotalGoalsBet.objects.filter(bet_info=bet_info)
                settle_total_goals_bet_list(total_goals_bets)
                total_goals_bets.update({"status": "Settled", "settled_date": date.today()})
    except Exception as e: 
        traceback.print_exc()


def main(): 
    upload_teams()

if __name__ == "__main__":
    main()