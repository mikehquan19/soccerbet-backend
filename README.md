# SoccerBet Backend & API 

## About

### Introduction
The backend of **SoccerBet**, the app that
- serves info about upcoming **soccer matches** of different leagues or tournaments, current league **standings**, **stats** of finished matches, and **bets** for each match. 

- simulates the platform where users can **bet on games**, experience winning or losing, and **communicate** with each other on any team about anything through comment sections. 

Leagues and tournaments that it currently covers: 
- **Champions League (UCL)**
- **Premiere League (EPL)**
- **La Liga (LAL)**
- **Bundesliga (BUN)**

Bigger tournaments such as **FIFA World Cup**, **UEFA EURO**, or **Copa America** are seasonal and will be covered when the time comes. More leagues can also be covered in the future.

The API will be used to provide the data to the **SoccerBet's front-end** (coming soon).

### Design
The app gets the data from subscription to [API-Football](https://www.api-football.com/), although web scraping is also a possibility, more affordable, and could be implemented in the future. 

The app will do the following tasks **periodically** to maintain the consistency of the data: 
- **Twice every week**, get upcoming games and available bet info of various types (regular moneyline, handicap, total objects) of each game from Football API for the half the week.

- **Every hour**, check if there's any new game that is finished to update the stats for those games (scores, possession, corners, cards, etc), settle all the bets of that game that were placed by the users, and delete all of their bet info that were not placed by any users (empty).

- **Every 12 hours**, update the standings of each league

- **Every day**, delete all the finished games and associated settled bets that have been in the database for 2 weeks.

**Note:** The difference between **bet info** and **bet** is that bet info contains all the info about game's name, odd, settled_date, while bet is basically bet info tagged with the **user**, **amount** the user bet on, and **created date**.

It also implements **JWT Authentication** through the popular package [django-simple-jwt](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/) so that user's personal info and info about which bet they have placed will be protected. 

### Tech Stack 
- [Django](https://www.djangoproject.com/) ([DRF](https://www.django-rest-framework.org/)) to build the API 
- [API-Football](https://www.api-football.com/) to fetch the data about games
- [Celery (Celery Beat)](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html) to upload and update matches and bets periodically and concurrently in the background
- [PostgreSQL](https://www.postgresql.org/) for database


## How to run 

The app will be deployed soon, below is the guide to run the app locally:

#### 1/ Prerequisites

Before getting started, make sure that you have a **postgreSQL** server up and running. If not, please visit [this website](https://www.postgresql.org/download/).

If you don't have ```redis``` or ```rabbitmq```, please visit [this website](https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#first-steps) 

If you don't have ```pip``` installed in your machine, please visit [this website](https://pip.pypa.io/en/stable/installation/).

Also make sure that you have **django, DRF, django-simple-jwt, & Celery** installed. If not, simply run the following command: 
```
pip install django djangorestframework django-simple-jwt django-celery-beat
```


#### 2/ Set up the server 
Then clone the project to local machine and set it up in the virtual environment: 
```
https://github.com/mikehquan19/soccerbet-backend.git

cd soccerbet # enter the main directory
```

Create the ```.env``` files in the both directory ```soccerapp``` and ```soccerbet``` based on ```.env.example```. 
- ```.env``` in ```soccerbet``` contains the environment variables that connect your **Postgresql** server to the **Django** app. 
- ```.env``` in ```soccerapp``` stores the the api key that you will get from subscription to **Football-API**


#### 3/ Migrate the database and run the server 

Run the following command within the outer ```soccerbet``` dir to migrate models to the database and create superuser to access the admin page 
```
python manage.py makemigrations 
python manage.py migrate 
python manage.py createsuperuser
```

Then create your own username and password. By now, you should be ready to run the server 
```
python manage.py runserver
```

#### 4/ Set up the Celery service and upload initital data to the database

Now, we will set up the celery beat server so that it can run the uploading and updating tasks periodically. 

Login the admin page with the username and password you created, add all of the below tasks with given **crontab schedule** to ```periodic tasks``` table: 

```
soccerapp.tasks.delete_past_betinfos_and_matches: 0 0 * * * 
soccerapp.tasks.update_scores_and_settle: 0 * * * *
soccerapp.tasks.upload_matches_and_bets: 0 0 * * 1.5
soccerapp.tasks.update_teams_rankings: 0 0,12 * * *

```

Then, run the following command to get **Celery** up and running: 
```
 celery -A soccerbet worker --loglevel=info -c 8 
 celery -A soccerbet beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

**Congrats! you have got the API server up and running**. However, for now your database is empty as you have to wait for the server to upload the data when the time comes for it to run the tasks. That would be no fun, so you can run the tasks manually to upload the matches and bets now. 

Open the django shell and run the task manually inside the shell:

```
cd soccerapp # enter directory soccerapp
python manage.py shell 

# in the shell
from soccerapp.tasks import upload_matches_and_bets 
upload_matches_and_bets()
```

This will upload all the matches and bets up to the next uploading cycle, so you don't have to worry about conflicting data.

**Now you have the API server with some substantial data to play around**. 


## Sample data served by the API 
Bellow is the some of the common requests that are made in the app

#### SAMPLE DATA FOR USER'S PERSONAL DETAILS
```/soccerapp/detail```
```
{
    "username": "mike_username", 
    "email": "mike_user@gmail.com", 
    "password": "mike_password", 
    "first_name": "Mike",
    "last_name": "Quan"
}
```


#### SAMPLE DATA FOR REGULAR MONEYLINE BET 
```/soccerapp/moneyline_bets```
```
{
    "bet_info": {
        "time_type": "full_time",
        "bet_team": "Atletico Madrid",
        "bet_object": "Goals",
        "odd": "120.00",
        "status": "Unsettled",
        "settled_date": null,
        "match": 1000000, 
        "match_name": "Atletico Madrid vs Barcelona"
    },
    "bet_amount": 100,
    "created_date": "01/01/2000"
    "user": 1
}
```

#### SAMPLE DATA FOR HANDICAP BET 
```/soccerapp/handicap_bets```
```
{
    "bet_info": {
        "time_type": "full_time",
        "bet_team": "Crystal Palace",
        "bet_object": "Corners"
        "handicap_cover": "-1.00",
        "odd": "-175.00",
        "status": "Unsettled",
        "settled_date": null,
        "match": 1000001, 
        "match_name": "Manchester United vs Crystal Palace"
    },
    "bet_amount": "175.00",
    "created_date": "02/02/2000",
    "user": 2
}
```

#### SAMPLE DATA FOR TOTAL OBJECTS BET 
```/soccerapp/total_bets```
```
{
    "bet_info": {
        "time_type": "full_time",
        "under_or_over": "Under",
        "bet_object": "Corners"
        "target_num_objects": 4,
        "odd": "140.00",
        "status": "Unsettled",
        "settled_date": null,
        "match": 1000002, 
        "match_name": "Real Madrid vs Manchester City"
    }, 
    "bet_amount": 100,
    "created_date": "03/03/2000",
    "user": 3
}
```

**Obviously, there are many other requests that can be explored.** 


## Resources

Below are some of the valuable sources for learning about ***Celery, and JWT authentication*** using django that I recommend: 
- For JWT: [Implementing JWT Authentication and User Profile with Django Rest API Part 3](https://dev.to/ki3ani/implementing-jwt-authentication-and-user-profile-with-django-rest-api-part-3-3dh9)
- For Celery: 
    - [Documentation](https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html)
    - [Mastering Celery: A Guide to Background Tasks, Workers, and Parallel Processing in Python](https://khairi-brahmi.medium.com/mastering-celery-a-guide-to-background-tasks-workers-and-parallel-processing-in-python-eea575928c52)


## Contact

The key obtained from subscription to API-Football does cost money.

If you want to play around with the API without having to pay for your own subcription, send an email to hoangphucquan19@gmail.com requesting the key and I'd be happy to consider. 