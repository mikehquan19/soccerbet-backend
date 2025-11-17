from rest_framework import serializers
from rest_framework.serializers import ValidationError
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from soccerapp.models import (
    User, Match, Team, TeamRanking,
    MoneylineBetInfo, HandicapBetInfo, TotalObjectsBetInfo,
)

class MyTokenObtainPairSerializer(TokenObtainPairSerializer): 
    """Serializer for the login"""

    @classmethod
    def get_token(cls, user): 
        token = super(MyTokenObtainPairSerializer, cls).get_token(user)
        token['username'] = user.username
        return token 


class RegisterSerializer(serializers.ModelSerializer): 
    """Serializer for the register"""
    class Meta: 
        model = User
        fields = ["username", "email", "password", "password2", "first_name", "last_name", "balance"]

    email = serializers.EmailField(
        required=True, 
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs): 
        """Validate if the 2 passwords match"""
        if attrs["password"] != attrs["password2"]: 
            raise ValidationError("Passwords do not match")
        return attrs

    def create(self, validated_data): 
        """Create the user with the hashed password"""
        created_user = User.objects.create_user(
            validated_data["username"], 
            validated_data["email"], 
            validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            balance=validated_data["balance"]
        )
        return created_user


class UserSerializer(serializers.ModelSerializer): 
    """Serializer of the user"""
    class Meta: 
        model = User
        exclude = ["password"]


class TeamSerializer(serializers.ModelSerializer): 
    """Serializer of the team"""
    class Meta: 
        model = Team
        fields = '__all__'


class TeamRankingSerializer(serializers.ModelSerializer): 
    """Serializer of the team rank"""
    team = TeamSerializer()

    class Meta: 
        model = TeamRanking
        fields = '__all__'


class MatchSerializer(serializers.ModelSerializer): 
    """Serializer of the match"""
    home_team = TeamSerializer()
    away_team = TeamSerializer()

    class Meta: 
        model = Match
        fields = '__all__'


class MoneylineBetInfoSerializer(serializers.ModelSerializer): 
    """Serializer of the moneyline bet info"""
    match = MatchSerializer()
    class Meta: 
        model = MoneylineBetInfo
        fields = '__all__'


class HandicapBetInfoSerizalizer(serializers.ModelSerializer): 
    """Serializer of the handicap bet info"""
    match = MatchSerializer()
    class Meta: 
        model = HandicapBetInfo
        fields = '__all__'

class TotalObjectsBetInfoSerializer(serializers.ModelSerializer):
    """Serializer of the total objects bet info""" 
    match = MatchSerializer()
    class Meta: 
        model = TotalObjectsBetInfo
        fields = '__all__'