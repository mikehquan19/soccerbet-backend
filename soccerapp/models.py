from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser): 
    """ User of the app, with the balance """
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self) -> str: 
        return self.username


class Team(models.Model): 
    """
    Team (the number of teams is fixed)
    used for part of the page where people can comment on the team, and rankings 
    many other objects include: Comment, Reply, etc.
    """

    league = models.CharField(max_length=100, choices={
        "Premiere League": "EPL",
        "La Liga": "LAL", 
        "Bundesliga": "BUN",
    }, default="Premiere League")
    name = models.CharField(max_length=150, unique=True)
    nickname = models.CharField(max_length=150, null=True, blank=True)
    logo = models.URLField("logo of the team", null=True, blank=True)

    # info for the history of the team 
    founded_year = models.IntegerField("The year the team was founded")
    home_stadium = models.CharField(max_length=150)
    # the images of the home stadium of the team 
    stadium_image = models.URLField("Image of the home stadium", null=True, blank=True)
    description = models.TextField() 

    def __str__(self) -> str:
        """ Example: Manchester United """
        return self.name
    

class Comment(models.Model): 
    """ The comment to the team  """

    # the team and user this comment belongs to 
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    created_time = models.DateTimeField(default=timezone.now, blank=True)
    content = models.TextField()
    # list of likes from other users 
    likes = models.ManyToManyField(User, related_name='like_users', blank=True)

    # the parent comment this comment belongs to & the actual user this comment replies to 
    replyToComment = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    replyToUsername = models.CharField(max_length=150, default="", blank=True)
    
    class Meta: 
        ordering = ["team", "-created_time"]

    def __str__(self) -> str: 
        str = f"{self.user}'s comment on {self.team}"
        if self.replyToUsername != "": str += f" to {self.replyToUsername}" 
        return str


class TeamRanking(models.Model): 
    """ Ranking of the team in the league  """

    league = models.CharField(max_length=100, choices={
        "Champions League": "UCL", 
        "Premiere League": "EPL",
        "La Liga": "LAL", 
        "Bundesliga": "BUN",
    })
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

    league = models.CharField(max_length=100, choices={
        "Champions League": "UCL", 
        "Premiere League": "EPL",
        "La Liga": "LAL", 
        "Bundesliga": "BUN",
    })
    match_id = models.IntegerField(unique=True) # match_id imported from API to do things
    date = models.DateTimeField("The time the match begins")

    home_team = models.CharField(max_length=250)
    home_team_logo = models.URLField(null=True, blank=True)
    away_team = models.CharField(max_length=250)
    away_team_logo = models.URLField(null=True, blank=True)

    # The info about the match's result. Finished matches will be deleted from the database in 7 days
    status = models.CharField(max_length=50, choices={
        "Not Finished": "NF", 
        "Finished": "FN"
    }, default="Not Finished")

    updated_date = models.DateField("The date the match's status is updated", null=True, blank=True)
    halftime_score = models.CharField(max_length=10, null=True, blank=True) # "3-0"
    fulltime_score = models.CharField(max_length=10, null=True, blank=True) # "3-3"
    penalty = models.CharField(max_length=10, null=True, blank=True) # "2-4"

    # other statistics such as posession, 
    possesion = models.CharField(max_length=10, null=True, blank=True) # "57-43"
    total_shots = models.CharField(max_length=10, null=True, blank=True) # "10-7"
    corners = models.CharField(max_length=10, null=True, blank=True) # "11-13"
    cards = models.CharField(max_length=10, null=True, blank=True) # "3-2"

    class Meta: 
        ordering = ["date"]

    def __str__(self) -> str:
        """ Example: Real Madrid vs Barcelona """
        return f"{self.home_team} vs {self.away_team}"


class MoneylineBetInfo(models.Model): 
    """ The moneyline bet info """

    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    time_type = models.CharField(max_length=50, choices={"full time": "full_time", "half time": "half_time" })
    bet_object = models.CharField(max_length=50, choices={
        "Goals": "Goals", 
        "Corners": "Corners", 
        "Cards": "Cards", 
    }, default="Goals")

    bet_team = models.CharField(max_length=150)
    odd = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    # the settled bet will be deleted from the database in 7 days 
    status = models.CharField(max_length=50, choices={
        "Unsettled": "UN", 
        "Settled": "SE"
    }, default="Unsettled")

    settled_date = models.DateField("The date this moneyline bet was settled", null=True, blank=True)

    def __str__(self) -> str: 
        """ Example: Manchester United -200 """
        return f"{self.match}: {self.bet_team} {self.time_type} {self.bet_object} {self.odd}"
    

class UserMoneylineBet(models.Model): 
    """ The moneyline bet of the user  """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bet_info = models.ForeignKey(MoneylineBetInfo, on_delete=models.CASCADE)
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_date = models.DateField("The date this moneyline bet was created", null=True, blank=True)
    payout = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self) -> str: 
        """ example mikequan19 bet $50: Manchester United -200 """
        return f"{self.user.username} bet {self.bet_amount}, {self.bet_info}"
    

class HandicapBetInfo(models.Model): 
    """ The handicap bet info """

    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    time_type = models.CharField(max_length=50, choices={"full time": "full_time",  "half time": "half_time"})
    bet_object = models.CharField(max_length=50, choices={
        "Goals": "Goals", 
        "Corners": "Corners", 
        "Cards": "Cards", 
    }, default="Goals")

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

    def __str__(self) -> str:
        """ Example: Manchester United -1.5 200 """
        return f"{self.match}: {self.bet_team} {self.time_type} {self.bet_object} {self.handicap_cover} {self.odd}"
    

class UserHandicapBet(models.Model): 
    """ The handicap bet of the user  """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bet_info = models.ForeignKey(HandicapBetInfo, on_delete=models.CASCADE)
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_date = models.DateField("The date this handicap bet was created", null=True, blank=True)
    payout = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self) -> str: 
        """ Example: mikequan19 bet $50: Manchester United -1.5 -200 """
        return f"{self.user.username} bet {self.bet_amount}, {self.bet_info}"
    

class TotalObjectsBetInfo(models.Model): 
    """ The total goals bet info """
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    time_type = models.CharField(max_length=50, choices={
        "full time": "full_time", 
        "half time": "half_time"
    })

    bet_object = models.CharField(max_length=50, choices={
        "Goals": "Goals", 
        "Corners": "Corners", 
        "Cards": "Cards", 
    }, default="Goals")

    under_or_over = models.CharField(max_length=10, choices={
        "Under": "Under", 
        "Over": "Over", 
    })

    target_num_objects = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    odd = models.DecimalField(max_digits=8, decimal_places=2)
    
    # the settled bet will be deleted from the database in 7 days 
    status = models.CharField(max_length=50, choices={
        "Unsettled": "UN", 
        "Settled": "SE"
    }, default="Unsettled")

    settled_date = models.DateField("The date this total goals bet was settled", null=True, blank=True)

    def __str__(self) -> str:
        """ Example: Over 5 goals 200 """
        return f"{self.match}: {self.under_or_over} {self.target_num_objects} {self.bet_object} {self.time_type}  {self.odd}"
    

class UserTotalObjectsBet(models.Model): 
    """ The total goals bet of the user """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bet_info = models.ForeignKey(TotalObjectsBetInfo, on_delete=models.CASCADE)
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_date = models.DateField("The date this total goals bet was created", null=True, blank=True)
    payout = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self) -> str: 
        """ Example: mikequan19 bet $50: Over 5 goals 200 """
        return f"{self.user.username} bet {self.bet_amount}, {self.bet_info}"
    