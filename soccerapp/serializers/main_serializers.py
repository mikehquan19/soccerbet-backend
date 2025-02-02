from rest_framework import serializers
from rest_framework.serializers import ValidationError
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from soccerapp.models import (
    User, Match, Team, Comment, TeamRanking,
    MoneylineBetInfo, HandicapBetInfo, TotalObjectsBetInfo,
)

# serializer for the login
class MyTokenObtainPairSerializer(TokenObtainPairSerializer): 
    @classmethod
    def get_token(cls, user): 
        token = super(MyTokenObtainPairSerializer, cls).get_token(user)
        token['username'] = user.username
        return token 


# serializer for the register 
class RegisterSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = User
        fields = ["username", "email", "password", "password2", "first_name", "last_name", "balance"]

    email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=User.objects.all())])
    password2 = serializers.CharField(write_only=True, required=True)

    # validate if the 2 passwords match
    def validate(self, attrs): 
        if attrs["password"] != attrs["password2"]: 
            raise ValidationError("Passwords didn't match.")
        return attrs

    # create the user with the hashed password 
    def create(self, validated_data): 
        # create user will also automatically hash the password
        created_user = User.objects.create_user(validated_data["username"], validated_data["email"], validated_data["password"])

        # set the first name, last name, and balance of the user 
        created_user.first_name = validated_data["first_name"]
        created_user.last_name = validated_data["last_name"]
        created_user.balance = validated_data["balance"]
        created_user.save()

        return created_user


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


# serializer of the list of comments, showing whether the comment is liked
class CommentSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = Comment
        fields = '__all__'

    """
    show whether this comment is liked by request user and belongs to the user,
    related to user so it can't be done in to_representation()

    they are read-only so can be easily ignored
    """
    is_liked_by_user = serializers.BooleanField(read_only=True) 
    is_from_user = serializers.BooleanField(read_only=True)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["username"] = instance.user.username
        representation["created_time"] = instance.created_time.strftime("%m/%d/%Y %H:%M:%S")
        representation["likes"] = instance.likes.count()
        return representation
    

# serializer of the team rank
class TeamRankingSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = TeamRanking
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop("league") # league doesn't matter 
        representation["team"] = instance.team.name
        representation["logo"] = instance.team.logo
        return representation


# serializer of the match 
class MatchSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = Match
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["date"] = instance.date.strftime("%m/%d/%Y, %a %H:%M%p")
        if representation["status"] == "Not Finished": 
            field_list = ["updated_date", "halftime_score", "fulltime_score", "penalty", "possesion", "total_shots", "corners", "cards"]
            for field in field_list: 
                representation[field] = "None-None"
        return representation


# serializer of the moneyline bet info 
class MoneylineBetInfoSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = MoneylineBetInfo
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["match_name"] = instance.match.__str__()
        representation["match_league"] = instance.match.league
        representation["match_time"] = instance.match.date.strftime("%m/%d, %H:%M")
        return representation


# serializer of the handicap bet info 
class HandicapBetInfoSerizalizer(serializers.ModelSerializer): 
    class Meta: 
        model = HandicapBetInfo
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["match_name"] = instance.match.__str__()
        representation["match_league"] = instance.match.league
        representation["match_time"] = instance.match.date.strftime("%m/%d, %H:%M")
        return representation


# serializer of the total goals bet info 
class TotalObjectsBetInfoSerializer(serializers.ModelSerializer): 
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
