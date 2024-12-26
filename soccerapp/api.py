import requests
import json
import environ

env = environ.Env()
# reading .env file 
environ.Env.read_env()

# the API key
API_KEY = env("API_KEY") # API-KEY OBTAINED FROM SUBSCRIBING TO API-FOOTBALL
base_url = "https://v3.football.api-sports.io"
payload = {}
headers = {
    'x-rapidapi-key': API_KEY, 
    'x-rapidapi-host': 'v3.football.api-sports.io'
}

# this is used to get id of the bets
def get_bet_ids(): 
    response = requests.get(f"{base_url}/odds/bets/", headers=headers, data=payload)
    print(json.dumps(json.loads(response.text), indent=4))
    

# call the api to get the data about the bet for goals with the given type 
# return the json 
def get_goals_api_data(bet_type: str, match_id: int) -> dict: 
    if bet_type == "moneyline": 
        fulltime_bet_id, halftime_bet_id = 1, 13 # id of the full-time and half-time moneyline bet 
    elif bet_type == "handicap": 
        fulltime_bet_id, halftime_bet_id = 9, 18 # id of the full-time and half-time handicap bet 
    elif bet_type == "total_goals": 
        fulltime_bet_id, halftime_bet_id = 5, 6 # id of the full-time and half-time total goals bet

    # the endpoint of the URL 
    full_endpt = f"odds?fixture={match_id}&season=2024&bookmaker=1&bet={fulltime_bet_id}"
    half_endpt = f"odds?fixture={match_id}&season=2024&bookmaker=1&bet={halftime_bet_id}"
    
    # the response full-time and half-time 
    full_res = requests.get(f"{base_url}/{full_endpt}", headers=headers, data=payload)
    half_res = requests.get(f"{base_url}/{half_endpt}", headers=headers, data=payload)

    json_response = {"full time": [], "half time": []}
    # load them into JSON object, which is iterable 
    if len(json.loads(full_res.text)["response"]) > 0: 
        json_response["full time"] = json.loads(full_res.text)["response"][0]["bookmakers"][0]["bets"][0]["values"]
    if len(json.loads(half_res.text)["response"]) > 0: 
        json_response["half time"] = json.loads(half_res.text)["response"][0]["bookmakers"][0]["bets"][0]["values"]

    # print(json.dumps(json_response, indent=4)) # print only for testing 
    return json_response


# call the api to get the data about the bet for other types (corners, cards) with the given type 
# return the json 
def get_other_api_data(bet_object: str, bet_type: str, match_id: int) -> dict: 
    # there are currently no moneyline bets for cards available 
    if bet_object == "Cards" and bet_type == "moneyline": return {"full time": []}

    if bet_type == "moneyline": bet_id = 55 # moneyline bet is only offered for corners 
    elif bet_type == "handicap": 
        bet_id = 56 if bet_object == "Corners" else 79 # 56, 79 are ids of corner and cards handicap bets
    elif bet_type == "total_goals": 
        bet_id = 45 if bet_object == "Corners" else 80 # 45, 80 are ids of corner and cards total bets

    # endpoint of the URL
    bookmaker = 8 if bet_object == "Cards" else 2 # different bookmakers might offer different types of objects
    endpoint = f"odds?fixture={match_id}&season=2024&bookmaker={bookmaker}&bet={bet_id}"
    response = requests.get(f"{base_url}/{endpoint}", headers=headers, data=payload)

    json_response = {"full time": []}
    if len(json.loads(response.text)["response"]) > 0: 
        json_response["full time"] = json.loads(response.text)["response"][0]["bookmakers"][0]["bets"][0]["values"]
        # limit the number of bets if there are too many (to not overload local database)
        if len(json_response["full time"]) > 8: 
            num_bets = len(json_response["full time"])
            json_response["full time"] = json_response["full time"][(num_bets - 8):num_bets]
            
    # print(json.dumps(json_response, indent=4)) # print for testing 
    return json_response 


# Football API originates from Europe, so they use a different system of odd 
# convert the obtained decimal odd and covert them to American odd 
def convert_american_odd(decimal_odd: float) -> int: 
    if decimal_odd >= 2.00: 
        american_odd = round((decimal_odd - 1) * 100)
    elif decimal_odd < 2.00: 
        american_odd = round(-100 / (decimal_odd - 1))
    return american_odd


