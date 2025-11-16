from django.db import transaction
from django.db.models import QuerySet, Count
from django.utils import timezone
from soccerapp.uploaders.api import (
    get_teams, get_league_standings, get_not_started_matches, 
    get_winner_bets, get_total_bets, get_match_score
)
from soccerapp.settle import settle_bet_list
from soccerapp.models import (
    Team, TeamRanking, Match,
    MoneylineBetInfo, HandicapBetInfo, TotalObjectsBetInfo, 
    UserMoneylineBet, UserHandicapBet, UserTotalObjectsBet
) 
from datetime import date, timedelta
import traceback
from soccerapp.uploaders.api import get_date_str

@transaction.atomic
def upload_teams() -> None: 
    """
    Upload data about the teams (for the comment and section part of the website).
    CALLED EVERY YEAR MANUALLY
    """
    leagues = {
        "Premiere League": 39, 
        "La Liga": 140, 
        "Bundesliga": 78,
        "Serie A": 135,
        "League 1": 61, 
    }
    try: 
        for league_name in list(leagues.keys()): 
            api_teams_data = get_teams(leagues[league_name])
            league_teams = []
            for team in api_teams_data:  
                league_teams.append(Team(league=league_name, **team))
            Team.objects.bulk_create(league_teams)
            print(f"{len(league_teams)} teams of {league_name} uploaded successfully!") 
    except Exception as e: 
        # print the exception in case something happened for immediate inspection
        traceback.print_exc()


def upload_team_rankings() -> None: 
    """ Upload (or update) data about the standings of the team """

    leagues = {
        "Premiere League": 39, 
        "La Liga": 140, 
        "Bundesliga": 78,
        "Serie A": 135,
        "League 1": 61,
    }

    for name in list(leagues.keys()): 
        # delete the current standings 
        TeamRanking.objects.filter(league=name).delete()

        # import the new standings 
        api_ranks_data = get_league_standings(leagues[name])
        league_standings = []
        for rank in api_ranks_data: 
            league_standings.append(TeamRanking(
                league=name, team=Team.objects.get(name=rank["team"]), 
                rank=rank["rank"], points=rank["points"], 
                num_watches=rank["num_matches"], num_wins=rank["num_wins"], 
                num_loses=rank["num_loses"], num_draws=rank["num_draws"],
            ))

        TeamRanking.objects.bulk_create(league_standings)
        print(f"Standings of {name} uploaded or updated successfully!")


def generic_upload_matches(
    league_name: str, league_id: int, from_date_str: str, to_date_str: str
) -> QuerySet[Match]: 
    """ Upload data about the matches between 2 given dates to the database. """

    # call the API 
    api_matches_data = get_not_started_matches(league_id, from_date_str, to_date_str)
    not_started_matches= [] # list of Match objects 

    for match in api_matches_data: 
        # process the date a little bit 
        match_date = timezone.datetime.fromisoformat(match["date"])
        # add the new match to the list 
        not_started_matches.append(Match(
            league=league_name, 
            match_id=match["match_id"], date=match_date, 
            home_team=match["home_team"], home_team_logo=match["home_team_logo"],
            away_team=match["away_team"], away_team_logo=match["away_team_logo"]
        ))
  
    created_matches = Match.objects.bulk_create(not_started_matches, batch_size=100) 

    # notify the user 
    print(f"{len(created_matches)} matches of {league_name} uploaded successfully!")
    return created_matches


def upload_matches(league_name: str, league_id: int) -> QuerySet[Match]: 
    """ Upload data about the matches automatically and periodically to the database. """

    # process the first date and last date of the week 
    from_date_str = get_date_str(date.today())
    weekday = date.today().weekday()
    if weekday >= 0 and weekday <= 3: # monday to thursday
        to_date_str = get_date_str(date.today() + timedelta(days=(3 - weekday)))
    else: # friday to sunday
        to_date_str = get_date_str(date.today() + timedelta(days=(6 - weekday)))

    # call above function 
    return list(generic_upload_matches(league_name, league_id, from_date_str, to_date_str))


