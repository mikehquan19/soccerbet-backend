"""
VIEWS FOR USER'S BET LIST
NOTE: THE VIEWS HERE WILL BE ONLY ACCESSIBLE BY AUTHENTICATED USER,
    SO THEY WILL BE IMPLEMENTED PERMISSION CLASSES ISAUTHENTICATED 
"""
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from soccerapp.models import UserMoneylineBet, UserHandicapBet, UserTotalObjectsBet
from soccerapp.serializers import (
    UserSerializer, 
    UserMoneylineBetSerializer, UserHandicapBetSerializer, UserTotalObjectsBetSerializer
)
from soccerapp.serializers import CustomValidator
from decimal import Decimal

# the validator used to validate the DELETE method endpoint 
bet_validator = CustomValidator() 

# views to show detail of the user 
class UserDetail(generics.RetrieveAPIView): 
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user # get the user from the request


# views to list all of the moneyline bets and create new bet
class UserMoneylineBetList(APIView): 
    permission_classes = [IsAuthenticated]

    # the GET method 
    def get(self, request, format=None) -> Response: 
        status = request.query_params.get("status")
        # get the response data and return 
        if status is not None: 
            moneyline_bet_list = UserMoneylineBet.objects.filter(user=request.user, bet_info__status=status)
        else: 
            moneyline_bet_list = UserMoneylineBet.objects.filter(user=request.user)
        bet_list_serializer = UserMoneylineBetSerializer(moneyline_bet_list, many=True)
        return Response(bet_list_serializer.data)
    
    # the POST method 
    def post(self, request, format=None) -> Response: 
        request_data = request.data
        for item_data in request_data: item_data['user'] = request.user.pk # add the user field to request data

        new_bet_list_serializer = UserMoneylineBetSerializer(data=request_data, many=True)
        if new_bet_list_serializer.is_valid(): 
            with transaction.atomic(): # maintain the integrity of the data
                # save the new bet to the database 
                new_moneyline_bet, total_bet_amount = new_bet_list_serializer.save()

                # adjust the balance of the user after saving 
                bet_owner = request.user
                bet_owner.balance -= total_bet_amount
                bet_owner.save()
            # return the reserialized to ensure the returned data is complete
            return Response(UserMoneylineBetSerializer(new_moneyline_bet, many=True).data, status=status.HTTP_201_CREATED)
        # return errors if the data is invalid 
        return Response(new_bet_list_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# views to handle the detail of the moneyline bets with given pk 
class UserMoneylineBetDetail(APIView): 
    permission_classes = [AllowAny]

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
                bet_owner = updated_bet.user 
                bet_amount_difference = old_bet_amount - updated_bet.bet_amount
                bet_owner.balance += (bet_amount_difference * Decimal(1.05)) # include the extra fees for placing the bets
                bet_owner.save()
            # return the updated data
            return Response(updated_bet_serializer.data, status=status.HTTP_202_ACCEPTED)
        # return the errors 
        return Response(updated_bet_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # the DELETE method 
    def delete(self, request, pk, format=None) -> Response: 
        queried_moneyline_bet = get_object_or_404(UserMoneylineBet, pk=pk)
        bet_validator.validate_delete(queried_moneyline_bet) # validate if the instance (bet) is elligible for withdrawing

        with transaction.atomic(): 
            # return the amount the user bet back to the user
            bet_owner = queried_moneyline_bet.user 
            bet_owner.balance += queried_moneyline_bet.bet_amount * Decimal(1.05)
            bet_owner.save()
            
            # delete the monyeline bet from the database 
            queried_moneyline_bet.delete()
        return Response({"message": "Bet deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


""" 
Generics views will be used for the remaining 2 types of bet for easier life 
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
            bet_owner = self.request.user
            bet_owner.balance -= total_bet_amount
            bet_owner.save()
        return new_bet_list

    # override create() method (which will be used by every other bet list views)
    def create(self, request, *args, **kwargs) -> Response: 
        request_data = request.data
        for item_data in request_data: item_data['user'] = request.user.pk # add user field to request data

        new_bet_list_serializer = self.get_serializer(data=request_data, many=True)
        new_bet_list_serializer.is_valid(raise_exception=True) # automatically raise the exception

        # the queryset of newly added user bets 
        created_bet_list = self.perform_create(new_bet_list_serializer) 
        # return the response with the list 
        return Response(self.get_serializer(created_bet_list, many=True).data, status=status.HTTP_201_CREATED)
    

# views to list all of the user handicap bets (inheriting from UserBetList)
class UserHandicapBetList(UserBetList): 
    serializer_class = UserHandicapBetSerializer
    permission_classes = [IsAuthenticated]

    # the queryset (list of the user's handicap bets )
    def get_queryset(self): 
        status = self.request.query_params.get('status')
        if status is None: 
            handicap_bet_list = UserHandicapBet.objects.filter(user=self.request.user)
        else:
            handicap_bet_list = UserHandicapBet.objects.filter(user=self.request.user, bet_info__status=status)
        return handicap_bet_list
    

# views to list all of the user total goals bets (inheriting from UserBetList)
class UserTotalGoalsBetList(UserBetList): 
    serializer_class = UserTotalObjectsBetSerializer
    permission_classes = [IsAuthenticated]

    # the queryset (list of the user's total goals bets)
    def get_queryset(self):
        status = self.request.query_params.get("status")
        if status is None:  
            total_bet_list = UserTotalObjectsBet.objects.filter(user=self.request.user)
        else: 
            total_bet_list = UserTotalObjectsBet.objects.filter(user=self.request.user, bet_info__status=status)
        return total_bet_list
    

"""
Generic views for 2 other types of bet details 
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
            bet_owner = updated_bet.user 
            bet_amount_difference = old_bet_amount - updated_bet.bet_amount
            bet_owner.balance += bet_amount_difference * Decimal(1.05) # extra fees 
            bet_owner.save()
        return updated_bet

    # override the perform_destroy() method to give the amount the user bet back 
    def perform_destroy(self, instance): 
        bet_validator.validate_delete(instance) # validate if the instance (bet) is elligible for withdrawing
        with transaction.atomic(): 
            # return the amount the user bet back to the user
            bet_owner = instance.user 
            bet_owner.balance += instance.bet_amount * Decimal(1.05) # extra fees 
            bet_owner.save()
            # delete the monyeline bet from the database 
            instance.delete()
    

# view to handle the detail of the handicap bet (inheritting from UserBetDetail)
class UserHandicapBetDetail(UserBetDetail): 
    permission_classes = [IsAuthenticated]
    queryset = UserHandicapBet.objects.all() # queryset from which the bet will be queried using pk
    serializer_class = UserHandicapBetSerializer # the serializer 
    

# view to handle the detailf of the total goals bet (inheriting from UserBetDetail)
class UserTotalGoalsBetDetail(UserBetDetail): 
    permission_classes = [IsAuthenticated]
    queryset = UserTotalObjectsBet.objects.all()
    serializer_class = UserTotalObjectsBetSerializer