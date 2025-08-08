"""
SERIALIZERS FOR THE USER BETS AND LIST OF THEM 
"""

from rest_framework import serializers
from django.db import transaction
from soccerapp.models import (
    MoneylineBetInfo, HandicapBetInfo, TotalObjectsBetInfo,
    UserMoneylineBet, UserHandicapBet, UserTotalObjectsBet,
)
from . import (
    MoneylineBetInfoSerializer, 
    HandicapBetInfoSerizalizer, 
    TotalObjectsBetInfoSerializer)
from .validator import CustomValidator

moneyline_validator = CustomValidator(MoneylineBetInfo, UserMoneylineBet)
""" Custom validator for moneyline bet  """

class MoneylineBetListSerializer(serializers.ListSerializer): 
    """
    The list serializer to handle the list of UserMoneylineBet objects
    used by ```UserMoneylineBetSerializer```
    """

    def create(self, validated_data): 
        """ Create the list of ```UserMoneylineBet``` objects  """

        # ```moneyline_data_list```: the list of moneyline bets to be saved to database
        moneyline_data_list, total_bet_amount = moneyline_validator.validate_create(validated_data)
    
        # save these moneyline bets to the user, maintain the integrity of the data 
        with transaction.atomic(): 
            moneyline_bet_list = UserMoneylineBet.objects.bulk_create(moneyline_data_list)
            
        # return the list and total bet amount 
        return moneyline_bet_list, total_bet_amount
    

class UserMoneylineBetSerializer(serializers.ModelSerializer):
    """ Serializer of the user moneyline bets """

    class Meta: 
        """ The list serializer to cutomize the creation of multiple objects """
        list_serializer_class = MoneylineBetListSerializer 
        model = UserMoneylineBet
        fields = '__all__'

    # the bet info will be in the form of nested json
    bet_info = MoneylineBetInfoSerializer()

    def update(self, instance, validated_data): 
        """ Update the bet amount of the UserMoneylineBet object (other fields not allowed) """

        # validate the data to be updated 
        moneyline_validator.validate_update(instance, validated_data)
        
        # update the bet amount (if any) of the bet 
        instance.bet_amount = validated_data["bet_amount"]
        instance.save()
        return instance
    
    def to_representation(self, instance):
        bet_representation = super().to_representation(instance)
        bet_representation["username"] = instance.user.username
        return bet_representation


handicap_validator = CustomValidator(HandicapBetInfo, UserHandicapBet)
""" Custom validator for handicap bet """

class HandicapBetListSerializer(serializers.ListSerializer): 
    """ Serializer for the list of handicap bets used by ```UserHandicapBetSerializer``` """

    def create(self, validated_data): 
        """ Create the list of ```UserHandicapBet``` objects  """

        # handicap_data_list: the list of handicap bets to be saved to database
        handicap_data_list, total_bet_amount = handicap_validator.validate_create(validated_data)

        # save this handicap bet to the user and maintain the integrity of the data 
        with transaction.atomic(): 
            handicap_bet_list = UserHandicapBet.objects.bulk_create(handicap_data_list)

        # return the new list and total amount of bet 
        return handicap_bet_list, total_bet_amount


class UserHandicapBetSerializer(serializers.ModelSerializer): 
    """ Serializer of the handicap bet """
    class Meta: 
        list_serializer_class = HandicapBetListSerializer
        model = UserHandicapBet
        fields = '__all__'
    bet_info = HandicapBetInfoSerizalizer()
 
    def update(self, instance, validated_data): 
        # validate the data to be updated 
        handicap_validator.validate_update(instance, validated_data)

        # update the bet amount (if any) of the bet 
        instance.bet_amount = validated_data["bet_amount"]
        instance.save()
        return instance
    
    def to_representation(self, instance):
        bet_representation = super().to_representation(instance)
        bet_representation["username"] = instance.user.username
        return bet_representation


total_objs_validator = CustomValidator(TotalObjectsBetInfo, UserTotalObjectsBet)
""" Custom validator for total objects bet """

class TotalObjectsBetListSerializer(serializers.ListSerializer): 
    """ 
    Serializer to handle the list of ```UserTotalGoalsBet``` objects used by ```UserTotalGoalsSerializer```
    """

    def create(self, validated_data):
        """ Handle the creation of multiple ```UserTotalGoalsBet``` """

        # validate the data to be added 
        objects_data_list, total_bet_amount = total_objs_validator.validate_create(validated_data)
        
        # save this handicap bet to the user and maintain the integrity of the data 
        with transaction.atomic(): 
            objects_bet_list = UserTotalObjectsBet.objects.bulk_create(objects_data_list)

        # return the new list and total amount of bet 
        return objects_bet_list, total_bet_amount


class UserTotalObjectsBetSerializer(serializers.ModelSerializer): 
    """ Serializer of the total goals bet """
    class Meta: 
        list_serializer_class = TotalObjectsBetListSerializer
        model = UserTotalObjectsBet
        fields = '__all__' 
    bet_info = TotalObjectsBetInfoSerializer()
    
    def update(self, instance, validated_data): 
        # validate the data to be updated 
        total_objs_validator.validate_update(instance, validated_data)
        
        # update the bet amount (if any) of the bet 
        instance.bet_amount = validated_data["bet_amount"]
        instance.save()
        return instance
    
    def to_representation(self, instance):
        bet_representation = super().to_representation(instance)
        bet_representation["username"] = instance.user.username
        return bet_representation

