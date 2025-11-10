from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

LEAGUE_CHOICES= [
    ("Champions League", "UCL"), 
    ("Premiere League", "EPL"), 
    ("La Liga", "LAL"),
    ("Bundesliga", "BUN"),
    ("Serie A", "SER"),
    ("League 1", "LEA"),
]

STATUS_CHOICES = [
    ("Not Finished", "NF"), 
    ("Finished", "FN")
]

TIME_TYPE_CHOICES = [
    ("Full-time", "full_time"),
    ("Half-time", "half_time"),
]

BET_OBJECT_CHOICES = [
    ("Goals", "Goals"), 
    ("Corners", "Corners"), 
    ("Cards", "Cards"), 
]

UNSETTLE_CHOICES = [
    ("Unsettled", "UN"), 
    ("Settled", "SE")
]

class User(AbstractUser): 
    """ User of the app, with the tokens balance """
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self) -> str: 
        return self.username


class Team(models.Model): 
    """
    Team (the number of teams is fixed over the season)
    UCL Teams: teams that play in lesser known league but they still get to to play in the UCL
    """
    
    league = models.CharField(max_length=100, choices=LEAGUE_CHOICES)
    name = models.CharField(max_length=150, unique=True)
    nickname = models.CharField(max_length=150, null=True, blank=True)
    logo = models.URLField(null=True, blank=True)

    founded_year = models.IntegerField()
    home_stadium = models.CharField(max_length=150)
    stadium_image = models.URLField(null=True, blank=True)
    description = models.TextField() 

    def __str__(self) -> str:
        """ Example: Manchester United """
        return self.name
    
class TeamRanking(models.Model): 
    """ Ranking of the team in the league  """

    league = models.CharField(max_length=100, choices=LEAGUE_CHOICES)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    rank = models.IntegerField()
    points = models.IntegerField()
    num_watches = models.IntegerField()
    num_wins = models.IntegerField()
    num_loses = models.IntegerField()
    num_draws = models.IntegerField()

    class Meta:
        ordering = ["league", "rank"]

    def __str__(self) -> str: 
        """ Example Champions League: Real Madrid 18 (LOL) """
        return f"{self.league}: {self.team} {self.rank}"


class Match(models.Model): 
    """ The soccer Match """

    league = models.CharField(max_length=100, choices=LEAGUE_CHOICES)
    match_id = models.IntegerField(unique=True)
    date = models.DateTimeField("The time the match begins")

    home_team = models.CharField(max_length=250)
    home_team_logo = models.URLField(null=True, blank=True)
    away_team = models.CharField(max_length=250)
    away_team_logo = models.URLField(null=True, blank=True)

    # The info about the match's result. 
    # Finished matches will be deleted from the database in 7 days
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Not Finished")
    updated_date = models.DateField(null=True, blank=True)
    # 3-0
    halftime_score = models.CharField(max_length=10, null=True, blank=True)
    # 3-3
    fulltime_score = models.CharField(max_length=10, null=True, blank=True)
    # 2-4
    penalty = models.CharField(max_length=10, null=True, blank=True)
    # 57-43
    possesion = models.CharField(max_length=10, null=True, blank=True) 
    # 10-7
    total_shots = models.CharField(max_length=10, null=True, blank=True)
    # 11-13
    corners = models.CharField(max_length=10, null=True, blank=True)
    # 3-2
    cards = models.CharField(max_length=10, null=True, blank=True)

    class Meta: 
        ordering = ["date"]

    def __str__(self) -> str:
        """ Example: Real Madrid vs Barcelona """
        return f"{self.home_team} vs {self.away_team}"


class MoneylineBetInfo(models.Model): 
    """ The moneyline bet info """

    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    time_type = models.CharField(max_length=50, choices=TIME_TYPE_CHOICES)
    bet_object = models.CharField(max_length=50, choices=BET_OBJECT_CHOICES, default="Goals")

    bet_team = models.CharField(max_length=150)
    odd = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    # The settled bet will be deleted from the database in 7 days 
    status = models.CharField(max_length=50, choices=UNSETTLE_CHOICES, default="Unsettled")

    settled_date = models.DateField(
        "The date this moneyline bet was settled", 
        null=True, blank=True
    )

    def __str__(self) -> str: 
        """ Example: Manchester United -200 """
        return f"{self.match}: {self.bet_team} {self.time_type} {self.bet_object} {self.odd}"
    

class UserMoneylineBet(models.Model): 
    """ The moneyline bet of the user  """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bet_info = models.ForeignKey(MoneylineBetInfo, on_delete=models.CASCADE)
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_date = models.DateField(null=True, blank=True)
    payout = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self) -> str: 
        """ example mikequan19 bet $50: Manchester United -200 """
        return f"{self.user.username} bet {self.bet_amount}, {self.bet_info}"
    

class HandicapBetInfo(models.Model): 
    """ The handicap bet info """

    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    time_type = models.CharField(max_length=50, choices=TIME_TYPE_CHOICES)
    bet_object = models.CharField(max_length=50, choices=BET_OBJECT_CHOICES, default="Goals")

    bet_team = models.CharField(max_length=150)
    # The handicap cover of the bet 
    handicap_cover = models.DecimalField(max_digits=5, decimal_places=2)
    odd = models.DecimalField(max_digits=8, decimal_places=2)

    # the settled bet will be deleted from the database in 7 days 
    status = models.CharField(max_length=50, choices=UNSETTLE_CHOICES, default="Unsettled")

    settled_date = models.DateField(null=True, blank=True)

    def __str__(self) -> str:
        """ Example: Manchester United -1.5 200 """
        return f"{self.match}: {self.bet_team} {self.time_type} {self.bet_object} {self.handicap_cover} {self.odd}"
    

class UserHandicapBet(models.Model): 
    """ The handicap bet of the user  """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bet_info = models.ForeignKey(HandicapBetInfo, on_delete=models.CASCADE)
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_date = models.DateField(null=True, blank=True)
    payout = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self) -> str: 
        """ Example: mikequan19 bet $50: Manchester United -1.5 -200 """
        return f"{self.user.username} bet {self.bet_amount}, {self.bet_info}"
    

class TotalObjectsBetInfo(models.Model): 
    """ The total goals bet info """
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    time_type = models.CharField(max_length=50, choices=TIME_TYPE_CHOICES)
    bet_object = models.CharField(max_length=50, choices=BET_OBJECT_CHOICES, default="Goals")

    under_or_over = models.CharField(
        max_length=10, 
        choices={
            "Under": "Under", 
            "Over": "Over", 
        }
    )

    target_num_objects = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    odd = models.DecimalField(max_digits=8, decimal_places=2)
    
    # the settled bet will be deleted from the database in 7 days 
    status = models.CharField(max_length=50, choices=UNSETTLE_CHOICES, default="Unsettled")

    settled_date = models.DateField(
        "The date this total goals bet was settled", 
        null=True, blank=True
    )

    def __str__(self) -> str:
        """ Example: Over 5 goals 200 """
        return f"{self.match}: {self.under_or_over} {self.target_num_objects} {self.bet_object} {self.time_type}  {self.odd}"
    

class UserTotalObjectsBet(models.Model): 
    """ The total goals bet of the user """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bet_info = models.ForeignKey(TotalObjectsBetInfo, on_delete=models.CASCADE)
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_date = models.DateField(null=True, blank=True)
    payout = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self) -> str: 
        """ Example: mikequan19 bet $50: Over 5 goals 200 """
        return f"{self.user.username} bet {self.bet_amount}, {self.bet_info}"
