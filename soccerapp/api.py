import requests
import json
import environ
from datetime import date, timedelta
from soccerapp.uploaders import get_date_str

env = environ.Env()
environ.Env.read_env() # reading .env file 

def get_api_response(endpoint: str): 
    base_url = "https://v3.football.api-sports.io"

    # API-key obtained from subscription to API-Football
    headers = {
        'x-rapidapi-key': env("API_KEY"), 
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    response = requests.get(f"{base_url}/{endpoint}", headers=headers, data={})
    response = json.loads(response.text)["response"]
    return response


def get_bet_ids(): 
    """ Get the ID of the bets, necessary only when to determine which bet to get info from """
    return get_api_response("/odds/bets/")
    

def get_goals_bets(bet_type: str, match_id: int) -> dict:
    """ Call the API to get the data about the bet for goals with the given type  """

    if bet_type == "moneyline": 
        fulltime_bet_id, halftime_bet_id = 1, 13 # id of the full-time and half-time moneyline bet 
    elif bet_type == "handicap":  
        fulltime_bet_id, halftime_bet_id = 9, 18 # id of the full-time and half-time handicap bet
    elif bet_type == "total_goals": 
        fulltime_bet_id, halftime_bet_id = 5, 6 # id of the full-time and half-time total goals bet
    else: 
        raise Exception("Invalid type of bets")

    # the endpoint of the URL 
    full_endpoint = f"odds?fixture={match_id}&season=2024&bookmaker=1&bet={fulltime_bet_id}"
    half_endpoint = f"odds?fixture={match_id}&season=2024&bookmaker=1&bet={halftime_bet_id}"

    # the response full-time and half-time 
    full_response = get_api_response(full_endpoint)
    half_response = get_api_response(half_endpoint)

    response = {
        "full time": [],
        "half time": []
    }
    # load them into JSON object, which is iterable 
    if len(full_response) > 0: 
        response["full time"] = full_response[0]["bookmakers"][0]["bets"][0]["values"]
    if len(half_response) > 0: 
        response["half time"] = half_response[0]["bookmakers"][0]["bets"][0]["values"]

    #print(json.dumps(response, indent=4)) 
    return response

 
def get_other_object_bets(bet_object: str, bet_type: str, match_id: int) -> dict: 
    """ Call the api to get the data about the bet for other types (corners, cards) with the given type """

    # currently, there are no moneyline bets for cards 
    if bet_object == "Cards" and bet_type == "moneyline": 
        return {
            "full time": []
        }

    if bet_type == "moneyline": 
        bet_id = 55 # moneyline bet is only offered for corners 
    elif bet_type == "handicap": 
        bet_id = 56 if bet_object == "Corners" else 79 # ids of corner and cards handicap bets
    elif bet_type == "total_goals": 
        bet_id = 45 if bet_object == "Corners" else 80 # ids of corner and cards total bets
    else: 
        raise Exception("Invalid type of bets ")

    # endpoint of the URL
    bookmaker = 8 if bet_object == "Cards" else 2 # different bookmakers offer different objects
    endpoint = f"odds?fixture={match_id}&season=2024&bookmaker={bookmaker}&bet={bet_id}"
    json_response = get_api_response(endpoint)

    response = {
        "full time": []
    }
    if len(json_response) > 0: 
        response["full time"] = json_response[0]["bookmakers"][0]["bets"][0]["values"]
        # limit the number of bets if there are too many
        if len(response["full time"]) > 10: 
            num_bets = len(response["full time"])
            response["full time"] = response["full time"][(num_bets - 10):num_bets]
            
    #print(json.dumps(response, indent=4))
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

    # call the api to get raw data
    response = get_api_response(f"teams?league={league_id}&season=2024")

    # process the raw data 
    league_team_list = []
    for team in response: 
        # add the info of team with given information to the list 
        league_team_list.append({
            "name": team["team"]["name"],
            "logo": team["team"]["logo"], 
            "founded_year": team["team"]["founded"], 
            "home_stadium": team["venue"]["name"], 
            "stadium_image": team["venue"]["image"], 
            "description": f"This is {team["team"]["name"]}",
        })
    return league_team_list


def get_not_started_matches(league_id: int, from_date: str, to_date: str) -> list:
    """ Get the upcoming matches, should be called every week  """

    # param is the endpoint to call matches
    response = get_api_response(f"fixtures?league={league_id}&season=2024&from={from_date}&to={to_date}")

    upcoming_match_list = []
    for fixture in response:
        # add the upcoming match with given information to the list 
        upcoming_match_list.append({
            "match_id": fixture["fixture"]["id"],
            "date": fixture["fixture"]["date"], 
            "home_team": fixture["teams"]["home"]["name"],
            "home_team_logo": fixture["teams"]["home"]["logo"],
            "away_team": fixture["teams"]["away"]["name"],
            "away_team_logo": fixture["teams"]["away"]["logo"], 
        })

    #print(json.dumps(upcoming_match_list, indent=4))
    return upcoming_match_list


def get_match_score(league_id: int, arg_date: str) -> list:
    """ Get the scores of all the matches of the given league on the given date """

    finished_endpoint = f"fixtures?date={arg_date}&league={league_id}&season=2024&status=FT-AET-PEN"
    response = get_api_response(finished_endpoint)
 
    match_result_list = []
    for fixture in response:
        halftime_score = fixture["score"]["halftime"]
        fulltime_score = fixture["score"]["fulltime"]
        penalty = fixture["score"]["penalty"]

        # add the score to the the list of scores 
        # the game in the format "{home team's goals} - {away team"s goals}"
        match_result = {
            "match_id": fixture["fixture"]["id"], 
            "halftime": f"{halftime_score["home"]}-{halftime_score["away"]}", 
            "fulltime": f"{fulltime_score["home"]}-{fulltime_score["away"]}",
            "penalty": f"{penalty["home"]}-{penalty["away"]}",
        }

        # get other stats of the matches of the given league on the given date 
        stat_endpoint = f"fixtures/statistics?fixture={fixture["fixture"]["id"]}"
        response = get_api_response(stat_endpoint)

        home_stat = response[0]["statistics"]
        away_stat = response[1]["statistics"]

        # concatenate the other statistics to the dictionary 
        match_result.update({
            "total_shots": f"{home_stat[2]["value"]}-{away_stat[2]["value"]}",
            "corners": f"{home_stat[7]["value"]}-{away_stat[7]["value"]}",
            "possession": f"{home_stat[9]["value"]}-{away_stat[9]["value"]}",
            "cards": f"{home_stat[10]["value"]}-{away_stat[10]["value"]}"
        })
        match_result_list.append(match_result)

    #print(json.dumps(match_result_list, indent=4))
    return match_result_list
 

def get_league_standings(league_id: int) -> dict: 
    """ Get the standing of the league (should be every day) """

    json_response = get_api_response(f"standings?league={league_id}&season=2024")
    response = []
    if len(json_response) > 0: 
        response = json_response[0]["league"]["standings"][0]

    standing_list = []
    for standing in response: 
        # the standing includes the rank, team, points, num_matches, wins, draws, and loses
        # add the standing to the list 

        standing_list.append({
            "rank": standing["rank"],
            "team": standing["team"]["name"], 
            "points": standing["points"], 
            "num_matches": standing["all"]["played"], 
            "num_wins": standing["all"]["win"], 
            "num_loses": standing["all"]["lose"], 
            "num_draws": standing["all"]["draw"],
        })

    #print(json.dumps(standing_list, indent=4))
    return standing_list
        
  
def get_obj_winner_bets(
        bet_obj: str, bet_type: str, match_id: int, home_team: str, away_team: str
    ) -> list: 
    """         
    Get the moneyline or handicap bets for the match (depending on user).

    bet_type: "moneyline" or "handicap", 

    bet_obj: "Goals" or "Corners" or "Cards"
    """  

    if bet_obj == "Goals": 
        response = get_goals_bets(bet_type, match_id)
    else: 
        response = get_other_object_bets(bet_obj, bet_type, match_id)

    obj_winner_bet_list = []
    for time_type in list(response.keys()): 
        for winner_odd in response[time_type]: 
            winner_bet_value = winner_odd["value"].split()

            if winner_bet_value[0] == "Home": 
                bet_team = home_team
            elif winner_bet_value[0] == "Away": 
                bet_team = away_team 
            else: 
                # if the type of bet is moneyline, account for draw. Otherwise, go the next bets 
                if bet_type == "handicap": continue
                bet_team = winner_bet_value[0] 

            try: 
                american_odd = convert_american_odd(float(winner_odd["odd"]))
            except ZeroDivisionError: 
                # Zero division (the bet has odd 1) indicates that the european odd can't be converted to american odd
                continue

            # stucture of the moneyline (or handicap) bet 
            winner_bet = {
                "match": f"{home_team} vs {away_team}",
                "time_type": time_type, # indicate if  the handicap is for half_time or full_time
                "bet_object": bet_obj,
                "bet_team": bet_team, 
                "odd": american_odd, # convert the obtained decimal odd and covert them to American odd 
            }
            # if the type of bet is handicap, add the handicap coverage 
            if bet_type == "handicap": 
                handicap_cover = float(winner_bet_value[1])
                winner_bet["handicap_cover"] = handicap_cover

            # add the bet of the list 
            obj_winner_bet_list.append(winner_bet)   

    #print(json.dumps(obj_winner_bet_list, indent=4))
    return obj_winner_bet_list


def get_winner_bets(bet_type: str, match_id: int, home_team: str, away_team: str) -> list : 
    """ Get moneyline or handicap bets for goals, corners and cards  """

    winner_bet_list = []
    for bet_object in ["Goals", "Corners", "Cards"]: 
        winner_bet_list.extend(
            get_obj_winner_bets(bet_object, bet_type, match_id, home_team, away_team)
        )
    return winner_bet_list


def get_obj_total_bets(bet_obj: str, match_id: int, home_team: str, away_team: str) -> list: 
    """
    Get the total goals bets for match with given ID.

    bet_obj: "Goals" or "Corners" or "Cards"
    """

    if bet_obj == "Goals": 
        response = get_goals_bets("total_goals", match_id)
    else: 
        response = get_other_object_bets(bet_obj, "total_goals", match_id)

    total_objs_bet_list = [] 
    for time_type in list(response.keys()): 
        for total_objs_odd in response[time_type]: 
            total_objs_bet_value = total_objs_odd["value"].split()
            under_or_over_value = total_objs_bet_value[0] # if the total objects are under or over
            target_num_objs = float(total_objs_bet_value[1]) # the target number of objects 

            try: 
                american_odd = convert_american_odd(float(total_objs_odd["odd"]))
            except ZeroDivisionError: 
                continue

            total_objs_bet_list.append({
                "match": f"{home_team} vs {away_team}", 
                "time_type": time_type,
                "bet_object": bet_obj,
                "under_or_over": under_or_over_value, 
                "num_objects": target_num_objs, 
                "odd": american_odd,
            })

    #print(json.dumps(total_objs_bet_list, indent=4))
    return total_objs_bet_list


def get_total_bets(match_id: int, home_team: str, away_team: str) -> list: 
    """ Get total bets for goals, corners, and cards """

    total_objs_bet_list = []
    for bet_object in ["Goals", "Corners", "Cards"]: 
        total_objs_bet_list.extend(get_obj_total_bets(bet_object, match_id, home_team, away_team))
    return total_objs_bet_list


if __name__ == "__main__": 

    # used for testing the script 
    leagues = {"ucl": 2, "epl": 39, "lal": 140, "bun": 78}
    from_date = get_date_str(date.today())
    weekday = date.today().weekday()

    if weekday >= 0 and weekday <= 3: # monday to thursday
        to_date = get_date_str(date.today() + timedelta(days=(3 - weekday)))
    else: # friday to sunday
        to_date = get_date_str(date.today() + timedelta(days=(6 - weekday)))

    # get the matches from all the league 
    for league_name in list(leagues.keys()): 
        upcoming_ucl_matches = get_not_started_matches(leagues[league_name], from_date, to_date)
        
        # loop through the matches
        for upcoming_ucl_match in upcoming_ucl_matches: 
            match_id = upcoming_ucl_match["match_id"]
            home_team = upcoming_ucl_match["home_team"]
            away_team = upcoming_ucl_match["away_team"]

            # 3 types of bet (full-time and half-time) of the match this turn 
            response = {
                "fixture": upcoming_ucl_match, 
                "moneyline_bets": get_winner_bets("moneyline", match_id, home_team, away_team), 
                "handicap_bets": get_winner_bets("handicap", match_id, home_team, away_team), 
                "total_goals_bets": get_total_bets(match_id, home_team, away_team),
            }
            print(json.dumps(response, indent=4))