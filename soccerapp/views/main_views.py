from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from soccerapp.models import (
    Match, Team, 
    MoneylineBetInfo, HandicapBetInfo, TotalGoalsBetInfo,
)
from soccerapp.serializers import (
    MatchSerializer, TeamSerializer,
    MoneylineBetInfoSerializer, HandicapBetInfoSerizalizer, TotalGoalsBetInfoSerializer,
)

"""
ALL OF THE VIEWS IN HERE HAVE PERMISSION ALLOWANY, AND ARE ACCESSIBLE TO ANY END USERS
"""
# mapping the value of request parameter to the value of the database 
LEAGUES_NAME_MAP = {
    "ucl": "Champions League", 
    "epl": "Premiere League", 
    "lal": "La Liga", 
    "bun": "Bundesliga"
}

# mapping the different format for time type 
TIME_TYPE_MAP = {"half_time": "half time", "full_time": "full time"}

# view to list all of the team according to the league 
@api_view(["GET"])
@permission_classes([AllowAny])
def team_list(request, league: str) -> Response: 
    if request.method == "GET": 
        # get the list of teams of the league
        team_list = Team.objects.filter(league=LEAGUES_NAME_MAP[league])
        team_list_serizalizer = TeamSerializer(team_list, many=True)
        return Response(team_list_serizalizer.data)


# view to list all of the matches according to the league
@api_view(["GET"])
@permission_classes([AllowAny])
def match_list(request, league: str, status: str) -> Response: 
    status_map = {
        "NF": "Not Finished", 
        "FN": "Finished"
    }
    if request.method == "GET": 
        # get the list of matches depending on the league parameter 
        if league == "all": 
            match_list = Match.objects.filter(status=status_map[status])
        else: 
            match_list = Match.objects.filter(
                league=LEAGUES_NAME_MAP[league], 
                status=status_map[status]
            )
        match_list_serializer = MatchSerializer(match_list, many=True)
        return Response(match_list_serializer.data)
    

# TODO: complete this views 
# view to handle the rankings of the league
@api_view(["GET"])
@permission_classes([AllowAny])
def rankings(request, league: str) -> Response: 
    if request.method == "GET": 
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
"""
VIEWS FOR BET INFO
"""

# view to list all of the moneyline bet info of the match with given match id
@api_view(["GET"])
@permission_classes([AllowAny])
def moneyline_info_list(request, match_id) -> Response: 
    if request.method == "GET": 
        # list of moneyline bets 
        match = get_object_or_404(Match, match_id=match_id)
        moneyline_info_list = MoneylineBetInfo.objects.filter(match=match)

        # list of moneyline bet info for half-time and fulltime
        response_data = {"half_time": None, "full_time": None}
        for time_type in list(response_data.keys()): 
            # list of moneyline bet info for this time type 
            type_moneyline_list = moneyline_info_list.filter(time_type=TIME_TYPE_MAP[time_type])
            # serializer 
            type_moneyline_data = MoneylineBetInfoSerializer(type_moneyline_list, many=True).data
            response_data[time_type] = type_moneyline_data
        return Response(response_data)


# view to list all of the handicap bet info of the match 
class HandicapInfoList(APIView):
    permission_classes = [AllowAny]

    # group the handicap bet info that correspond to each other together
    # the form [[Home1 -cover, Draw cover, Away1 cover], [Home2 -cover, Draw cover, Away2 cover], ...]
    def group_handicap_info(self, handicap_info_list: list, home_team: str) -> list: 
        # the dictionary mapping the cover to the correponding list of handicap info
        cover_to_handicap_list = {}
        for handicap_info in handicap_info_list: 
            # the handicap cover of this item data 
            if handicap_info["bet_team"] == home_team: 
                this_cover = float(handicap_info["handicap_cover"])
            else: 
                this_cover = -float(handicap_info["handicap_cover"])

            # if this handicap cover isn't already in the list, add them 
            if this_cover not in cover_to_handicap_list: 
                cover_to_handicap_list[this_cover] = [None, None]

            # put the handicap bet info into the right place of the list 
            if handicap_info["bet_team"] == home_team: 
                cover_to_handicap_list[this_cover][0] = handicap_info
            else: 
                cover_to_handicap_list[this_cover][1] = handicap_info

        # conver the dictionary to the list 
        grouped_info_list = [grouped_info for grouped_info in list(cover_to_handicap_list.values())]
        # return the rearranged list of data 
        return grouped_info_list
    
    # GET method of the request 
    def get(self, request, match_id, format=None) -> Response: 
        # the list of handicap bets 
        match = get_object_or_404(Match, match_id=match_id)
        handicap_info_list = HandicapBetInfo.objects.filter(match=match)

        # display the bets dependending on the time-type of each bet 
        response_data = {"half_time": None, "full_time": None}
        for time_type in list(response_data.keys()): 
            # list of handicap bet info for this time type
            type_handicap_list = handicap_info_list.filter(time_type=TIME_TYPE_MAP[time_type])
            # serialize and then regroup the records of the data 
            type_handicap_data = HandicapBetInfoSerizalizer(type_handicap_list, many=True).data
            response_data[time_type] = self.group_handicap_info(type_handicap_data, match.home_team)
            # response_data[time_type] = type_handicap_data # for testing 
        # return the response data
        return Response(response_data)


# views to list all of the total goals bet info of the match 
class TotalGoalsInfoList(APIView):
    permission_classes = [AllowAny]

    # group the the total goals bet infos that have the same number of target goals 
    # the form [[Under num_goals1, Over num_goals1], [Under num_goals2, Over num_goals2], ...]
    def group_total_goals_info(self, total_goals_info_list: list) -> list: 
        # dict mapping the target number of goals available to corresponding list of bets 
        goals_to_info_list = {}
        for total_goals_info in total_goals_info_list: 
            # the target number of goals 
            target_num_goals = total_goals_info["target_num_goals"]

            # if this number of goals isn't already in dict, add them
            if target_num_goals not in goals_to_info_list: 
                goals_to_info_list[target_num_goals] = [None, None]

            # put the total-goals bet info into the right place of the list 
            if total_goals_info["under_or_over"] == "Under": 
                goals_to_info_list[target_num_goals][0] = total_goals_info
            else: 
                goals_to_info_list[target_num_goals][1] = total_goals_info
                
        # convert dictionary into the list of grouped bet info
        grouped_info_list = [grouped_info for grouped_info in list(goals_to_info_list.values())]
        return grouped_info_list
    
    # GET method of the request 
    def get(self, request, match_id, format=None) -> Response: 
        # get the list of total goals bet infos
        match = get_object_or_404(Match, match_id=match_id)
        total_goals_info_list = TotalGoalsBetInfo.objects.filter(match=match)
        
        # the response data
        response_data = {"half_time": None, "full_time": None}
        for time_type in list(response_data.keys()): 
            # list of total goals bet info for this time type
            type_total_goals_list = total_goals_info_list.filter(time_type=TIME_TYPE_MAP[time_type])
            # serialized data of the list 
            type_total_goals_data = TotalGoalsBetInfoSerializer(type_total_goals_list, many=True).data
            response_data[time_type] = self.group_total_goals_info(type_total_goals_data)
            # response_data[time_type] = type_total_goals_data # for testing 
        return Response(response_data)
    