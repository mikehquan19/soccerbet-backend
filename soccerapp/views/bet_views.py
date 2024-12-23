"""
VIEWS FOR USER'S BET LIST
NOTE: THE VIEWS HERE WILL BE ONLY ACCESSIBLE BY AUTHENTICATED USER,
    SO THEY WILL BE IMPLEMENTED PERMISSION CLASSES ISAUTHENTICATED 
"""

from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from soccerapp.models import User, UserMoneylineBet, UserHandicapBet, UserTotalObjectsBet
from soccerapp.serializers import (
    UserSerializer,
    UserMoneylineBetSerializer, UserHandicapBetSerializer, UserTotalObjectsBetSerializer
)

# views to show detail of the user 
class UserDetail(generics.RetrieveAPIView): 
    queryset = User.objects.all()
    serializer_class = UserSerializer


# views to list all of the moneyline bets and create new bet
class UserMoneylineBetList(APIView): 
    # get the response data (list of moneyline bet of the given user)
    def get_response_data(self, user_id) -> list: 
        queried_user = get_object_or_404(User, id=user_id)
        moneyline_bet_list = UserMoneylineBet.objects.filter(user=queried_user)
        bet_list_serializer = UserMoneylineBetSerializer(moneyline_bet_list, many=True)
        return bet_list_serializer.data

    # the GET method 
    def get(self, request, user_id, format=None) -> Response: 
        moneyline_bet_data = self.get_response_data(user_id)
        return Response(moneyline_bet_data)
    
    # the POST method 
    def post(self, request, user_id, format=None) -> Response: 
        request_data = request.data
        for item_data in request_data: item_data["user"] = user_id

        new_bet_serializer = UserMoneylineBetSerializer(data=request_data, many=True)
        if new_bet_serializer.is_valid(): 
            with transaction.atomic(): # maintain the integrity of the data
                # save the new bet to the database 
                _, total_bet_amount = new_bet_serializer.save() 
                # adjust the balance of the user after saving 
                queried_user = get_object_or_404(User, id=user_id)
                queried_user.balance -= total_bet_amount
                queried_user.save()

            # return the new list of bets (in which the new bets have been added)
            new_moneyline_bet_data = self.get_response_data(user_id)
            return Response(new_moneyline_bet_data, status=status.HTTP_201_CREATED)
        # return errors if the data is invalid 
        return Response(new_bet_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# views to handle the detail of the moneyline bets with given pk 
class UserMoneylineBetDetail(APIView): 
    # the GET method 
    def get(self, request, pk, format=None) -> Response: 
        queried_moneyline_bet = get_object_or_404(UserMoneylineBet, pk=pk)
        bet_serializer = UserMoneylineBetSerializer(queried_moneyline_bet)
        return Response(bet_serializer.data)
    
    # the PUT method 
    def put(self, request, pk, format=None) -> Response: 
        queried_moneyline_bet = get_object_or_404(UserMoneylineBet, pk=pk)
        updated_bet_serializer = UserMoneylineBetSerializer(queried_moneyline_bet, data=request.data)
        if updated_bet_serializer.is_valid(): 
            with transaction.atomic(): # maintain integrity 
                # the old bet amount 
                old_bet_amount = queried_moneyline_bet.bet_amount
                updated_bet = updated_bet_serializer.save()

                # adjust the balance of the user 
                queried_user = updated_bet.user 
                bet_amount_difference = old_bet_amount - updated_bet.bet_amount
                queried_user.balance += bet_amount_difference
                queried_user.save()

            # return the updated data
            return Response(updated_bet_serializer.data, status=status.HTTP_202_ACCEPTED)
        # return the errors 
        return Response(updated_bet_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # the DELETE method 
    def delete(self, request, pk, format=None) -> Response: 
        queried_moneyline_bet = get_object_or_404(UserMoneylineBet, pk=pk)
        with transaction.atomic(): 
            # return the amount the user bet back to the user
            this_user = queried_moneyline_bet.user 
            this_user.balance += queried_moneyline_bet.bet_amount 
            this_user.save()

            # delete the monyeline bet from the database 
            queried_moneyline_bet.delete()
        return Response({"message": "Bet deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


""" 
generics views will be used for the remaining 2 types of bet for easier life 
""" 
# base views for listing and creating of all types of view
class UserBetList(generics.ListCreateAPIView): 
    queryset = None
    serializer_class = None

    # override perform_create() method to adjust the balance of the user 
    def perform_create(self, serializer):
        with transaction.atomic(): 
            new_bet_list, total_bet_amount = serializer.save()
            # adjust the balance of the user 
            queried_user = get_object_or_404(User, id=self.kwargs["user_id"])
            queried_user.balance -= total_bet_amount
            queried_user.save()
        return new_bet_list

    # override create() method (which will be used by every other bet list views)
    def create(self, request, **kwargs) -> Response: 
        request_data = request.data
        for item_data in request_data: item_data["user"] = self.kwargs["user_id"]

        new_bet_list_serializer = self.get_serializer(data=request_data, many=True)
        # automatically raise the exception
        new_bet_list_serializer.is_valid(raise_exception=True) 
        self.perform_create(new_bet_list_serializer) # create the bet

        # query the list in which new moneyline bet has been added 
        new_moneyline_bet_list = self.get_queryset()
        new_list_serializer = self.get_serializer(new_moneyline_bet_list, many=True)
        # return the response with the list 
        return Response(new_list_serializer.data, status=status.HTTP_201_CREATED)
    

# views to list all of the user handicap bets (inheriting from UserBetList)
class UserHandicapBetList(UserBetList): 
    serializer_class = UserHandicapBetSerializer

    # the queryset (list of the user's handicap bets )
    def get_queryset(self): 
        queried_user = get_object_or_404(User, id=self.kwargs["user_id"])
        handicap_bet_list = UserHandicapBet.objects.filter(user=queried_user)
        return handicap_bet_list
    

# views to list all of the user total goals bets (inheriting from UserBetList)
class UserTotalGoalsBetList(UserBetList): 
    serializer_class = UserTotalObjectsBetSerializer

    # the queryset (list of the user's total goals bets)
    def get_queryset(self):
        queried_user = get_object_or_404(User, id=self.kwargs["user_id"])
        total_goals_bet_list = UserTotalObjectsBet.objects.filter(user=queried_user)
        return total_goals_bet_list
    

"""
generic views for 2 other types of bet details 
"""
# common views for handling the detail of view of all types of view
class UserBetDetail(generics.RetrieveUpdateDestroyAPIView): 
    queryset = None
    serializer_class = None

    # override the perform_update() method to update the amount user's balance is deducted
    def perform_update(self, serializer):
        with transaction.atomic(): 
            old_bet_amount = self.get_object().bet_amount
            # update the bet's info
            updated_bet = serializer.save()

            # adjust the balance of the user 
            queried_user = updated_bet.user 
            bet_amount_difference = old_bet_amount - updated_bet.bet_amount
            queried_user.balance += bet_amount_difference
            queried_user.save()
        return updated_bet

    # override the perform_destroy() method to give the amount the user bet back 
    def perform_destroy(self, instance): 
        with transaction.atomic(): 
            # return the amount the user bet back to the user
            this_user = instance.user 
            this_user.balance += instance.bet_amount 
            this_user.save()
            # delete the monyeline bet from the database 
            instance.delete()
    

# view to handle the detail of the handicap bet (inheritting from UserBetDetail)
class UserHandicapBetDetail(UserBetDetail): 
    queryset = UserHandicapBet.objects.all() # queryset from which the bet will be queried using pk
    serializer_class = UserHandicapBetSerializer # the serializer 
    

# view to handle the detailf of the total goals bet (inheriting from UserBetDetail)
class UserTotalGoalsBetDetail(UserBetDetail): 
    queryset = UserTotalObjectsBet.objects.all()
    serializer_class = UserHandicapBetSerializer