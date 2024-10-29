from django.db import models

# User of the app
class User(models.Model): 
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    email = models.EmailField()
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=150)
    balance = models.DecimalField(max_digits=12, decimal_places=2)

    # example: mikequan19
    def __str__(self) -> str:
        return self.username
    

# Team (the number of teams is fixed)
# used for part of the page where people can comment on the team 
# many other objects include: Comment, Reply, etc.
class Team(models.Model): 
    league = models.CharField(max_length=100, choices={
        "Premiere League": "EPL",
        "La Liga": "LAL", 
        "Bundesliga": "BUN",
    }, default="Premiere League")
    name = models.CharField(max_length=150, unique=True)
    nickname = models.CharField(max_length=150, null=True, blank=True)
    # the images of the team's logo
    logo = models.URLField("logo of the team", null=True, blank=True)

    # info for the history of the team 
    founded_year = models.IntegerField("The year the team was founded")
    home_stadium = models.CharField(max_length=150)
    # the images of the home stadium of the team 
    stadium_image = models.URLField("Image of the home stadium", null=True, blank=True)
    description = models.TextField() 

    # example: Manchester United 
    def __str__(self) -> str:
        return self.name


# the soccer Match
class Match(models.Model): 
    league = models.CharField(max_length=100, choices={
        "Champions League": "UCL", 
        "Premiere League": "EPL",
        "La Liga": "LAL", 
        "Bundesliga": "BUN",
    })
    match_id = models.AutoField(primary_key=True, editable=False) # id imported from API 
    date = models.DateTimeField("The time the match begins")

    home_team = models.CharField(max_length=250)
    home_team_logo = models.URLField(null=True, blank=True)
    away_team = models.CharField(max_length=250)
    away_team_logo = models.URLField(null=True, blank=True)

    # the info about the match's result 
    # Finished matches will be deleted from the database in 7 days
    status = models.CharField(max_length=50, choices={
        "Not Finished": "NF", 
        "Finished": "FN"
    }, default="Not Finished")
    updated_date = models.DateField("The date the match's status is updated", null=True, blank=True)
    halftime_score = models.CharField(max_length=10, null=True, blank=True) # "3 - 0"
    fulltime_score = models.CharField(max_length=10, null=True, blank=True) # "3 - 3"
    penalty = models.CharField(max_length=10, null=True, blank=True) # "2 - 4"

    # example: Real Madrid vs Barcelona
    def __str__(self) -> str:
        return f"{self.home_team} vs {self.away_team}"


# the moneyline bet info 
class MoneylineBetInfo(models.Model): 
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    time_type = models.CharField(max_length=50, choices={
        "full time": "full_time", 
        "half time": "half_time",
    })
    bet_team = models.CharField(max_length=150)
    odd = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    # the settled bet will be deleted from the database in 7 days 
    status = models.CharField(max_length=50, choices={
        "Unsettled": "UN", 
        "Settled": "SE"
    }, default="Unsettled")
    settled_date = models.DateField("The date this moneyline bet was settled", null=True, blank=True)

    # example: Manchester United -200
    def __str__(self) -> str: 
        return f"{self.bet_team} {self.odd}"
    

# the moneyline bet of the user 
class UserMoneylineBet(models.Model): 
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bet_info = models.ForeignKey(MoneylineBetInfo, on_delete=models.CASCADE)
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # example mikequan19 bet $50: Manchester United -200
    def __str__(self) -> str: 
        return f"{self.user.username} bet {self.bet_amount}: {self.bet_info.bet_team} {self.bet_info.odd}"
    

# the handicap bet info 
class HandicapBetInfo(models.Model): 
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    time_type = models.CharField(max_length=50, choices={
        "full time": "full_time", 
        "half time": "half_time"})
    bet_team = models.CharField(max_length=150)
    # the handicap cover of the bet 
    handicap_cover = models.DecimalField(max_digits=5, decimal_places=2)
    odd = models.DecimalField(max_digits=8, decimal_places=2)
    # the settled bet will be deleted from the database in 7 days 
    status = models.CharField(max_length=50, choices={
        "Unsettled": "UN", 
        "Settled": "SE"
    }, default="Unsettled")
    settled_date = models.DateField("The date this handicap bet was settled", null=True, blank=True)

    # example: Manchester United -1.5 200
    def __str__(self) -> str:
        return f"{self.bet_team} {self.handicap_cover} {self.odd}"
    

# the handicap bet of the user 
class UserHandicapBet(models.Model): 
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bet_info = models.ForeignKey(HandicapBetInfo, on_delete=models.CASCADE)
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # example: mikequan19 bet $50: Manchester United -1.5 -200
    def __str__(self) -> str: 
        return f"{self.user.username} bet {self.bet_amount}: {self.bet_info.bet_team} {self.bet_info.handicap_cover} {self.bet_info.odd}"
    

# the total goals bet info
class TotalGoalsBetInfo(models.Model): 
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    time_type = models.CharField(max_length=50, choices={
        "full time": "full_time", 
        "half time": "half_time"
    })
    under_or_over = models.CharField(max_length=10, choices={
        "Under": "Under", 
        "Over": "Over", 
    })
    target_num_goals = models.IntegerField(default=0)
    odd = models.DecimalField(max_digits=8, decimal_places=2)
    # the settled bet will be deleted from the database in 7 days 
    status = models.CharField(max_length=50, choices={
        "Unsettled": "UN", 
        "Settled": "SE"
    }, default="Unsettled")
    settled_date = models.DateField("The date this total goals bet was settled", null=True, blank=True)

    # example: Over 5 goals 200
    def __str__(self) -> str:
        return f"{self.under_or_over} {self.target_num_goals} goals {self.odd}"
    

# the total goals bet of the user 
class UserTotalGoalsBet(models.Model): 
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bet_info = models.ForeignKey(TotalGoalsBetInfo, on_delete=models.CASCADE)
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # example: mikequan19 bet $50: Over 5 goals 200
    def __str__(self) -> str: 
        return f"{self.user.username} bet {self.bet_amount}: {self.bet_info.under_or_over} {self.bet_info.target_num_goals} {self.bet_info.odd}"
    