# get the info about the team this season 
def get_teams(league_id: int): 
    # call the api to get raw data 
    response = requests.get(f"{base_url}/teams?league={league_id}&season=2024", headers=headers, data=payload)
    json_response = json.loads(response.text)["response"]

    # process the raw data 
    this_league_team_list = []
    for team in json_response: 
        # add the team with the given info to the list of teams 
        this_league_team_list.append({
            "name": team["team"]["name"],
            "logo": team["team"]["logo"], 
            "founded_year": team["team"]["founded"], 
            "home_stadium": team["venue"]["name"], 
            "stadium_image": team["venue"]["image"], 
            "description": f"This is {team["team"]["name"]}",

        })
    return this_league_team_list


# get the upcoming matches, should be called every week 
def get_not_started_matches(league_id: int, arg_from_date: str, arg_to_date: str) -> list:
    # call the API to get the raw data  
    match_endpt = f"fixtures?league={league_id}&season=2024&from={arg_from_date}&to={arg_to_date}"
    response = requests.get(f"{base_url}/{match_endpt}", headers=headers, data=payload)
    json_response = json.loads(response.text)["response"]

    # process the raw data 
    upcoming_match_list = []
    for fixture in json_response:
        # add the upcoming match with given information to the list 
        upcoming_match_list.append({
            "match_id": fixture["fixture"]["id"],
            "date": fixture["fixture"]["date"], 
            "home_team": fixture["teams"]["home"]["name"],
            "home_team_logo": fixture["teams"]["home"]["logo"],
            "away_team": fixture["teams"]["away"]["name"],
            "away_team_logo": fixture["teams"]["away"]["logo"], 
        })
    return upcoming_match_list


# get the scores of all the matches of the given league on the given date 
def get_match_score(league_id: int, arg_date: str) -> list:
    # call the API to get the data about the fixtures that are finished
    finished_endpt = f"fixtures?date={arg_date}&league={league_id}&season=2024&status=FT-AET-PEN"
    response = requests.get(f"{base_url}/{finished_endpt}", headers=headers, data=payload)
    json_response = json.loads(response.text)["response"]

    # process the data 
    match_result_list = []
    for fixture in json_response:
        # scores of the fixture 
        halftime_score = fixture["score"]["halftime"]
        fulltime_score = fixture["score"]["fulltime"]
        penalty = fixture["score"]["penalty"]

        # add the score to the the list of scores 
        match_result = {
            # the id of the game 
            "match_id": fixture["fixture"]["id"], 
            # the game in the format "{home team's goals} - {away team"s goals}"
            "halftime": f"{halftime_score["home"]}-{halftime_score["away"]}", 
            "fulltime": f"{fulltime_score["home"]}-{fulltime_score["away"]}",
            "penalty": f"{penalty["home"]}-{penalty["away"]}",
        }

        # get other statistics of the matches of the given league on the given date 
        response = requests.get(f"{base_url}/fixtures/statistics?fixture={fixture["fixture"]["id"]}", headers=headers, data=payload)
        json_response = json.loads(response.text)["response"]
        home_stat = json_response[0]["statistics"]
        away_stat = json_response[1]["statistics"]
        # concatenate the other statistics to the dictionary 
        match_result.update({
            "possession": f"{home_stat[9]["value"]}-{away_stat[9]["value"]}",
            "total_shots": f"{home_stat[2]["value"]}-{away_stat[2]["value"]}",
            "corners": f"{home_stat[7]["value"]}-{away_stat[7]["value"]}",
            "cards": f"{home_stat[10]["value"]}-{away_stat[10]["value"]}"
        })
        match_result_list.append(match_result)

    # print(json.dumps(match_result_list, indent=4))
    return match_result_list
 

# get the standing of the league (should be every day)
def get_league_standings(league_id: int) -> dict: 
    standing_endpt = f"{base_url}/standings?league={league_id}&season=2024"
    response = requests.get(standing_endpt, headers=headers, data=payload)

    json_response = []
    if len(json.loads(response.text)["response"]) > 0: 
        json_response = json.loads(response.text)["response"][0]["league"]["standings"][0]

    # process the raw data 
    standing_list = []
    for standing in json_response: 
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
    # print(json.dumps(standing_list, indent=4)) # printing for testing 
    return standing_list
        
                
