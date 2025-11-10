import requests
import json
import environ
from datetime import date, timedelta


def get_date_str(arg_date: date) -> str: 
    """ Process the date and return the string for API calling. """

    # Process the first date 
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


def get_api_response(endpoint: str): 
    base_url = "https://v3.football.api-sports.io"
    env = environ.Env()
    environ.Env.read_env()

    # API-key obtained from subscription to API-Football
    raw_response = requests.get(
        f"{base_url}/{endpoint}", 
        headers={
            'x-rapidapi-key': env("API_KEY"), 
            'x-rapidapi-host': 'v3.football.api-sports.io'
        },
    )
    response = json.loads(raw_response.text)["response"]
    return response


def convert_american_odd(decimal_odd: float) -> int: 
    """
    Football-API is from France, so they use a different system of odd convert the obtained decimal odd 
    and covert them to American odd
    """ 
    if decimal_odd >= 2.00: 
        american_odd = round((decimal_odd - 1) * 100)
    elif decimal_odd < 2.00: 
        american_odd = round(-100 / (decimal_odd - 1))
    return american_odd


def get_teams(league_id: int) -> list: 
    """ Get the info about the team this season """
    # Call the api to get raw data
    response = get_api_response(f"teams?league={league_id}&season=2025")

    # Process the raw data 
    league_team_list = []
    for team in response: 
        # Add the info of team with given information to the list 
        league_team_list.append({
            "name": team["team"]["name"],
            "logo": team["team"]["logo"],
            "founded_year": team["team"]["founded"],
            "home_stadium": team["venue"]["name"],
            "stadium_image": team["venue"]["image"],
            "description": f"",
        })
    return league_team_list


def get_not_started_matches(league_id: int, from_date: str, to_date: str) -> list:
    """ Get the upcoming matches, should be called every week  """

    # Param is the endpoint to call matches
    response = get_api_response(
        f"fixtures?league={league_id}&season=2025&from={from_date}&to={to_date}")

    upcoming_match_list = []
    for fixture in response:
        # Add the upcoming match with given information to the list 
        upcoming_match_list.append({
            "match_id": fixture["fixture"]["id"],
            "date": fixture["fixture"]["date"],
            "home_team": fixture["teams"]["home"]["name"],
            "home_team_logo": fixture["teams"]["home"]["logo"],
            "away_team": fixture["teams"]["away"]["name"],
            "away_team_logo": fixture["teams"]["away"]["logo"],
        })
    return upcoming_match_list


