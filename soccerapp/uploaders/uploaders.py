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
            existing = set(team.name for team in Team.objects.all())
            teams = []
            for item_data in teams_data:
                if item_data["name"] not in existing:
                    teams.append(Team(league=league, **item_data))
            created_teams = Team.objects.bulk_create(teams)
            print(f"{len(created_teams)} teams of {league} uploaded successfully!") 
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
        api_ranks_data = get_league_standings(leagues[name])
        league_standings = []
        for rank in api_ranks_data:
            team=Team.objects.get(name=rank.pop("team"))
            league_standings.append(TeamRanking(
                league=name, team=team, **rank
            ))

        TeamRanking.objects.bulk_create(league_standings)
        print(f"Standings of {name} uploaded or updated successfully!")


def generic_upload_matches(
    league_name: str, league_id: int, from_date: str, to_date: str
) -> QuerySet[Match]: 
    """Upload data about the matches between 2 given dates to the database"""
    matches_data = get_not_started_matches(league_id, from_date, to_date)
    upcoming_matches = []

    for item_data in matches_data:
        # Process the data a little bit
        started_at = timezone.datetime.fromisoformat(item_data["started_at"])
        home_team = Team.objects.get(name=item_data["home_team"])
        away_team = Team.objects.get(name=item_data["away_team"])

        # Add the new match to the list
        upcoming_matches.append(Match(
            league=league_name,
            match_id=item_data["match_id"], started_at=started_at,
            home_team=home_team, away_team=away_team
        ))

    created_matches = Match.objects.bulk_create(upcoming_matches, batch_size=100) 
    print(f"{len(created_matches)} matches of {league_name} uploaded successfully!")
    return created_matches


def upload_matches(league_name: str, league_id: int) -> QuerySet[Match]: 
    """Upload data about the matches periodically to the database"""
    # First date and last date of the week 
    from_date: str = get_date_str(date.today())
    to_date: str = get_date_str(date.today() + timedelta(days=7))
    return generic_upload_matches(league_name, league_id, from_date, to_date)


def upload_match_bets(matches: QuerySet[Match]) -> None: 
    """Upload of the bets for each match in the list of matches"""
    for match in matches:
        # Save the moneyline bets to database
        moneyline_info_data = get_winner_bets(
            "moneyline", match.match_id, match.home_team.name, match.away_team.name
        )
        existing = set()
        for info in match.moneylinebetinfo_set.all():
            existing.add((
                info.period, info.bet_object, info.bet_team, info.odd
            ))
        moneyline_info_list = []
        for item in moneyline_info_data:
            info = tuple(item[k] for k in ["period", "bet_object", "bet_team", "odd"])
            if info not in existing:
                moneyline_info_list.append(
                    MoneylineBetInfo(match=match, **item)
                ) 
        created = MoneylineBetInfo.objects.bulk_create(moneyline_info_list)
        print(f"{len(created)} moneyline bets of {match} uploaded successfully!") 

        # Save the handicap bets to the database
        handicap_info_data = get_winner_bets(
            "handicap", match.match_id, match.home_team.name, match.away_team.name
        )
        existing = set()
        for info in match.handicapbetinfo_set.all():
            existing.add((
                info.period, info.bet_object, info.bet_team, info.odd, info.cover
            ))
        handicap_info_list = []
        for item in handicap_info_data: 
            info = tuple(item[k] for k in ["period", "bet_object", "bet_team", "odd", "cover"])
            if info not in existing:
                handicap_info_list.append(
                    HandicapBetInfo(match=match, **item)
                )
        created = HandicapBetInfo.objects.bulk_create(handicap_info_list)
        print(f"{len(created)} handicap bets of {match} uploaded successfully!") 

        # Save the total goals bets to the database
        total_info_data = get_total_bets(
            match.match_id, match.home_team.name, match.away_team.name
        )
        existing = set()
        for info in match.handicapbetinfo_set.all():
            existing.add((
                info.period, info.bet_object, info.under_or_over, info.num_objects, info.odd
            ))
        total_info_list = [] 
        for item in total_info_data: 
            info = tuple(item[k] for k in ["period", "bet_object", "under_or_over", "num_objects", "odd"])
            if info not in existing:
                total_info_list.append(
                    TotalObjectsBetInfo(match=match, **item)
                )
        created = TotalObjectsBetInfo.objects.bulk_create(total_info_list)
        print(f"{len(created)} total object bets of {match} uploaded successfully!")


def generic_update_match_scores(
    league_name: str, league_id: int, given_date_str: str
) -> QuerySet[Match]: 
    """Update the score of the matches on the given date"""
    match_scores_data = get_match_score(league_id, given_date_str)
    matches = []

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
        "status", "updated_date", "halftime_score", "fulltime_score", "penalty", "possesion", "total_shots", "corners", "cards"
    ]
    num_updated_matches = Match.objects.bulk_update(
        matches, updated_field_list, batch_size=100
    )

    # Get the updated queryset 
    updated_matches = Match.objects.filter(
        match_id__in=[match.match_id for match in matches]
    )
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