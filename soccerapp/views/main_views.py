"""
ALL OF THE VIEWS IN HERE HAVE PERMISSION ALLOWANY, AND ARE ACCESSIBLE TO ANY END USERS
"""

from django.shortcuts import get_object_or_404
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

LEAGUES_NAME_MAP = {
    "ucl": "Champions League", 
    "epl": "Premiere League", 
    "lal": "La Liga", 
    "bun": "Bundesliga"
}
""" Mapping the value of request parameter to the value of the database  """

TIME_TYPE_MAP = {
    "half_time": "half time", 
    "full_time": "full time"
}
""" Mapping the different format for time type """

class Login(TokenObtainPairView): 
    """ View to handle the user login """

    permission_classes = [AllowAny]
    serializer_class = MyTokenObtainPairSerializer


class Register(generics.CreateAPIView): 
    """ View to handle the user register  """

    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class TeamList(APIView): 
    """ View to list all of the team according to the league  """

    permission_classes = [AllowAny]

    def get(self, request, format=None) -> Response: 
        league_name = request.query_params.get("league")
        if league_name is None: raise ValidationError({ "error": "League not specified" })

        # get the list of teams of the league
        team_list = Team.objects.filter(league=LEAGUES_NAME_MAP[league_name])
        team_list_serizalizer = TeamSerializer(team_list, many=True)
        return Response(team_list_serizalizer.data)
    

class TeamDetail(generics.RetrieveAPIView): 
    permission_classes = [AllowAny]
    queryset = Team.objects.all() 
    serializer_class = TeamSerializer


class MatchList(APIView): 
    """ View to list all of the matches according to the league """
    permission_classes = [AllowAny]

    def get(self, request, format=None) -> Response: 
        status_map = {"NF": "Not Finished", "FN": "Finished"}
        league = request.query_params.get("league")
        status = request.query_params.get("status")

        # status = None is not allowed for this endpoint 
        if status is None: raise ValidationError({ "error": "Status is not defined" })
        
        if league is None: 
            match_list = Match.objects.filter(status=status_map[status])
        else: 
            match_list = Match.objects.filter(
                league=LEAGUES_NAME_MAP[league], status=status_map[status]
            )
        match_list_serializer = MatchSerializer(match_list, many=True)
        return Response(match_list_serializer.data)
    

class MatchDetail(generics.RetrieveAPIView): 
    permission_classes = [AllowAny]
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    lookup_field = "match_id"


class Standings(APIView): 
    """ View to handle the rankings of the league """

    permission_classes = [AllowAny]

    def get(self, request) -> Response: 
        league_name = request.query_params.get("league")
        if not league_name: raise ValidationError({"error": "League not specified"})

        standings = TeamRanking.objects.filter(league=LEAGUES_NAME_MAP[league_name])
        standings_serializer = TeamRankingSerializer(standings, many=True)
        return Response(standings_serializer.data)
     

""" VIEWS FOR BET INFO """

class MoneylineInfoList(APIView): 
    """ View to list all of the moneyline bet info of the match with given match id """

    permission_classes = [AllowAny]

    def get(self, request, match_id: int, format=None) -> Response: 
        bet_obj = request.query_params.get("bet_obj")
        if bet_obj is None: raise ValidationError({"error": "Bet obj is not defined"})
        
        # list of moneyline bets 
        queried_match = get_object_or_404(Match, match_id=match_id)
        moneyline_info_list = MoneylineBetInfo.objects.filter(match=queried_match, bet_object=bet_obj)

        # list of moneyline bet info for half-time and fulltime
        response_data = {
            "half_time": None, 
            "full_time": None
        }
        for time_type in list(response_data.keys()): 
            # list of moneyline bet info for this time type 
            type_moneyline_list = moneyline_info_list.filter(time_type=TIME_TYPE_MAP[time_type])
            type_moneyline_data = MoneylineBetInfoSerializer(type_moneyline_list, many=True).data
            response_data[time_type] = type_moneyline_data

        return Response(response_data)
    

