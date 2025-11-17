import requests
import json
import environ
from datetime import date, timedelta
from typing import Any, List


def get_date_str(date: date) -> str: 
    """Convert date to string for API calling"""
    year, month, day = date.year, date.month, date.day
    if month < 10 and day < 10: 
        date_str = f"{year}-0{month}-0{day}"
    elif month < 10 and day > 10: 
        date_str = f"{year}-0{month}-{day}"
    elif month > 10 and day < 10: 
        date_str = f"{year}-{month}-0{day}"
    else: 
        date_str = f"{year}-{month}-{day}"
    return date_str


def get_api_response(endpoint: str) -> Any: 
    env = environ.Env()
    environ.Env.read_env()
    # API-key obtained from subscription to API-Football
    raw_response = requests.get(
        f"https://v3.football.api-sports.io/{endpoint}", 
        headers={
            'x-rapidapi-key': "ff80d75fb2fa72353ed4c5092a474eac", 
            'x-rapidapi-host': 'v3.football.api-sports.io',
        }
    )
    response = json.loads(raw_response.text)["response"]
    return response


def convert_american_odd(european_odd: float) -> int: 
    """
    Football-API is from France, so they use a different system of odd.
    Convert the obtained decimal odd to American odd
    """ 
    if european_odd >= 2.00: 
        american_odd = round((european_odd - 1) * 100)
    elif european_odd < 2.00: 
        american_odd = round(-100 / (european_odd - 1))
    return american_odd


def get_teams(league_id: int) -> List: 
    """Get the info about the team this season"""
    response = get_api_response(f"teams?league={league_id}&season=2025")

    # Process the raw data 
    team_list = []
    for item in response: 
        team_list.append({
            "name": item["team"]["name"],
            "logo": item["team"]["logo"],
            "founded_year": item["team"]["founded"],
            "home_stadium": item["venue"]["name"],
            "stadium_image": item["venue"]["image"],
        })
    return team_list


def get_not_started_matches(league_id: int, from_date: str, to_date: str) -> List:
    """Get the upcoming matches, should be called every week"""
    # Param is the endpoint to call matches
    response = get_api_response(
        f"fixtures?league={league_id}&season=2025&from={from_date}&to={to_date}")

    upcoming_match_list = []
    for match in response:
        upcoming_match_list.append({
            "match_id": match["fixture"]["id"],
            "started_at": match["fixture"]["date"],
            "home_team": match["teams"]["home"]["name"],
            "away_team": match["teams"]["away"]["name"],
        })
    return upcoming_match_list


def get_match_score(league_id: int, date: str) -> list:
    """Get the scores of all the matches of the given league on the given date"""
    response = get_api_response(
        f"fixtures?date={date}&league={league_id}&season=2025&status=FT-AET-PEN")
 
    match_result_list = []
    for match in response:
        half_score = match["score"]["halftime"]
        full_score = match["score"]["fulltime"]
        penalty = match["score"]["penalty"]

        # Get other stats of the matches of the league on the date 
        response = get_api_response(f"fixtures/statistics?fixture={match["fixture"]["id"]}")
        home_stat = response[0]["statistics"]
        away_stat = response[1]["statistics"]

        # Add the score to the the list of scores
        match_result = {
            "match_id": match["fixture"]["id"], 
            "halftime": f"{half_score["home"]}-{half_score["away"]}", 
            "fulltime": f"{full_score["home"]}-{full_score["away"]}",
            "penalty": f"{penalty["home"]}-{penalty["away"]}",
            "total_shots": f"{home_stat[2]["value"]}-{away_stat[2]["value"]}",
            "possession": f"{home_stat[9]["value"]}-{away_stat[9]["value"]}",
            "corners": f"{home_stat[7]["value"]}-{away_stat[7]["value"]}",
            "cards": f"{home_stat[10]["value"]}-{away_stat[10]["value"]}"
        }
        match_result_list.append(match_result)

    return match_result_list
 

def get_league_standings(league_id: int) -> dict: 
    """Get the standing of the league (should be every day)"""

    raw_response = get_api_response(f"standings?league={league_id}&season=2025")
    response = []
    if len(raw_response) > 0: 
        response = raw_response[0]["league"]["standings"][0]

    standing_list = []
    for standing in response: 
        standing_list.append({
            "rank": standing["rank"],
            "team": standing["team"]["name"], 
            "points": standing["points"], 
            "num_matches": standing["all"]["played"], 
            "num_wins": standing["all"]["win"], 
            "num_loses": standing["all"]["lose"], 
            "num_draws": standing["all"]["draw"],
        })
    return standing_list

 
