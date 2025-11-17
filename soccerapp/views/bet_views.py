"""
VIEWS FOR USER'S BET LIST
NOTE: 
THE VIEWS HERE WILL BE ONLY ACCESSIBLE BY AUTHENTICATED USER,
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
    UserMoneylineBetSerializer, 
    UserHandicapBetSerializer, 
    UserTotalObjectsBetSerializer
)
from soccerapp.serializers import CustomValidator
from decimal import Decimal

bet_validator = CustomValidator() 
""" The validator used to validate the DELETE method endpoint """

class UserDetail(generics.RetrieveAPIView): 
    """ View to show detail of the user  """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        """ Get the user from the request """
        return self.request.user


class UserMoneylineBetList(APIView): 
    """ View to list all of the moneyline bets and create new bet """
    permission_classes = [IsAuthenticated]
 
    def get(self, request, format=None) -> Response: 
        status = request.query_params.get("status")

        if status: 
            bet_list = UserMoneylineBet.objects.filter(user=request.user, bet_info__status=status)
        else: 
            bet_list = UserMoneylineBet.objects.filter(user=request.user)
        bet_list = bet_list.select_related(
            "bet_info", 
            "bet_info__match",
            "bet_info__match__home_team",
            "bet_info__match__away_team",
        )
        bet_list_serializer = UserMoneylineBetSerializer(bet_list, many=True)
        return Response(bet_list_serializer.data)
    
    def post(self, request, format=None) -> Response: 
        request_data = request.data
        # Add the user field to request data
        for data in request_data: data['user'] = request.user.id

        new_list_serializer = UserMoneylineBetSerializer(data=request_data, many=True)
        new_list_serializer.is_valid(raise_exception=True)
        # Maintain the integrity of the data
        with transaction.atomic():
            # save the new bet to the database 
            new_bet_list, total_bet_amount = new_list_serializer.save()

            # Adjust the balance of the user after saving 
            bet_owner = request.user
            bet_owner.balance -= total_bet_amount
            bet_owner.save()
            
        bet_list_serializer = UserMoneylineBetSerializer(new_bet_list, many=True)
        return Response(bet_list_serializer.data, status=status.HTTP_201_CREATED)


class UserMoneylineBetDetail(APIView): 
    """ View to handle the detail of the moneyline bets with given private key """
    permission_classes = [AllowAny]

    def get(self, request, pk: int, format=None) -> Response: 
        moneyline_bet = get_object_or_404(UserMoneylineBet, pk=pk)
        bet_serializer = UserMoneylineBetSerializer(moneyline_bet)
        return Response(bet_serializer.data)
    
    def put(self, request, pk: int, format=None) -> Response: 
        moneyline_bet = get_object_or_404(UserMoneylineBet, pk=pk)
        updated_bet_serializer = UserMoneylineBetSerializer(
            moneyline_bet, data=request.data
        )

        updated_bet_serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            # The old bet amount 
            old_bet_amount = moneyline_bet.bet_amount
            updated_bet = updated_bet_serializer.save()

            # Adjust the balance of the user 
            bet_owner = updated_bet.user 
            bet_amount_difference = old_bet_amount - updated_bet.bet_amount

            # Include the extra fees for placing the bets
            bet_owner.balance += bet_amount_difference * Decimal(1.05) 
            bet_owner.save()
            
        return Response(updated_bet_serializer.data, status=status.HTTP_202_ACCEPTED)
    
    def delete(self, request, pk: int, format=None) -> Response: 
        queried_moneyline_bet = get_object_or_404(UserMoneylineBet, pk=pk)
        # validate if the instance (bet) is elligible for withdrawing
        bet_validator.validate_delete(queried_moneyline_bet)

        with transaction.atomic(): 
            # return the amount the user bet back to the user
            bet_owner = queried_moneyline_bet.user 
            bet_owner.balance += queried_moneyline_bet.bet_amount * Decimal(1.05)
            bet_owner.save()
            
            # delete the monyeline bet from the database 
            queried_moneyline_bet.delete()
        return Response(
            {"message": "Bet deleted successfully."}, status=status.HTTP_204_NO_CONTENT
        )


class UserBetList(generics.ListCreateAPIView): 
    """ 
    Generics views for listing and creating of all types of view, which will be used 
    for the remaining 2 types of bet for easier life. 
    """

    queryset = None
    serializer_class = None

    def perform_create(self, serializer):
        """ Override ```perform_create()``` method to adjust the balance of the user  """
        with transaction.atomic(): 
            new_bet_list, total_bet_amount = serializer.save()
            # adjust the balance of the user 
            bet_owner = self.request.user
            bet_owner.balance -= total_bet_amount
            bet_owner.save()
            return new_bet_list

    def create(self, request, *args, **kwargs) -> Response: 
        """ Override ```create()``` method (which will be used by every other bet list views) """

        request_data = request.data
        # add user field to request data
        for item_data in request_data: 
            item_data['user'] = request.user.pk 

        new_bet_list_serializer = self.get_serializer(data=request_data, many=True)
        new_bet_list_serializer.is_valid(raise_exception=True)

        # The queryset of newly added user bets 
        created_bet_list = self.perform_create(new_bet_list_serializer) 
        
        # return the response with the list 
        return Response(
            self.get_serializer(created_bet_list, many=True).data, 
            status=status.HTTP_201_CREATED
        )
    

class UserHandicapBetList(UserBetList): 
    """ View to list all of the user handicap bets """
    serializer_class = UserHandicapBetSerializer
    permission_classes = [IsAuthenticated]

    # the queryset (list of the user's handicap bets )
    def get_queryset(self): 
        status = self.request.query_params.get('status')
        if not status: 
            handicap_bet_list = UserHandicapBet.objects.filter(user=self.request.user)
        else:
            handicap_bet_list = UserHandicapBet.objects.filter(
                user=self.request.user, bet_info__status=status)
        handicap_bet_list = handicap_bet_list.select_related(
            "bet_info", 
            "bet_info__match",
            "bet_info__match__home_team",
            "bet_info__match__away_team",
        )
        return handicap_bet_list
    

class UserTotalGoalsBetList(UserBetList): 
    """ View to list all of the user total goals bets """
    serializer_class = UserTotalObjectsBetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """ Get the queryset (list of the user's total goals bets) """
        status = self.request.query_params.get("status")
        if not status:  
            total_bet_list = UserTotalObjectsBet.objects.filter(user=self.request.user)
        else: 
            total_bet_list = UserTotalObjectsBet.objects.filter(
                user=self.request.user, bet_info__status=status)
        total_bet_list = total_bet_list.select_related(
            "bet_info", 
            "bet_info__match",
            "bet_info__match__home_team",
            "bet_info__match__away_team",
        )
        return total_bet_list
    

class UserBetDetail(generics.RetrieveUpdateDestroyAPIView): 
    """ Generic views for handling the detail of view of all types of view """

    queryset = None
    serializer_class = None

    def perform_update(self, serializer):
        """ Override ```perform_update()``` to update the dedecuted amount  """

        with transaction.atomic(): 
            old_bet_amount = self.get_object().bet_amount
            updated_bet = serializer.save() # call method update()

            # adjust the balance of the user 
            bet_owner = updated_bet.user 
            bet_amount_difference = old_bet_amount - updated_bet.bet_amount
            bet_owner.balance += bet_amount_difference * Decimal(1.05) 
            bet_owner.save()
        return updated_bet

    def perform_destroy(self, instance): 
        """ Override ```perform_destroy()``` to give back the bet amount """

        # validate if the instance (bet) is elligible for withdrawing
        bet_validator.validate_delete(instance) 
        with transaction.atomic(): 
            # return the amount the user bet back to the user
            bet_owner = instance.user 
            bet_owner.balance += instance.bet_amount * Decimal(1.05)  
            bet_owner.save()

            # delete the monyeline bet from the database 
            instance.delete()
    

class UserHandicapBetDetail(UserBetDetail): 
    """ Handling the detail of the handicap bet """
    permission_classes = [IsAuthenticated]
    queryset = UserHandicapBet.objects.all() 
    serializer_class = UserHandicapBetSerializer # the serializer 
    

class UserTotalGoalsBetDetail(UserBetDetail): 
    """ Handling the detailf of the total goals bet """
    permission_classes = [IsAuthenticated]
    queryset = UserTotalObjectsBet.objects.all()
    serializer_class = UserTotalObjectsBetSerializer