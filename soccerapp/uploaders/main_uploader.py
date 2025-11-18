from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from soccerapp.uploaders.api import (
    get_teams, get_league_standings, get_not_started_matches, get_match_score
)
from soccerapp.models import Team, TeamRanking, Match, MatchStat
from datetime import date, timedelta
import traceback
from soccerapp.uploaders.api import get_date_str

@transaction.atomic
def upload_teams() -> None: 
    """
    Upload data about the teams (for the comment and section part of the website).
    CALLED EVERY YEAR MANUALLY
    """
    league_dict = {
        "Premiere League": 39, 
        "La Liga": 140, 
        "Bundesliga": 78,
        "Serie A": 135,
        "Ligue 1": 61, 
        "Champions League": 2,
    }
    try: 
        for league in list(league_dict.keys()): 
            teams_data = get_teams(league_dict[league])
            existing_teams = set(team.name for team in Team.objects.all())
            teams = []
            for item in teams_data: 
                if item["name"] not in existing_teams:
                    teams.append(Team(league=league, **item))

            created_teams = Team.objects.bulk_create(teams)
            print(f"{len(created_teams)} teams of {league} uploaded!") 
    except Exception as e: 
        # Print the exception in case something happened for immediate inspection
        traceback.print_exc()


def upload_team_rankings() -> None: 
    """ Upload (or update) data about the standings of the team """
    leagues = {
        "Champions League": 2,
        "Premiere League": 39, 
        "La Liga": 140, 
        "Bundesliga": 78,
        "Serie A": 135,
        "Ligue 1": 61,
    }
    for name in list(leagues.keys()): 
        # Delete the current standings 
        TeamRanking.objects.filter(league=name).delete()
        # Import the new standings 
        ranks_data = get_league_standings(leagues[name])
        league_standings = []
        for rank in ranks_data:
            team=Team.objects.get(name=rank.pop("team"))
            league_standings.append(TeamRanking(league=name, team=team, **rank))

        TeamRanking.objects.bulk_create(league_standings)
        print(f"Standings of {name} uploaded or updated!")


def generic_upload_matches(
    league_name: str, league_id: int, from_date: str, to_date: str
) -> QuerySet[Match]: 
    """Upload data about the matches between 2 given dates to the database"""
    matches_data = get_not_started_matches(league_id, from_date, to_date)
    upcoming_matches = []

    for item in matches_data:
        # Process the data a little bit
        started_at = timezone.datetime.fromisoformat(item["started_at"])
        home_team = Team.objects.get(name=item["home_team"])
        away_team = Team.objects.get(name=item["away_team"])

        # Add the new match to the list
        upcoming_matches.append(Match(
            league=league_name,
            match_id=item["match_id"], started_at=started_at,
            home_team=home_team, away_team=away_team
        ))

    created_matches = Match.objects.bulk_create(upcoming_matches) 
    print(f"{len(created_matches)} matches of {league_name} uploaded!")
    return created_matches


def upload_matches(league_name: str, league_id: int) -> QuerySet[Match]: 
    """Upload data about the matches periodically to the database"""
    # First date and last date of the week 
    from_date = get_date_str(date.today())
    to_date = get_date_str(date.today() + timedelta(days=7))
    return generic_upload_matches(league_name, league_id, from_date, to_date)


def generic_update_match_scores(
    league_name: str, league_id: int, given_date_str: str
) -> QuerySet[Match]: 
    """Update the score of the matches on the given date"""
    match_scores_data = get_match_score(league_id, given_date_str)
    matches, stats = [], []

    for item in match_scores_data:
        try: 
            # Get the match that is already finished but "Not Finished" in the DB
            match = Match.objects.get(match_id=item["match_id"], status="Not Finished")
            # update the main score
            match.status = "Finished"
            match.updated_at = date.today()

            matches.append(match)
            stats.append(MatchStat(match=match, **item["stat"]))

        except Match.DoesNotExist: 
            # If the match doesn't exist, move to the next match
            pass
    
    num_updated = Match.objects.bulk_update(matches, ["status", "updated_at"])
    create_stats = MatchStat.objects.bulk_create(stats)

    if num_updated != 0:
        if len(create_stats) // num_updated == 7:
            raise RuntimeError("Not importing necessary stats")
    
    # Get the updated queryset 
    updated_matches = Match.objects.filter(
        match_id__in=[match.match_id for match in matches]
    )
    print(f"{num_updated} finished matches of {league_name} updated!")  
    return updated_matches


def update_match_scores(league_name: str, league_id: int) -> QuerySet[Match]: 
    """Update the scores of matches finished today"""
    today = get_date_str(date.today())
    return generic_update_match_scores(league_name, league_id, today)

if __name__ == "__main__": None