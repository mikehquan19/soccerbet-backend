# Soccerbet's Backend & API (Coming soon)
## Introduction
This is the backend of of the Soccerbet, the app which:
- provides data about soccer teams, rankings in the leagues, upcoming fixtures, available bets on those fixtures.
- simulates betting between users on the available bets 

The API will be used to provide the data to the front-end (coming soon)

At the beginning of every week, it will fetch from [API-Football](https://www.api-football.com/) all upcoming fixtures from 3 different leagues for the week, and available bets of each fixture. Every hour, it will check if any match was finished and settled all of the bets from that match. 

The API is now functional but the following features are still in progress: 
- Unit test on how the bets are settled
- Periodic execution of the matches and bets uploading, updating, and bet settling
- Authentication

## Tech Stack 
- [Django](https://www.djangoproject.com/) ([DRF](https://www.django-rest-framework.org/)) are used to build the API 
- Data was fetched from [API-Football](https://www.api-football.com/)

## Sample data for API
```
SAMPLE DATA FOR MONEYLINE BET 
{
    "bet_info": {
        "id": 169,
        "time_type": "full_time",
        "bet_team": "Atletico Madrid",
        "odd": "-278.00",
        "status": "Unsettled",
        "settled_date": null,
        "match": 1208575
    },
    "bet_amount": 100,
    "user": 1
}


SAMPLE DATA FOR HANDICAP BET 
[  
    {
        "bet_info": {
            "id": 000,
            "time_type": "full_time",
            "bet_team": "Crystal Palace",
            "handicap_cover": "-1.00",
            "odd": "-175.00",
            "status": "Unsettled",
            "settled_date": null,
            "match": 1234567
        },
        "bet_amount": "100.00",
        "user": 1
    }, 
    {
        "bet_info": {
            "id": 001,
            "time_type": "full_time",
            "bet_team": "Crystal Palace",
            "handicap_cover": "-1.00",
            "odd": "-175.00",
            "status": "Unsettled",
            "settled_date": null,
            "match": 1234567
        },
        "bet_amount": "100.00",
        "user": 1
    }
]


SAMPLE DATA FOR TOTAL GOALS BET 
{
    "bet_info": {
        "id": 002,
        "time_type": "full_time",
        "under_or_over": "Under",
        "target_num_goals": 4,
        "odd": "-500.00",
        "status": "Unsettled",
        "settled_date": null,
        "match": 1234567
    }, 
    "bet_amount": 100, 
    "user": 1
}
```