class HandicapInfoList(APIView):
    """ View to list all of the handicap bet info of the match  """

    permission_classes = [AllowAny]
    
    def group_handicap_info(self, handicap_info_list: list, home_team: str) -> list: 
        """
        Group the handicap bet info that correspond to each other together.

        the form ```[[home1 -cover, away1 cover], [home2 -cover, away2 cover], ...]```
        """

        # Dict mapping the cover to the list of handicap info
        cover_to_info = {} 

        for handicap_info in handicap_info_list: 
            # the handicap cover of this item data 
            cover = -float(handicap_info["handicap_cover"])
            if handicap_info["bet_team"] == home_team: 
                cover = float(handicap_info["handicap_cover"])

            # if this handicap cover isn't already in the list, add them 
            if cover not in cover_to_info: 
                cover_to_info[cover] = {
                    "home": None, 
                    "away": None
                }
            # put the handicap bet info into the right place of the list 
            if handicap_info["bet_team"] == home_team: 
                cover_to_info[cover]["home"] = handicap_info
            else: 
                cover_to_info[cover]["away"] = handicap_info

        # conver the dictionary to the list 
        grouped_info_list = [info for info in list(cover_to_info.values())]

        # return the rearranged list of data 
        return grouped_info_list
    
    def get(self, request, match_id: int, format=None) -> Response: 
        bet_obj = request.query_params.get("bet_obj")
        if bet_obj is None: raise ValidationError({"error": "Bet obj is not defined"})

        # the list of handicap bets 
        queried_match = get_object_or_404(Match, match_id=match_id)
        handicap_info_list = HandicapBetInfo.objects.filter(
            match=queried_match, bet_object=bet_obj)

        # display the bets dependending on the time-type of each bet 
        response_data = {
            "half_time": None, 
            "full_time": None
        }
        for time_type in list(response_data.keys()): 
            # list and serialize handicap bet info for this time type
            type_handicap_list = handicap_info_list.filter(
                time_type=TIME_TYPE_MAP[time_type]
            )
            type_handicap_data = HandicapBetInfoSerizalizer(type_handicap_list, many=True).data
            
            response_data[time_type] = self.group_handicap_info(
                type_handicap_data, queried_match.home_team
            ) 
        return Response(response_data)


class TotalObjectsInfoList(APIView):
    """ View to list all of the total goals bet info of the match  """

    permission_classes = [AllowAny]
    
    def group_total_objects_info(self, total_objs_info_list: list) -> list:
        """
        Group the the total goals bet infos that have the same number of target goals.

        the form ```[[under num_goals1, over num_goals1], [under num_goals2, over num_goals2], ...]```
        """

        num_to_info = {}  # dict mapping the target number of objects to list of total bets 
        
        for total_objs_info in total_objs_info_list:
            # the target number of goals 
            target_num_objs = total_objs_info["target_num_objects"]

            # if this number of goals isn't already in dict, add them
            if target_num_objs not in num_to_info: 
                num_to_info[target_num_objs] = {
                    "under": None, 
                    "over": None
                }
            # place the total-goals bet info into the right place of the list 
            if total_objs_info["under_or_over"] == "Under": 
                num_to_info[target_num_objs]["under"] = total_objs_info
            else: 
                num_to_info[target_num_objs]["over"] = total_objs_info
                
        # convert dictionary into the list of grouped bet info
        grouped_info_list = [info for info in list(num_to_info.values())]
        return grouped_info_list
     
    def get(self, request, match_id: int, format=None) -> Response: 
        bet_obj = request.query_params.get("bet_obj")
        if bet_obj is None: raise ValidationError({"error": "Bet obj is not defined"})

        # get the list of total goals bet infos
        queried_match = get_object_or_404(Match, match_id=match_id)
        objs_info_list = TotalObjectsBetInfo.objects.filter(
            match=queried_match, bet_object=bet_obj
        )

        # the custom response data
        response_data = {
            "half_time": None, 
            "full_time": None
        }
        for time_type in list(response_data.keys()): 
            # list of total goals bet info for this time type
            type_objs_list = objs_info_list.filter(time_type=TIME_TYPE_MAP[time_type])

            # serialized data of the list 
            type_objs_data = TotalObjectsBetInfoSerializer(
                type_objs_list, many=True
            ).data
            response_data[time_type] = self.group_total_objects_info(type_objs_data)
        return Response(response_data)
    
