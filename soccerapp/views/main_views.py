"""
ALL OF THE VIEWS IN HERE HAVE PERMISSION ALLOWANY, AND ARE ACCESSIBLE TO ANY END USERS
"""

from typing import Dict, Union, List, Any
from django.shortcuts import get_object_or_404
from django.db.models import QuerySet
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.validators import ValidationError
from soccerapp.models import (
    User, Match, Team, TeamRanking,
    MoneylineBetInfo, HandicapBetInfo, TotalObjectsBetInfo,
)
from soccerapp.serializers import (
    MyTokenObtainPairSerializer, RegisterSerializer, MatchSerializer, TeamSerializer, TeamRankingSerializer,
    MoneylineBetInfoSerializer, HandicapBetInfoSerizalizer, TotalObjectsBetInfoSerializer,
)

"""Mapping the value of request parameter to the value of the database"""
LEAGUES_MAP = {
    "ucl": "Champions League", 
    "epl": "Premiere League", 
    "lal": "La Liga", 
    "bun": "Bundesliga",
    "ser": "Serie A",
    "lea": "Ligue 1"
}

"""Mapping the different format for time type"""
PERIOD_MAP = {
    "half_time": "Half-time", 
    "full_time": "Full-time"
}

class Login(TokenObtainPairView): 
    """View to handle the user login"""
    permission_classes = [AllowAny]
    serializer_class = MyTokenObtainPairSerializer


class Register(generics.CreateAPIView): 
    """View to handle the user register"""
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class TeamList(APIView): 
    """View to list all of the team according to the league"""
    permission_classes = [AllowAny]

    def get(self, request, format=None) -> Response: 
        league = request.query_params.get("league")
        if league is None: 
            raise ValidationError({ "error": "League not specified" })

        # Get the list of teams of the league
        team_list = Team.objects.filter(league=LEAGUES_MAP[league])
        team_list_serializer = TeamSerializer(team_list, many=True)
        return Response(team_list_serializer.data)


class TeamDetail(generics.RetrieveAPIView): 
    permission_classes = [AllowAny]
    queryset = Team.objects.all() 
    serializer_class = TeamSerializer


class MatchList(APIView): 
    """View to list all of the matches according to the league"""
    permission_classes = [AllowAny]

    def get(self, request, format=None) -> Response: 
        STATUS_MAP = { 
            "NF": "Not Finished", 
            "FN": "Finished" 
        }
        league = request.query_params.get("league")
        status = request.query_params.get("status")

        # User must specify status for this endpoint 
        if status is None: 
            raise ValidationError({ "error": "Status is not defined" })
        
        # Avoid the N+1 Query problems
        if league is None: 
            match_list = Match.objects.filter(
                status=STATUS_MAP[status]).select_related("home_team", "away_team")
        else: 
            match_list = Match.objects.filter(
                league=LEAGUES_MAP[league], status=STATUS_MAP[status]).select_related("home_team", "away_team")
        match_list_serializer = MatchSerializer(match_list, many=True)
        return Response(match_list_serializer.data)
    

class MatchDetail(generics.RetrieveAPIView): 
    permission_classes = [AllowAny]
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    lookup_field = "match_id"


class Standings(APIView): 
    """View to handle the rankings of the league"""
    permission_classes = [AllowAny]

    def get(self, request) -> Response: 
        league_name = request.query_params.get("league")
        if not league_name: 
            raise ValidationError({"error": "League not specified"})

        standings = TeamRanking.objects.filter(league=LEAGUES_MAP[league_name]).select_related("team")
        standings_serializer = TeamRankingSerializer(standings, many=True)
        return Response(standings_serializer.data)
     

""" VIEWS FOR BET INFO """
class MoneylineInfoList(APIView): 
    """View to list all of the moneyline bet info of the match with given match id"""
    permission_classes = [AllowAny]

    def get(self, request, match_id: int, format=None) -> Response: 
        bet_object = request.query_params.get("bet_object")
        if bet_object is None: 
            raise ValidationError({"error": "Bet object is not defined"})
        
        # List of moneyline bets 
        match = get_object_or_404(Match, match_id=match_id)
        # List of moneyline bet info for halftime and fulltime
        response_data = {
            "half_time": None, 
            "full_time": None
        }
        for period in list(response_data.keys()): 
            # List of moneyline bet info for this time type 
            info_list = MoneylineBetInfo.objects.filter(
                match=match, 
                bet_object=bet_object, 
                period=PERIOD_MAP[period]).select_related("match", "match__home_team", "match__away_team")
            info_list_serializer = MoneylineBetInfoSerializer(info_list, many=True)
            response_data[period] = info_list_serializer.data

        return Response(response_data)


