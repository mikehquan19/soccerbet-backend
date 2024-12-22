"""
SERIALIZERS FOR THE USER BETS AND LIST OF THEM 
"""

from rest_framework import serializers
from django.db import transaction
from soccerapp.models import (
    MoneylineBetInfo, HandicapBetInfo, TotalObjectsBetInfo,
    UserMoneylineBet, UserHandicapBet, UserTotalObjectsBet,
)
from . import MoneylineBetInfoSerializer, HandicapBetInfoSerizalizer, TotalObjectsBetInfoSerializer
from .serializer_utils import * 


# the list serializer to handle the list of UserMoneylineBet objects
# used by UserMoneylineBetSerializer
class MoneylineBetListSerializer(serializers.ListSerializer): 
    # create the list of UserMoneylineBet objects 
    def create(self, validated_data): 
        # moneyline_bet_list: the list of moneyline bets to be saved to database
        moneyline_data_list, total_bet_amount = validate_create_data(MoneylineBetInfo, UserMoneylineBet, validated_data)
    
        # save these moneyline bets to the user 
        # maintain the integrity of the data 
        with transaction.atomic(): 
            moneyline_bet_list = UserMoneylineBet.objects.bulk_create(moneyline_data_list)
        # return the list and total bet amount 
        return moneyline_bet_list, total_bet_amount
    

# serializer of the user moneyline bets
class UserMoneylineBetSerializer(serializers.ModelSerializer): 
    class Meta: 
        # the list serializer to cutomize the creationt of multiple objects 
        list_serializer_class = MoneylineBetListSerializer 
        model = UserMoneylineBet
        fields = '__all__'
    # the bet info will be in the form of nested json
    bet_info = MoneylineBetInfoSerializer()

    # update the bet amount of the UserMoneylineBet object (other fields not allowed)
    def update(self, instance, validated_data): 
        # validate the data to be updated 
        validate_update_data(MoneylineBetInfo, instance, validated_data)
        
        # update the bet amount (if any) of the bet 
        instance.bet_amount = validated_data["bet_amount"]
        instance.save()
        return instance
    
    # the representation of the bet in the json data
    def to_representation(self, instance):
        bet_representation = super().to_representation(instance)
        bet_representation["username"] = instance.user.username
        return bet_representation
    

# serializer for the list of handicap bets 
# used by UserHandicapBetSerializer 
class HandicapBetListSerializer(serializers.ListSerializer): 
    # create the list of UserHandicapBet objects 
    def create(self, validated_data): 
        # handicap_data_list: the list of handicap bets to be saved to database
        total_bet_amount, handicap_data_list = validate_create_data(HandicapBetInfo, UserHandicapBet, validated_data)

        # save this handicap bet to the user 
        # maintain the integrity of the data 
        with transaction.atomic(): 
            handicap_bet_list = UserHandicapBet.objects.bulk_create(handicap_data_list)
        # return the new list and total amount of bet 
        return handicap_bet_list, total_bet_amount


# serializer of the handicap bet
class UserHandicapBetSerializer(serializers.ModelSerializer): 
    class Meta: 
        list_serializer_class = HandicapBetListSerializer
        model = UserHandicapBet
        fields = '__all__'
    bet_info = HandicapBetInfoSerizalizer()

    # update the UserHandicapBet object 
    def update(self, instance, validated_data): 
        # validate the data to be updated 
        validate_update_data(HandicapBetInfo, instance, validated_data)
        
        # update the bet amount (if any) of the bet 
        instance.bet_amount = validated_data["bet_amount"]
        instance.save()
        return instance
    
    # the representation of the bet in the json data
    def to_representation(self, instance):
        bet_representation = super().to_representation(instance)
        bet_representation["username"] = instance.user.username
        return bet_representation
    

# serializer to handle the list of UserTotalGoalsBet objects 
# used by UserTotalGoalsSerializer 
class TotalObjectsBetListSerializer(serializers.ListSerializer): 
    # handle the creation of multiple UserTotalGoalsBet 
    def create(self, validated_data): 
        # validate the data to be added 
        total_bet_amount, objects_data_list = validate_create_data(TotalObjectsBetInfo, UserTotalObjectsBet, validated_data)
        
        # save this handicap bet to the user
        # maintain the integrity of the data 
        with transaction.atomic(): 
            objects_bet_list = UserTotalObjectsBet.objects.bulk_create(objects_data_list)
        # return the new list and total amount of bet 
        return objects_bet_list, total_bet_amount


# serializer of the total goals bet
class UserTotalObjectsBetSerializer(serializers.ModelSerializer): 
    class Meta: 
        list_serializer_class = TotalObjectsBetListSerializer
        model = UserTotalObjectsBet
        fields = '__all__' 
    bet_info = TotalObjectsBetInfoSerializer()
    
    # update the UserTotalGoals object 
    def update(self, instance, validated_data): 
        # validate the data to be updated 
        validate_update_data(TotalObjectsBetInfo, instance, validated_data)
        
        # update the bet amount (if any) of the bet 
        instance.bet_amount = validated_data["bet_amount"]
        instance.save()
        return instance
    
    # the representation of the bet in the json data
    def to_representation(self, instance):
        bet_representation = super().to_representation(instance)
        bet_representation["username"] = instance.user.username
        return bet_representation

