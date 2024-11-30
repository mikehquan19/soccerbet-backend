from rest_framework import serializers
from soccerapp.models import (
    Match, Team, 
    MoneylineBetInfo, HandicapBetInfo, TotalGoalsBetInfo,
)
# serializer of the team
class TeamSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = Team
        fields = '__all__'


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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["match"] = instance.match.match_id
        return representation


# serializer of the handicap bet info 
class HandicapBetInfoSerizalizer(serializers.ModelSerializer): 
    class Meta: 
        model = HandicapBetInfo
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["match"] = instance.match.match_id
        return representation


# serializer of the total goals bet info 
class TotalGoalsBetInfoSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = TotalGoalsBetInfo
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["match"] = instance.match.match_id
        return representation