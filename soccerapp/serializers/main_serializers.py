from rest_framework import serializers
from rest_framework.serializers import ValidationError
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from soccerapp.models import (
    User, Match, Team, TeamRanking,
    MoneylineBetInfo, HandicapBetInfo, TotalObjectsBetInfo,
)

class MyTokenObtainPairSerializer(TokenObtainPairSerializer): 
    """ Serializer for the login """

    @classmethod
    def get_token(cls, user): 
        token = super(MyTokenObtainPairSerializer, cls).get_token(user)
        token['username'] = user.username
        return token 


class RegisterSerializer(serializers.ModelSerializer): 
    """ Serializer for the register """
    class Meta: 
        model = User
        fields = ["username", "email", "password", "password2", "first_name", "last_name", "balance"]

    email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=User.objects.all())])
    password2 = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs): 
        """ Validate if the 2 passwords match """

        if attrs["password"] != attrs["password2"]: 
            raise ValidationError("Passwords didn't match.")
        return attrs

    def create(self, validated_data): 
        """ Create the user with the hashed password """

        # create user will also automatically hash the password
        created_user = User.objects.create_user(validated_data["username"], validated_data["email"], validated_data["password"])

        # set the first name, last name, and balance of the user 
        created_user.first_name = validated_data["first_name"]
        created_user.last_name = validated_data["last_name"]
        created_user.balance = validated_data["balance"]
        created_user.save()

        return created_user


class UserSerializer(serializers.ModelSerializer): 
    """ Serializer of the user """
    class Meta: 
        model = User
        exclude = ["password"]


class TeamSerializer(serializers.ModelSerializer): 
    """ Serializer of the team """
    class Meta: 
        model = Team
        fields = '__all__'


class TeamRankingSerializer(serializers.ModelSerializer): 
    """ Serializer of the team rank """
    class Meta: 
        model = TeamRanking
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop("league") # league doesn't matter 
        representation["team"] = instance.team.name
        representation["logo"] = instance.team.logo
        return representation


class MatchSerializer(serializers.ModelSerializer): 
    """ Serializer of the match """
    class Meta: 
        model = Match
        fields = '__all__'

    def to_representation(self, instance):
        field_list = ["updated_date", "halftime_score", "fulltime_score", "penalty", "possesion", "total_shots", "corners", "cards"]

        representation = super().to_representation(instance)
        representation["date"] = instance.date.strftime("%m/%d/%Y, %a %H:%M%p")
        if representation["status"] == "Not Finished": 
            for field in field_list: 
                representation[field] = "None-None"
        return representation


class MoneylineBetInfoSerializer(serializers.ModelSerializer): 
    """ Serializer of the moneyline bet info """

    class Meta: 
        model = MoneylineBetInfo
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["match_name"] = instance.match.__str__()
        representation["match_league"] = instance.match.league
        representation["match_time"] = instance.match.date.strftime("%m/%d, %H:%M")
        return representation


class HandicapBetInfoSerizalizer(serializers.ModelSerializer): 
    """ Serializer of the handicap bet info  """
    class Meta: 
        model = HandicapBetInfo
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["match_name"] = instance.match.__str__()
        representation["match_league"] = instance.match.league
        representation["match_time"] = instance.match.date.strftime("%m/%d, %H:%M")
        return representation


class TotalObjectsBetInfoSerializer(serializers.ModelSerializer):
    """ Serializer of the total goals bet info """ 
    class Meta: 
        model = TotalObjectsBetInfo
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # these extra fields are not a part of serializers and therefore ignored in validated_data
        representation["match_name"] = instance.match.__str__()
        representation["match_league"] = instance.match.league
        representation["match_time"] = instance.match.date.strftime("%m/%d, %H:%M")
        return representation
