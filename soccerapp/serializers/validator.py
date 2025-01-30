""" Validator """

from rest_framework.serializers import ValidationError as DRFValidationError
from django.utils import timezone
from datetime import date
from typing import Type
from django.db.models import Model
from decimal import Decimal

class CustomValidator: 
    # constructor, initializing appropriate bet info and user bet models 
    def __init__(self, bet_info_class: Type[Model]=None, user_bet_class: Type[Model]=None): 
        self.bet_info_class = bet_info_class
        self.user_bet_class = user_bet_class


    # validate the data to be created (for create() method)
    # return the list of bets to be added and total bet amount
    def validate_create(self, create_data): 
        total_bet_amount = 0 # total amount the user bet from the list
        saved_bet_list = [] # list of bets to be saved to the database 

        for i, item_data in enumerate(create_data): 
            # get the bet info based on the classes
            this_user = item_data["user"]
            bet_info_data = item_data.pop("bet_info")
            bet_info_obj = self.bet_info_class.objects.get(**bet_info_data)

            # validate if the bet info has been settled 
            if bet_info_obj.status == "Settled": 
                raise DRFValidationError({"error": f"Bet {i+1} can't be added because this bet info has been settled."})

            # validate if the it's still before the match 
            if timezone.now() >= bet_info_obj.match.date: 
                error_msg = f"Bet {i + 1} can't be added after the match begins"
                raise DRFValidationError({
                    "error": error_msg,
                    "detail": f"Match begins at {bet_info_obj.match.date}"
                })
            
            # validate whether the bet with same bet info has been added by the user in the past 
            if self.user_bet_class.objects.filter(user=this_user, bet_info=bet_info_obj).exists(): 
                raise DRFValidationError({"error": f"Bet {i + 1} in the list has already been placed"})
                    
            # increment the total and add the instance to the list 
            total_bet_amount += item_data["bet_amount"]
            saved_bet_list.append(self.user_bet_class(**item_data, created_date=date.today(), bet_info=bet_info_obj))
    
        total_bet_amount *= Decimal(1.05) # extra fees for placing the bets 
        
        # validate the sufficiency of the user's balance
        if this_user.balance < total_bet_amount: 
            raise DRFValidationError({
                "error": f"Sufficient balance to place these bets", 
                "detail": f"Balance: ${this_user.balance}, total amount: ${total_bet_amount}"
            })
        # return 
        return saved_bet_list, total_bet_amount
    

    # validate the data to be updated (for update() method)
    # return none 
    def validate_update(self, instance, update_data): 
        current_user = update_data["user"]
        try: 
            current_info = self.bet_info_class.objects.get(**update_data["bet_info"])
        except self.bet_info_class.DoesNotExist: 
            raise DRFValidationError({"error": "The bet info not defined."})

        # validate if the bet info has been settled 
        if instance.bet_info.status == "Settled": 
            raise DRFValidationError({"error": f"This bet can't be updated because the info has been settled."})

        # validate if other fields change 
        if instance.user != current_user or instance.bet_info != current_info: 
            # notify the client what has been changed for easier fix 
            detail_msg = ""
            if instance.user != current_user: 
                detail_msg += f"User has changed from {instance.user.pk} to {current_user.pk}\n"
            if instance.bet_info != current_info: 
                detail_msg += f" Bet info has changed from {instance.bet_info.pk} to {current_info.pk}\n"

            raise DRFValidationError({"error": "Only the bet amount can be updated.", "detail": detail_msg})
            
        # validate if the it's still before the match 
        if timezone.now() >= instance.bet_info.match.date: 
            error_msg = "This bet can't be updated because the match has begun."
            raise DRFValidationError({
                "error": error_msg, 
                "detail": f"The match begins at: {instance.bet_info.match.date}"
            })
            
        # validate the sufficiency of the users' balance 
        old_bet_amount = instance.bet_amount
        prior_bet_balance = current_user.balance + old_bet_amount
        if prior_bet_balance < update_data["bet_amount"]: 
            raise DRFValidationError({
                "error": "Insufficient balance to update bet to this amount",
                "detail": f"Balance: ${prior_bet_balance}, new bet amount: ${update_data["bet_amount"]}"
            })


    # validate the data to be deleted 
    def validate_delete(self, instance): 
        # validate if the it's still before the match 
        if timezone.now() >= instance.bet_info.match.date: 
            error_msg = "This bet can't be withdrawn because the match has begun."
            raise DRFValidationError({
                "error": error_msg, 
                "detail": f"The match begins at: {instance.bet_info.match.date}"
            })