def upload_match_bets(arg_matches: QuerySet[Match]) -> None: 
    """ Upload of the bets for each match in the list of given matches in arguments """

    for match in arg_matches:  
        # save the data about the moneyline bets of the match to database
        moneyline_info_data = get_winner_bets("moneyline", match.match_id, match.home_team, match.away_team)
        moneyline_info_list = []

        for bet_info in moneyline_info_data:
            moneyline_info_list.append(MoneylineBetInfo(
                match=match, 
                time_type=bet_info["time_type"], 
                bet_object=bet_info["bet_object"], bet_team=bet_info["bet_team"], 
                odd=bet_info["odd"]
            )) 
            
        created_moneyline = MoneylineBetInfo.objects.bulk_create(moneyline_info_list, batch_size=100) 
        print(f"{len(created_moneyline)} moneyline bets of match {match} uploaded successfully!") 

        # save the data about the handicap bets of the match to the database
        handicap_info_data = get_winner_bets("handicap", match.match_id, match.home_team, match.away_team)
        handicap_info_list = []

        for bet_info in handicap_info_data: 
            handicap_info_list.append(HandicapBetInfo(
                match=match, 
                time_type=bet_info["time_type"], 
                bet_object=bet_info["bet_object"],  bet_team=bet_info["bet_team"], 
                handicap_cover=bet_info["handicap_cover"], odd=bet_info["odd"]
            ))
        created_handicap = HandicapBetInfo.objects.bulk_create(handicap_info_list, batch_size=100)
        print(f"{len(created_handicap)} handicap bets of match {match} uploaded successfully!") 
                   
        # save the data about the total goals bet of the match to the database
        total_info_data = get_total_bets(match.match_id, match.home_team, match.away_team)
        total_info_list = [] 

        for bet_info in total_info_data: 
            total_info_list.append(TotalObjectsBetInfo(
                match=match, 
                time_type=bet_info["time_type"], 
                bet_object=bet_info["bet_object"], under_or_over=bet_info["under_or_over"], 
                target_num_objects=bet_info["num_objects"], odd=bet_info["odd"]
            ))
        created_total = TotalObjectsBetInfo.objects.bulk_create(total_info_list, batch_size=100)
        print(f"{len(created_total)} total goals bets of match {match} uploaded successfully!")


def generic_update_match_scores(league_name: str, league_id: int, given_date_str: str) -> QuerySet[Match]: 
    """ Update the score of the matches on the given date """
    
    match_scores_data = get_match_score(league_id, given_date_str)
    matches = [] # List of Match objects 

    for match_score in match_scores_data:
        try: 
            # Get the match that is already finished but "Not Finished" in the DB
            match = Match.objects.get(match_id=match_score["match_id"], status="Not Finished")
            # update the main score
            match.status = "Finished"
            match.updated_date = date.today()
            match.halftime_score = match_score["halftime"]
            match.fulltime_score = match_score["fulltime"]
            match.penalty = match_score["penalty"]

            # update the other stats for users to see 
            match.possesion = match_score["possession"]
            match.total_shots = match_score["total_shots"]
            match.corners = match_score["corners"]
            match.cards = match_score["cards"]
            matches.append(match)

        except Match.DoesNotExist: 
            # If the match doesn't exist, move to the next match
            pass
    
    updated_field_list = [
        "status", 
        "updated_date", 
        "halftime_score", 
        "fulltime_score", 
        "penalty", 
        "possesion", 
        "total_shots", 
        "corners", 
        "cards"
    ]
    num_updated_matches = Match.objects.bulk_update(matches, updated_field_list, batch_size=100)

    # Get the updated queryset 
    updated_matches = Match.objects.filter(match_id__in=[match.match_id for match in matches])
    print(f"{num_updated_matches} finished matches of {league_name} updated successfully!")  
    
    return updated_matches


def update_match_scores(league_name: str, league_id: int) -> QuerySet[Match]: 
    """Update the matches scores of matches finished today"""
    given_date_str = get_date_str(date.today())
    # call above function 
    return generic_update_match_scores(league_name, league_id, given_date_str)


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
        # settle all the moneyline bets of the match 
        moneyline_bet_list = UserMoneylineBet.objects.filter(bet_info__match=match)
        total, _ = settle_bet_list("moneyline", moneyline_bet_list)

        # update the status and settled date of list of bet info
        MoneylineBetInfo.objects.filter(match=match).update(
            status="Settled", 
            settled_date=date.today()
        )
        print(f"{total} moneyline bets of match {match} settled!")
                        
        # settle all the handicap bets of the match 
        handicap_bet_list = UserHandicapBet.objects.filter(bet_info__match=match)
        total, _ = settle_bet_list("handicap", handicap_bet_list)

        # update the status and settled date
        HandicapBetInfo.objects.filter(match=match).update(
            status="Settled", 
            settled_date=date.today()
        )
        print(f"{total} handicap bets of match {match} settled!")
                            
        # settle all the total goals bets of the match 
        total_goals_bet_list = UserTotalObjectsBet.objects.filter(bet_info__match=match)
        total, _ = settle_bet_list("total_objects", total_goals_bet_list)
        
        # update the status and settled date 
        TotalObjectsBetInfo.objects.filter(match=match).update(
            status="Settled", 
            settled_date=date.today()
        )
        print(f"{total} total objects bets of match {match} settled!")

if __name__ == "__main__": None