def get_match_score(league_id: int, date: str) -> list:
    """ Get the scores of all the matches of the given league on the given date """
    response = get_api_response(
        f"fixtures?date={date}&league={league_id}&season=2025&status=FT-AET-PEN")
 
    match_result_list = []
    for fixture in response:
        half_score = fixture["score"]["halftime"]
        full_score = fixture["score"]["fulltime"]
        penalty = fixture["score"]["penalty"]

        # Get other stats of the matches of the league on the date 
        response = get_api_response(f"fixtures/statistics?fixture={fixture["fixture"]["id"]}")
        home_stat = response[0]["statistics"]
        away_stat = response[1]["statistics"]

        # Add the score to the the list of scores
        # The game in the format "{home team's goals} - {away team"s goals}"
        match_result = {
            "match_id": fixture["fixture"]["id"], 
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
    """ Get the standing of the league (should be every day) """

    raw_response = get_api_response(f"standings?league={league_id}&season=2025")
    response = []
    if len(raw_response) > 0: 
        response = raw_response[0]["league"]["standings"][0]

    standing_list = []
    for standing in response: 
        # Standing includes the rank, team, points, num_matches, wins, draws, and loses
        # Add the standing to the list 
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
    Call the api to get the data about the bet for given object with the given type 
    """
    response = {"Half-time": [], "Full-time": []}

    # Dictionary to map bet type to fulltime and halftime bet IDs
    if bet_object == "Goals":
        type_to_id_dict = {
            "moneyline": (13, 1), "handicap": (19, 9), "total_objects": (6, 5)}
        bookmaker = 1
    elif bet_object == "Corners":
        type_to_id_dict = {
            "moneyline": (130, 55), "handicap": (125, 56), "total_objects": (77, 45)}
        bookmaker = 11
    elif bet_object == "Cards":
        type_to_id_dict = {
            "moneyline": (161, 158), "handicap": (159, 81), "total_objects": (155, 80)}
        bookmaker = 8

    ht_bet_id, ft_bet_id = type_to_id_dict[bet_type]

    # Different bookmakers offer different objects
    # Response full-time and half-time 
    ht_response = get_api_response(
        f"odds?fixture={match_id}&season=2025&bookmaker={bookmaker}&bet={ht_bet_id}")
    ft_response = get_api_response(
        f"odds?fixture={match_id}&season=2025&bookmaker={bookmaker}&bet={ft_bet_id}")
    
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
    for time_type in list(response.keys()): 
        for winner_odd in response[time_type]: 
            winner_bet_value = winner_odd["value"].split()

            if winner_bet_value[0] == "Home": bet_team = home_team
            elif winner_bet_value[0] == "Away": bet_team = away_team 
            else: 
                if bet_type == "handicap": 
                    # If the type of bet is moneyline, account for draw. 
                    # Otherwise, go the next bets 
                    continue
                bet_team = winner_bet_value[0] 

            try: 
                american_odd = convert_american_odd(float(winner_odd["odd"]))
            except ZeroDivisionError: 
                # Zero division (the bet has odd 1): 
                # The european odd can't be converted to american odd
                continue

            # Structure of the moneyline (or handicap) bet 
            winner_bet = {
                "match": f"{home_team} vs {away_team}",
                "time_type": time_type,
                "bet_object": bet_object,
                "bet_team": bet_team, 
                "odd": american_odd,
            }
            if bet_type == "handicap": 
                # If the type of bet is handicap, add the handicap coverage 
                winner_bet["handicap_cover"] = float(winner_bet_value[1])

            # Add the bet of the list 
            object_winner_bet_list.append(winner_bet)   
    return object_winner_bet_list
        

def get_winner_bets(bet_type: str, match_id: int, home_team: str, away_team: str) -> list : 
    """ Get moneyline or handicap bets for goals, corners and cards  """
    winner_bet_list = []
    for bet_object in ["Goals", "Corners", "Cards"]: 
        winner_bet_list.extend(
            get_object_winner_bets(
                bet_object, bet_type, match_id, home_team, away_team
            )
        )
    return winner_bet_list


def get_object_total_bets(
    bet_object: str, match_id: int, home_team: str, away_team: str
) -> list: 
    """
    Get the total goals bets for match with given ID.
    ```bet_object: "Goals" or "Corners" or "Cards"
    """
    response = get_objects_bets(bet_object, "total_objects", match_id)
    total_objects_bet_list = [] 

    for time_type in list(response.keys()): 
        for total_objects_odd in response[time_type]: 
            under_or_over_value = total_objects_odd["value"].split()[0]
            target_num = float(total_objects_odd["value"].split()[1])

            try: 
                american_odd = convert_american_odd(float(total_objects_odd["odd"]))
            except ZeroDivisionError: 
                continue

            total_objects_bet_list.append({
                "match": f"{home_team} vs {away_team}", 
                "time_type": time_type,
                "bet_object": bet_object,
                "under_or_over": under_or_over_value, 
                "num_objects": target_num, 
                "odd": american_odd,
            })
    return total_objects_bet_list


def get_total_bets(match_id: int, home_team: str, away_team: str) -> list: 
    """ Get total bets for goals, corners, and cards """
    total_objects_bet_list = []
    for bet_object in ["Goals", "Corners", "Cards"]: 
        total_objects_bet_list.extend(
            get_object_total_bets(
                bet_object, match_id, home_team, away_team
            )
        )
    return total_objects_bet_list


if __name__ == "__main__": 
    leagues = {"ucl": 2, "epl": 39, "lal": 140, "bun": 78}
    from_date = get_date_str(date.today())
    weekday = date.today().weekday()

    if weekday >= 0 and weekday <= 3: # monday to thursday
        to_date = get_date_str(date.today() + timedelta(days=(3 - weekday)))
    else: # friday to sunday
        to_date = get_date_str(date.today() + timedelta(days=(6 - weekday)))

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
                "moneyline_bets": get_winner_bets("moneyline", match_id, home, away), 
                "handicap_bets": get_winner_bets("handicap", match_id, home, away), 
                "total_goals_bets": get_total_bets(match_id, home, away),
            }
            print(json.dumps(response, indent=4))