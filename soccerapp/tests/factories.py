import factory
from soccerapp.models import *
from factory.django import DjangoModelFactory

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = "RandomUser"
    balance = factory.Faker(
        "pydecimal", left_digits=8, right_digits=2, positive=True
    )


class TeamFactory(DjangoModelFactory):
    class Meta:
        model = Team

    league = "Premiere League"
    name = factory.Sequence(lambda n: f"Team {n}")
    nickname = factory.Faker("word")
    logo = factory.Faker("image_url")
    founded_year = factory.Faker("year")
    home_stadium = factory.Faker("city")
    stadium_image = factory.Faker("image_url")
    description = factory.Faker("sentence")


class MatchFactory(DjangoModelFactory):
    class Meta:
        model = Match

    league = "Premiere League"
    match_id = factory.Sequence(lambda n: n + 1)
    started_at = factory.Faker("date_time")
    updated_at = factory.Faker("date_time")
    home_team = factory.SubFactory(TeamFactory)
    away_team = factory.SubFactory(TeamFactory)
    status = "Not Finished"


class MoneylineBetInfoFactory(DjangoModelFactory):
    class Meta:
        model = MoneylineBetInfo

    match = factory.SubFactory(Match)
    period = "Full-time"
    bet_object = "Goals"
    bet_team = factory.Faker("word")
    odd = factory.Faker("pydecimal", left_digits=6, right_digits=2)
    status = "Unsettled"


class UserMoneylineBetFactory(DjangoModelFactory):
    class Meta:
        model = UserMoneylineBet

    user = factory.SubFactory(UserFactory)
    bet_info = factory.SubFactory(MoneylineBetInfoFactory)
    bet_amount = factory.Faker("pydecimal", left_digits=8, right_digits=2)
    created_at = factory.Faker("date_time")
    payout = factory.Faker(
        "pydecimal", left_digits=8, right_digits=2, positive=True
    )
