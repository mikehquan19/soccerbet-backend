from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

LEAGUE_CHOICES= [
    ("Champions League", "UCL"), 
    ("Premiere League", "EPL"), 
    ("La Liga", "LAL"),
    ("Bundesliga", "BUN"),
    ("Serie A", "SER"),
    ("Ligue 1", "LEA"),
]

STATUS_CHOICES = [
    ("Not Finished", "NF"), 
    ("Finished", "FN")
]

PERIOD_CHOICES = [
    ("Full-time", "full_time"),
    ("Half-time", "half_time"),
]

BET_OBJECT_CHOICES = [
    ("Goals", "Goals"), 
    ("Corners", "Corners"), 
    ("Cards", "Cards"), 
]

UNDER_ORVER_CHOICES = [
    ("Under", "Under"), 
    ("Over", "Over")
]

SETTLE_CHOICES = [
    ("Unsettled", "UN"), 
    ("Settled", "SE")
]

class User(AbstractUser): 
    """User of the app, with the tokens balance"""
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self) -> str: 
        return self.username


class Team(models.Model): 
    """
    Team (the number of teams is fixed over the season)
    UCL Teams: Teams that play in lesser known league
    """
    league = models.CharField(max_length=20, choices=LEAGUE_CHOICES)
    name = models.CharField(max_length=50, unique=True)
    nickname = models.CharField(max_length=100, null=True, blank=True)
    logo = models.URLField(null=True, blank=True)
    founded_year = models.IntegerField(null=True, blank=True)
    home_stadium = models.CharField(max_length=100)
    stadium_image = models.URLField(null=True, blank=True)
    description = models.TextField() 

    def __str__(self) -> str:
        """Example: Manchester United"""
        return self.name
    
class TeamRanking(models.Model): 
    """ Ranking of the team in the league  """
    league = models.CharField(max_length=20, choices=LEAGUE_CHOICES)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    rank = models.IntegerField()
    points = models.IntegerField()
    num_matches = models.IntegerField()
    num_wins = models.IntegerField()
    num_loses = models.IntegerField()
    num_draws = models.IntegerField()

    class Meta:
        ordering = ["league", "rank"]

    def __str__(self) -> str: 
        """Example Champions League: Real Madrid 18"""
        return f"{self.league}: {self.team} {self.rank}"


class Match(models.Model): 
    """The soccer Match"""
    league = models.CharField(max_length=20, choices=LEAGUE_CHOICES)
    match_id = models.IntegerField(unique=True)
    started_at = models.DateTimeField(default=timezone.now())
    updated_at = models.DateTimeField(default=timezone.now())
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="home_team")
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="away_team")
    status = models.CharField( # Finished matches will be deleted from the database in 7 days
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="Not Finished"
    )
    class Meta: 
        ordering = ["started_at"]

    def __str__(self) -> str:
        """Example: Real Madrid vs Barcelona"""
        return f"{self.home_team} vs {self.away_team}"


class MatchStat(models.Model): 
    """The statistics of the finished matches"""
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=[
        ("Halftime score", "halftime_score"),
        ("Fulltime score", "fulltime_score"),
        ("Penalty", "penalty"),
        ("Possesion", "possesion"),
        ("Total shots", "total_shots"),
        ("Corners", "corners"),
        ("Yellow cards", "yellow_cards"),
    ])
    home_stat = models.IntegerField(null=True, blank=True)
    away_stat = models.IntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.stat_type}: {self.home_stat}-{self.away_stat}"


class MoneylineBetInfo(models.Model): 
    """The moneyline bet info"""
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default="Full-time")
    bet_object = models.CharField(
        max_length=20, 
        choices=BET_OBJECT_CHOICES, 
        default="Goals"
    )
    bet_team = models.CharField(max_length=50)
    odd = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    # The settled bet will be deleted from the database in 7 days 
    status = models.CharField(
        max_length=20, 
        choices=SETTLE_CHOICES,
        default="Unsettled"
    )
    settled_at = models.DateField(null=True, blank=True)

    def __str__(self) -> str: 
        """Example: Manchester United vs Arsenal: Manchester United full-time -200"""
        return f"{self.match}: {self.bet_team} {self.period} {self.bet_object} {self.odd}"
    

class UserMoneylineBet(models.Model): 
    """ The moneyline bet of the user  """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bet_info = models.ForeignKey(MoneylineBetInfo, on_delete=models.CASCADE)
    bet_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateField(null=True, blank=True)
    payout = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    def __str__(self) -> str: 
        """Example: mikequan19 bet $50: Manchester United -200"""
        return f"{self.user.username} bet {self.bet_amount}, {self.bet_info}"
    

class HandicapBetInfo(models.Model): 
    """ The handicap bet info """
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default="Full-time")
    bet_object = models.CharField(
        max_length=20, 
        choices=BET_OBJECT_CHOICES, 
        default="Goals"
    )
    bet_team = models.CharField(max_length=50)

    # The handicap cover of the bet 
    cover = models.DecimalField(max_digits=5, decimal_places=2)
    odd = models.DecimalField(max_digits=8, decimal_places=2)

    # Settled bet will be deleted from the database in 7 days 
    status = models.CharField(
        max_length=50, 
        choices=SETTLE_CHOICES, 
        default="Unsettled"
    )

    settled_at = models.DateField(null=True, blank=True)

    def __str__(self) -> str:
        """Example: Manchester United -1.5 200"""
        return f"{self.match}: {self.bet_team} {self.period} {self.bet_object} {self.cover} {self.odd}"
    

class UserHandicapBet(models.Model): 
    """The handicap bet of the user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bet_info = models.ForeignKey(HandicapBetInfo, on_delete=models.CASCADE)
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateField(null=True, blank=True)
    payout = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    def __str__(self) -> str: 
        """ Example: mikequan19 bet $50: Manchester United -1.5 -200 """
        return f"{self.user.username} bet {self.bet_amount}, {self.bet_info}"
    

class TotalObjectsBetInfo(models.Model): 
    """ The total goals bet info """
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default="Full-time")
    bet_object = models.CharField(
        max_length=50,
        choices=BET_OBJECT_CHOICES,
        default="Goals"
    )
    under_or_over = models.CharField(max_length=10, choices=UNDER_ORVER_CHOICES)
    num_objects = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    odd = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Settled bets will be deleted from the database in 7 days 
    status = models.CharField(
        max_length=20, 
        choices=SETTLE_CHOICES, 
        default="Unsettled"
    )
    settled_at = models.DateField(null=True, blank=True)

    def __str__(self) -> str:
        """Example: Over 5 goals 200"""
        return f"{self.match}: {self.under_or_over} {self.num_objects} {self.bet_object} {self.period} {self.odd}"


class UserTotalObjectsBet(models.Model): 
    """The total goals bet of the user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bet_info = models.ForeignKey(TotalObjectsBetInfo, on_delete=models.CASCADE)
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateField(null=True, blank=True)
    payout = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    def __str__(self) -> str: 
        """Example: mikequan19 bet $50: Over 5 goals 200"""
        return f"{self.user.username} bet {self.bet_amount}, {self.bet_info}"
