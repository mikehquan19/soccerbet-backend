from rest_framework import serializers
from rest_framework.serializers import ValidationError as DRFValidationError
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from soccerapp.models import HandicapBetInfo, UserHandicapBet
from . import HandicapBetInfoSerizalizer


# serializer for the list of handicap bets 
# used by UserHandicapBetSerializer 
class HandicapBetListSerializer(serializers.ListSerializer): 
    # create the list of UserHandicapBet objects 
    def create(self, validated_data): 
        total_bet_amount = 0
        handicap_data_list = [] # list of handicap bets to be saved 

        for i, item_data in enumerate(validated_data): 
            this_user = item_data["user"]
            handicap_bet_info_data = item_data.pop("bet_info")
            handicap_bet_info = HandicapBetInfo.objects.get(**handicap_bet_info_data)

            # validate if the bet info has been settled 
            if handicap_bet_info.status == "Settled": 
                raise DRFValidationError({"error": f"Bet {i+1} can't be added because the info has been settled."})

            # validate if the it's still an hour before the match 
            if timezone.now() >= handicap_bet_info.match.date - timedelta(hours=1): 
                if timezone.now() > handicap_bet_info.match.date: 
                    error_msg = f"Bet {i + 1} can't be added because the match has begun"
                error_msg = f"Bet {i + 1} can't added because it's too close to when the match begin"

                raise DRFValidationError({
                    "error": error_msg,
                    "detail": f"The time match begins: {handicap_bet_info.match.date}"
                })
            
            # validate whether the bet with same bet info has been added by the user in the past 
            if UserHandicapBet.objects.filter(user=this_user, bet_info=handicap_bet_info).exists(): 
                raise DRFValidationError({"error": f"Bet {i + 1} in the list has been added by the user."})
            
            # increment the total and add the instance to the list 
            total_bet_amount += item_data["bet_amount"]
            handicap_data_list.append(UserHandicapBet(**item_data, bet_info=handicap_bet_info))
        
        # validate the sufficiency of the user's balance
        if this_user.balance < total_bet_amount: 
            raise DRFValidationError({
                "error": f"The user's balance is insufficient to create this bet.", 
                "detail": f"User balance: ${this_user.balance}, total amount: ${total_bet_amount}"
            })
        
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
        current_user = validated_data["user"]
        current_info_id = HandicapBetInfo.objects.get(**validated_data["bet_info"]).id
        old_bet_amount = instance.bet_amount

        # validate if the bet info has been settled 
        if instance.bet_info.status == "Settled": 
            raise DRFValidationError({"error": f"This bet can't be updated because the info has been settled."})

        # validate if other fields change 
        if instance.user.id != current_user.id or instance.bet_info.id != current_info_id: 
            # notify the client what has been changed for easier fix 
            detail_msg = ""
            if instance.user.id != current_user: 
                detail_msg += f"User has changed from {instance.user.id} to {current_user.id}."
            if instance.bet_info.id != current_info_id: 
                detail_msg += f" Bet info has changed from {instance.bet_info.id} to {current_info_id}."

            raise DRFValidationError({"error": "Only the bet amount can be updated.", "detail": detail_msg})
        
        # validate if the it's still an hour before the match 
        if timezone.now() >= instance.bet_info.match.date - timedelta(hours=1):
            if timezone.now() > instance.bet_info.match.date: 
                error_msg = "This be can't be updated because the match has begun."
            error_msg = "This bet can't be updated because it's too close to when the match begins."
            
            raise DRFValidationError({
                "error": error_msg, 
                "detail": f"The time match begins: {instance.bet_info.match.date}"
            })
        
        # validate the sufficiency of the users' balance 
        prior_bet_balance = current_user.balance + old_bet_amount
        if prior_bet_balance < validated_data["bet_amount"]: 
            raise DRFValidationError({
                "error": "The user's balance is insufficient to update this to bet to this amount",
                "detail": f"The user's balance: ${prior_bet_balance}, new bet amount: ${validated_data["bet_amount"]}"
            })
        
        # update the bet amount (if any) of the bet 
        instance.bet_amount = validated_data["bet_amount"]
        instance.save()
        return instance
    
    # the representation of the bet in the json data
    def to_representation(self, instance):
        bet_representation = super().to_representation(instance)
        bet_representation["username"] = instance.user.username
        return bet_representation