import requests
import json
import environ
from datetime import date, timedelta

env = environ.Env()
environ.Env.read_env() # reading .env file 


def get_api_response(endpoint: str): 
    base_url = "https://v3.football.api-sports.io"
    headers = {
        'x-rapidapi-key': env("API_KEY"), # API-KEY OBTAINED FROM SUBSCRIPTION TO API-FOOTBALL
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    response = requests.get(f"{base_url}/{endpoint}", headers=headers, data={})
    response = json.loads(response.text)["response"]
    return response


# this is used to get id of the bets
def get_bet_ids(): 
    return get_api_response("/odds/bets/")
    

# call the api to get the data about the bet for goals with the given type 
def get_goals_bets(bet_type: str, match_id: int) -> dict: 
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

    response = {"full time": [], "half time": []}
    # load them into JSON object, which is iterable 
    if len(full_response) > 0: 
        response["full time"] = full_response[0]["bookmakers"][0]["bets"][0]["values"]
    if len(half_response) > 0: 
        response["half time"] = half_response[0]["bookmakers"][0]["bets"][0]["values"]

    # print(json.dumps(response, indent=4)) # print only for testing 
    return response


# call the api to get the data about the bet for other types (corners, cards) with the given type  
def get_other_object_bets(bet_object: str, bet_type: str, match_id: int) -> dict: 
    # there are currently no moneyline bets for cards available 
    if bet_object == "Cards" and bet_type == "moneyline": return {"full time": []}

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

    response = {"full time": []}
    if len(json_response) > 0: 
        response["full time"] = json_response[0]["bookmakers"][0]["bets"][0]["values"]
        # limit the number of bets if there are too many (to not overload database)
        if len(response["full time"]) > 10: 
            num_bets = len(response["full time"])
            response["full time"] = response["full time"][(num_bets - 10):num_bets]
            
    # print(json.dumps(response, indent=4)) # print for testing 
    return response 


"""
    Football-API is from France, so they use a different system of odd 
    convert the obtained decimal odd and covert them to American odd
""" 
def convert_american_odd(decimal_odd: float) -> int: 
    if decimal_odd >= 2.00: 
        american_odd = round((decimal_odd - 1) * 100)
    elif decimal_odd < 2.00: 
        american_odd = round(-100 / (decimal_odd - 1))
    return american_odd


# get the info about the team this season 
def get_teams(league_id: int): 
    # call the api to get raw data
    response = get_api_response(f"teams?league={league_id}&season=2024")

    # process the raw data 
    league_team_list = []
    for team in response: 
        # add the team with the given info to the list of teams 
        league_team_list.append({
            "name": team["team"]["name"],
            "logo": team["team"]["logo"], 
            "founded_year": team["team"]["founded"], 
            "home_stadium": team["venue"]["name"], 
            "stadium_image": team["venue"]["image"], 
            "description": f"This is {team["team"]["name"]}",
        })
    return league_team_list


# get the upcoming matches, should be called every week 
def get_not_started_matches(league_id: int, from_date: str, to_date: str) -> list:
    # param is the nedpoint to call matches
    response = get_api_response(f"fixtures?league={league_id}&season=2024&from={from_date}&to={to_date}")

    # process the raw data 
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
    return upcoming_match_list


# get the scores of all the matches of the given league on the given date 
def get_match_score(league_id: int, arg_date: str) -> list:
    finished_endpoint = f"fixtures?date={arg_date}&league={league_id}&season=2024&status=FT-AET-PEN"
    response = get_api_response(finished_endpoint)

    # process the data 
    match_result_list = []
    for fixture in response:
        # scores of the fixture 
        halftime_score = fixture["score"]["halftime"]
        fulltime_score = fixture["score"]["fulltime"]
        penalty = fixture["score"]["penalty"]

        # add the score to the the list of scores 
        match_result = {
            "match_id": fixture["fixture"]["id"], # the id of the game 

            # the game in the format "{home team's goals} - {away team"s goals}"
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
    standing_endpt = f"standings?league={league_id}&season=2024"
    json_response = get_api_response(standing_endpt)
    response = []
    if len(json_response) > 0: 
        response = json_response[0]["league"]["standings"][0]

    # process the raw data 
    standing_list = []
    for standing in response: 
        """
            the standing includes the rank, team, points, num_matches, wins, draws, and loses
            add the standing to the list 
        """
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
        

"""         
    get the moneyline or handicap bets for the match (depending on user)
    bet_type: "moneyline" or "handicap", bet_obj: "Goals" or "Corners" or "Cards"
"""    
def get_obj_winner_bets(bet_obj: str, bet_type: str, match_id: int, home_team: str, away_team: str) -> list: 
    if bet_obj == "Goals": 
        response = get_goals_bets(bet_type, match_id)
    else: 
        response = get_other_object_bets(bet_obj, bet_type, match_id)

    # process the raw data 
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
    return obj_winner_bet_list



# get moneyline of handicap bets for corners and cards 
def get_winner_bets(bet_type: str, match_id: int, home_team: str, away_team: str) -> list : 
    winner_bet_list = []
    for bet_object in ["Goals", "Corners", "Cards"]: 
        winner_bet_list.extend(get_obj_winner_bets(bet_object, bet_type, match_id, home_team, away_team))
    return winner_bet_list


"""
    get the total goals bets for match with given id 
    bet_obj: "Goals" or "Corners" or "Cards"
"""
def get_obj_total_bets(bet_obj: str, match_id: int, home_team: str, away_team: str) -> list: 
    if bet_obj == "Goals": 
        response = get_goals_bets("total_goals", match_id)
    else: 
        response = get_other_object_bets(bet_obj, "total_goals", match_id)

    total_objs_bet_list = [] 
    for time_type in list(response.keys()): 
        for total_objs_odd in response[time_type]: 
            # if the total objects are under or over, and the target num of objects 
            total_objs_bet_value = total_objs_odd["value"].split()
            under_or_over = total_objs_bet_value[0] 
            target_num_objs = float(total_objs_bet_value[1])

            try: 
                # in case the bet has odd 1, skip it as it's invalid and non-convertible to american
                american_odd = convert_american_odd(float(total_objs_odd["odd"]))
            except ZeroDivisionError: 
                continue

            total_objs_bet_list.append({
                "match": f"{home_team} vs {away_team}", 
                "time_type": time_type,
                "bet_object": bet_obj,
                "under_or_over": under_or_over, 
                "num_objects": target_num_objs, 
                "odd": american_odd, # convert the obtained decimal odd and covert them to American odd 
            })
    return total_objs_bet_list


def get_total_bets(match_id: int, home_team: str, away_team: str) -> list: 
    total_objs_bet_list = []
    for bet_object in ["Goals", "Corners", "Cards"]: 
        total_objs_bet_list.extend(get_obj_total_bets(bet_object, match_id, home_team, away_team))
    return total_objs_bet_list


def main(): 
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

    # this snippet of code is used for testing the script 
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

if __name__ == "__main__": 
    main()