def get_objects_bets(bet_object: str, bet_type: str, match_id: int) -> dict: 
    """ 
    Call the api to get the bet data for object with bet type 
    """
    response = {"Half-time": [], "Full-time": []}

    # Dictionary to map bet type to fulltime and halftime bet IDs
    if bet_object == "Goals":
        type_to_id = {"moneyline": (13, 1), "handicap": (19, 9), "total_objects": (6, 5)}
        bookmaker = 1
    elif bet_object == "Corners":
        type_to_id = {"moneyline": (130, 55), "handicap": (125, 56), "total_objects": (77, 45)}
        bookmaker = 11
    elif bet_object == "Cards":
        type_to_id = {"moneyline": (161, 158), "handicap": (159, 81), "total_objects": (155, 80)}
        bookmaker = 8
    else: 
        raise ValueError("Invalid bet object")

    halftime_id, fulltime_id = type_to_id[bet_type]

    # Different bookmakers offer different objects
    ht_response = get_api_response(
        f"odds?fixture={match_id}&season=2025&bookmaker={bookmaker}&bet={halftime_id}")
    ft_response = get_api_response(
        f"odds?fixture={match_id}&season=2025&bookmaker={bookmaker}&bet={fulltime_id}")
    
    # Load them into iterable JSON object 
    if len(ht_response) > 0: 
        response["Half-time"] = ht_response[0]["bookmakers"][0]["bets"][0]["values"]
    if len(ft_response) > 0: 
        response["Full-time"] = ft_response[0]["bookmakers"][0]["bets"][0]["values"]

    return response


def get_object_winner_bets(
    bet_object: str, bet_type: str, match_id: int, home_team: str, away_team: str
) -> list: 
    """
    Get the moneyline or handicap bets for the match (depending on user).
    ```bet_type: "moneyline" or "handicap"
    ```bet_object: "Goals" or "Corners" or "Cards"
    """  
    response = get_objects_bets(bet_object, bet_type, match_id)

    object_winner_bet_list = []
    for period in list(response.keys()): 
        for winner_odd in response[period]: 
            winner_value = winner_odd["value"].split()

            if winner_value[0] == "Home": bet_team = home_team
            elif winner_value[0] == "Away": bet_team = away_team 
            else: 
                if bet_type == "handicap": 
                    # If the type of bet is moneyline, account for draw. 
                    # Otherwise, go the next bets 
                    continue
                bet_team = winner_value[0] 
            try: 
                american_odd = convert_american_odd(float(winner_odd["odd"]))
            except ZeroDivisionError: 
                # Zero division (the bet has odd 1): 
                # The european odd can't be converted to american odd
                continue
            # Structure of the moneyline (or handicap) bet 
            winner_bet = {
                "period": period,
                "bet_object": bet_object,
                "bet_team": bet_team, 
                "odd": american_odd,
            }
            if bet_type == "handicap": 
                # If the type of bet is handicap, add the handicap coverage 
                winner_bet["cover"] = float(winner_value[1])

            # Add the bet of the list 
            object_winner_bet_list.append(winner_bet)   
    return object_winner_bet_list


def get_object_total_bets(
    bet_object: str, match_id: int, home_team: str, away_team: str
) -> list: 
    """
    Get the total goals bets for match with given ID.
    ```bet_object: "Goals" or "Corners" or "Cards"
    """
    response = get_objects_bets(bet_object, "total_objects", match_id)
    total_objects_bet_list = [] 

    for period in list(response.keys()): 
        for total_objects_odd in response[period]: 
            under_or_over = total_objects_odd["value"].split()[0]
            num_objects = float(total_objects_odd["value"].split()[1])
            try: 
                american_odd = convert_american_odd(float(total_objects_odd["odd"]))
            except ZeroDivisionError: 
                continue
            total_objects_bet_list.append({
                "period": period,
                "bet_object": bet_object,
                "under_or_over": under_or_over, 
                "num_objects": num_objects, 
                "odd": american_odd,
            })
    return total_objects_bet_list


def get_bets(bet_type: str, match_id: int, home_team: str, away_team: str) -> list: 
    """ Get bets of given type for goals, corners, and cards """
    bet_list = []
    for bet_object in ["Goals", "Corners", "Cards"]:
        if bet_type == "moneyline" or bet_type == "handicap":
            new_bets = get_object_winner_bets(
                bet_object, bet_type, match_id, home_team, away_team)
        else:
            new_bets = get_object_total_bets(
                bet_object, match_id, home_team, away_team)
        bet_list.extend(new_bets)
    return bet_list


if __name__ == "__main__": 
    leagues = {"ucl": 2, "epl": 39, "lal": 140, "bun": 78}
    from_date = get_date_str(date.today())
    to_date = get_date_str(date.today() + timedelta(days=7))

    # Get the matches from all the league 
    for league_name in list(leagues.keys()): 
        upcoming_ucl_matches = get_not_started_matches(leagues[league_name], from_date, to_date)
        for match in upcoming_ucl_matches: 
            match_id = match["match_id"]
            home = match["home_team"]
            away = match["away_team"]

            # 3 types of bet (full-time and half-time) of the match this turn 
            response = {
                "fixture": match, 
                "moneyline_bets": get_bets("moneyline", match_id, home, away), 
                "handicap_bets": get_bets("handicap", match_id, home, away), 
                "total_goals_bets": get_bets("total_objects", match_id, home, away),
            }
            print(json.dumps(response, indent=4))