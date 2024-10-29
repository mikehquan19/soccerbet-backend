import requests
import json
import os

# the API key
API_KEY = os.environ.get("API_KEY") # API-KEY OBTAINED FROM SUBSCRIBING TO API-FOOTBALL
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
    

# call the api to get the data about the bet with the given type 
# return the json 
def get_api_data(bet_type: str, match_id: int) -> dict: 
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

    json_response = {"full time": None, "half time": None}
    # load them into JSON object, which is iterable 
    if len(json.loads(full_res.text)["response"]) > 0: 
        json_response["full time"] = json.loads(full_res.text)["response"][0]["bookmakers"][0]["bets"][0]["values"]
    if len(json.loads(half_res.text)["response"]) > 0: 
        json_response["half time"] = json.loads(half_res.text)["response"][0]["bookmakers"][0]["bets"][0]["values"]

    # print(json.dumps(json_response, indent=4)) # print only for testing 
    return json_response

 
# Football API doesn't originate from America, therefore they use a different system of odd 
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
    # print(json.dumps(json.loads(response.text), indent=4))

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
    # print(json.dumps(json_response, indent=4)) # print only for testing

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
    # print(json.dumps(json_response, indent=4)) # print only for testing

    # process the data 
    match_score_list = []
    for fixture in json_response: 
        # scores of the fixture 
        halftime_score = fixture["score"]["halftime"]
        fulltime_score = fixture["score"]["fulltime"]
        penalty = fixture["score"]["penalty"]

        # add the score to the the list of scores 
        match_score_list.append({
            # the id of the game 
            "match_id": fixture["fixture"]["id"], 
            # the game in the format "{home team's goals} - {away team"s goals}"
            "halftime": f"{halftime_score["home"]} - {halftime_score["away"]}", 
            "fulltime": f"{fulltime_score["home"]} - {fulltime_score["away"]}",
            "penalty": f"{penalty["home"]} - {penalty["away"]}",
        })
    # print(json.dumps(match_score_list, indent=4))
    return match_score_list


# get the standing of the league (should be every day)
def get_league_standings(league_id: int) -> dict: 
    standing_endpt = f"{base_url}/standings?league={league_id}&season=2024"
    response = requests.get(standing_endpt, headers=headers, data=payload)

    json_response = []
    if len(json.loads(response.text)["response"]) > 0: 
        json_response = json.loads(response.text)["response"][0]["league"]["standings"][0]
    # print(json.dumps(json_response, indent=4)) # print only for testing

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
# bet_type is "moneyline" or "handicap"
# structure of regular bet (match, time_type, bet_team, odd)
# structure of handicap bet (match, time_type, bet_team, odd, handicap_cover)
def get_moneyline_bets(bet_type: str, match_id: int, home_team: str, away_team: str) -> list: 
    # get RAW data about the bets from Football API 
    json_response = get_api_data(bet_type, match_id=match_id)

    # process the raw data (the pain in the neck)
    moneyline_bet_list = []
    for time_type in list(json_response): 
        if json_response[time_type] is not None: 
            for moneyline_odd in json_response[time_type]: 
                moneyline_bet_value = moneyline_odd["value"].split()
                if moneyline_bet_value[0] == "Home": 
                    bet_team = home_team
                elif moneyline_bet_value[0] == "Away": 
                    bet_team = away_team 
                elif moneyline_bet_value[0] == "Draw": 
                    # if the type of bet is moneyline, account for draw. 
                    if bet_type == "handicap": 
                        continue # Otherwise, go the next bets 
                    bet_team = moneyline_bet_value[0] 

                # stucture of the moneyline (or handicap) bet 
                moneyline_bet = {
                    "match": f"{home_team} vs {away_team}",
                    "time_type": time_type, # indicate if  the handicap is for half_time or full_time
                    "bet_team": bet_team, 
                    # convert the obtained decimal odd and covert them to American odd 
                    "odd": convert_american_odd(float(moneyline_odd["odd"])), 
                }
                # if the type of moneyline is handicap, add the handicap coverage 
                if bet_type == "handicap": 
                    handicap_cover = float(moneyline_bet_value[1])
                    moneyline_bet["handicap_cover"] = handicap_cover
                # add the bet of the list 
                moneyline_bet_list.append(moneyline_bet)    
    return moneyline_bet_list


# get the total goals bets for match with given id 
# structure of the total-goals bets (match, time_type, over or under, num goals, odd)
def get_total_goals_bets(match_id: int, home_team: str, away_team: str) -> list: 
    # get raw data from the API 
    json_response = get_api_data("total_goals", match_id=match_id)

    # process the data to be feedable to the database 
    total_goals_bet_list = [] 
    for time_type in list(json_response.keys()): 
        if json_response[time_type] is not None: 
            for total_goals_odd in json_response[time_type]: 
                # if the total goals are under or over, and the target num of goals 
                total_goals_bet_value = total_goals_odd["value"].split()
                under_or_over = total_goals_bet_value[0] 
                num_goals = float(total_goals_bet_value[1])

                # add the odd to the list 
                total_goals_bet_list.append({
                    "match": f"{home_team} vs {away_team}", 
                    "time_type": time_type,
                    "under_or_over": under_or_over, 
                    "num_goals": num_goals, 
                    # convert the obtained decimal odd and covert them to American odd 
                    "odd": convert_american_odd(float(total_goals_odd["odd"])),
                })
    return total_goals_bet_list


def main(): 
    # this snippet of code is used for testing the script 
    leagues = {"ucl": 2, "epl": 39, "lal": 140}
    from_date = "2024-10-14"
    to_date = "2024-10-21"

    # get the standing of the given league 
    get_league_standings(leagues["lal"])

    # get the match scores all the matches of given league 
    print(json.dumps(get_match_score(leagues["epl"], arg_date="2024-09-29"),indent=4))

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
                "total_goals_bets": get_total_goals_bets(match_id, home_team, away_team),
            }
            print(json.dumps(response, indent=4))

if __name__ == "__main__": 
    main()