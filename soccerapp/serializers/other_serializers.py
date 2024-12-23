from rest_framework import serializers
from soccerapp.models import (
    User, Match, Team, TeamRanking,
    MoneylineBetInfo, HandicapBetInfo, TotalObjectsBetInfo,
)

# serializer of the user 
class UserSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = User
        exclude = ["password"]


# serializer of the team
class TeamSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = Team
        fields = '__all__'


# serializer of the team rank
class TeamRankingSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = TeamRanking
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop("league")
        representation["team"] = instance.team.name
        representation["logo"] = instance.team.logo
        return representation


# serializer of the match 
class MatchSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = Match
        fields = '__all__'


# serializer of the moneyline bet info 
class MoneylineBetInfoSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = MoneylineBetInfo
        fields = '__all__'


# serializer of the handicap bet info 
class HandicapBetInfoSerizalizer(serializers.ModelSerializer): 
    class Meta: 
        model = HandicapBetInfo
        fields = '__all__'


# serializer of the total goals bet info 
class TotalObjectsBetInfoSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = TotalObjectsBetInfo
        fields = '__all__'