class HandicapInfoList(APIView):
    """ View to list all of the handicap bet info of the match  """
    permission_classes = [AllowAny]
    
    def group_handicap_info(
        self, info_list: Any, home_team: str
        ) -> List[Dict[str, Union[HandicapBetInfo, None]]]: 
        """
        Group the handicap bet info that correspond to each other together.
        The form ```[[home1 -cover, away1 cover], [home2 -cover, away2 cover], ...]```
        """
        # Dictionary mapping the cover to the list of handicap info
        cover_to_info_dict = {} 

        for info in info_list: 
            # The handicap cover of this info
            cover = -float(info["cover"]) if info["bet_team"] != home_team else float(info["cover"])

            # If this handicap cover isn't already in the dictionary, add it
            if cover not in cover_to_info_dict: 
                cover_to_info_dict[cover] = { 
                    "home": None, 
                    "away": None 
                }
            # The put info ino the right place
            team = "home" if info["bet_team"] == home_team else "away"
            cover_to_info_dict[cover][team] = info

        # Convert the dictionary to the list of values
        return list(cover_to_info_dict.values())
    
    def get(self, request, match_id: int, format=None) -> Response: 
        bet_object = request.query_params.get("bet_object")
        if bet_object is None: 
            raise ValidationError({"error": "Bet object is not defined"})

        # The list of handicap bets 
        match = get_object_or_404(Match, match_id=match_id)

        # Display the bets dependending on the time-type of each bet 
        response_data = {
            "half_time": None, 
            "full_time": None
        }
        for period in list(response_data.keys()): 
            # List and serialize handicap bet info for this time type
            info_list = HandicapBetInfo.objects.filter(
                match=match, 
                bet_object=bet_object, 
                period=PERIOD_MAP[period]).select_related("match", "match__home_team", "match__away_team")
            info_list_serializer = HandicapBetInfoSerizalizer(info_list, many=True)
            
            response_data[period] = self.group_handicap_info(
                info_list_serializer.data, match.home_team
            ) 
        return Response(response_data)


class TotalObjectsInfoList(APIView):
    """ View to list all of the total goals bet info of the match  """
    permission_classes = [AllowAny]
    
    def group_total_objects_info(
        self, info_list: QuerySet[TotalObjectsBetInfo]) -> List[Dict[str, Union[TotalObjectsBetInfo, None]]]:
        """
        Group the the total goals bet infos that have the same number.
        Returns the form ```[[under num1, over num1], [under num2, over num2], ...]```
        """
        # Dictionary mapping the number of objects to list of total bets info
        total_to_info_dict = {} 
        
        for info in info_list:
            num_objects = info["num_objects"]
            if num_objects not in total_to_info_dict: 
                # If this number of goals isn't already in dictionary, add it
                total_to_info_dict[num_objects] = {
                    "under": None, 
                    "over": None
                }
            # Place the bet info into the right place of the list 
            uoo = "under" if info["under_or_over"] == "Under" else "over"
            total_to_info_dict[num_objects][uoo] = info
                
        # Convert dictionary into the list of grouped bet info
        return list(total_to_info_dict.values())
    
    def get(self, request, match_id: int, format=None) -> Response: 
        bet_object = request.query_params.get("bet_object")
        if bet_object is None: 
            raise ValidationError({"error": "Bet object is not defined"})

        # List of total goals bet infos
        match = get_object_or_404(Match, match_id=match_id)

        response_data = {
            "half_time": None, 
            "full_time": None
        }
        for period in list(response_data.keys()): 
            # List of total goals bet info for this time type
            info_list = TotalObjectsBetInfo.objects.filter(
                match=match, 
                bet_object=bet_object, 
                period=PERIOD_MAP[period]).select_related("match", "match__home_team", "match__away_team")
            # Serialize data of the list 
            info_list_serializer = TotalObjectsBetInfoSerializer(info_list, many=True)
            response_data[period] = self.group_total_objects_info(
                info_list_serializer.data
            )
        return Response(response_data)
    