# get the moneylineo or handicap bets for the match (depending on user)
# bet_type: "moneyline" or "handicap"
# regular moneyline bet: (match, time_type, bet_team, odd)
# handicap bet: (match, time_type, bet_team, odd, handicap_cover)
def get_obj_moneyline_bets(bet_obj: str, bet_type: str, match_id: int, home_team: str, away_team: str) -> list: 
    # get RAW data about the bets from Football API 
    json_response = get_goals_api_data(bet_type, match_id) if bet_obj == "Goals" else get_other_api_data(bet_obj, bet_type, match_id)

    # process the raw data (the pain in the neck)
    obj_moneyline_bet_list = []
    for time_type in list(json_response.keys()): 
        for moneyline_odd in json_response[time_type]: 
            moneyline_bet_value = moneyline_odd["value"].split()
            if moneyline_bet_value[0] == "Home": 
                bet_team = home_team
            elif moneyline_bet_value[0] == "Away": 
                bet_team = away_team 
            else: 
                # if the type of bet is moneyline, account for draw. Otherwise, go the next bets 
                if bet_type == "handicap": continue
                bet_team = moneyline_bet_value[0] 

            try: 
                american_odd = convert_american_odd(float(moneyline_odd["odd"]))
            except ZeroDivisionError: 
                continue
            # stucture of the moneyline (or handicap) bet 
            moneyline_bet = {
                "match": f"{home_team} vs {away_team}",
                "time_type": time_type, # indicate if  the handicap is for half_time or full_time
                "bet_object": bet_obj,
                "bet_team": bet_team, 
                "odd": american_odd, # convert the obtained decimal odd and covert them to American odd 
            }
            # if the type of moneyline is handicap, add the handicap coverage 
            if bet_type == "handicap": 
                handicap_cover = float(moneyline_bet_value[1])
                moneyline_bet["handicap_cover"] = handicap_cover
            # add the bet of the list 
            obj_moneyline_bet_list.append(moneyline_bet)    
    return obj_moneyline_bet_list


def get_moneyline_bets(bet_type: str, match_id: int, home_team: str, away_team: str) -> list : 
    moneyline_bet_list = []
    for bet_object in ["Goals", "Corners", "Cards"]: 
        moneyline_bet_list.extend(get_obj_moneyline_bets(bet_object, bet_type, match_id, home_team, away_team))
    return moneyline_bet_list


# get the total goals bets for match with given id 
# structure of the total-goals bets (match, time_type, over or under, num goals, odd)
def get_obj_total_bets(bet_obj: str, match_id: int, home_team: str, away_team: str) -> list: 
    # get raw data from the API 
    json_response = get_goals_api_data("total_goals", match_id) if bet_obj == "Goals" else get_other_api_data(bet_obj, "total_goals", match_id)

    # process the data to be feedable to the database 
    type_total_objs_bet_list = [] 
    for time_type in list(json_response.keys()): 
        for total_goals_odd in json_response[time_type]: 
            # if the total objects are under or over, and the target num of objects 
            total_goals_bet_value = total_goals_odd["value"].split()
            under_or_over = total_goals_bet_value[0] 
            num_objects = float(total_goals_bet_value[1])

            # in case the bet has odd 1, skip it as it's invalid and non-convertible to american
            try: 
                american_odd = convert_american_odd(float(total_goals_odd["odd"]))
            except ZeroDivisionError: 
                continue
            type_total_objs_bet_list.append({
                "match": f"{home_team} vs {away_team}", 
                "time_type": time_type,
                "bet_object": bet_obj,
                "under_or_over": under_or_over, 
                "num_objects": num_objects, 
                # convert the obtained decimal odd and covert them to American odd 
                "odd": american_odd,
            })
    return type_total_objs_bet_list


def get_total_bets(match_id: int, home_team: str, away_team: str) -> list: 
    total_objs_bet_list = []
    for bet_object in ["Goals", "Corners", "Cards"]: 
        total_objs_bet_list.extend(get_obj_total_bets(bet_object, match_id, home_team, away_team))
    return total_objs_bet_list


def main(): 
    # this snippet of code is used for testing the script 
    leagues = {"ucl": 2, "epl": 39, "lal": 140}
    from_date = "2024-12-18"
    to_date = "2024-12-25"

    # get the standing of the given league 
    print(json.dumps(get_league_standings(leagues["lal"]), indent=4))

    # get the match scores all the matches of given league 
    print(json.dumps(get_match_score(leagues["epl"], arg_date="2024-09-29"), indent=4))

    # get the teams of the given leauge 
    print(json.dumps(get_teams(leagues["lal"]), indent=4))
    
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
                "moneyline_bets": get_moneyline_bets("moneyline", match_id, home_team, away_team), 
                "handicap_bets": get_moneyline_bets("handicap", match_id, home_team, away_team), 
                "total_goals_bets": get_total_bets(match_id, home_team, away_team),
            }
            print(json.dumps(response, indent=4))

if __name__ == "__main__": 
    main()