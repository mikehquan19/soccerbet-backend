""" SERIALIZER VALIDATOR """

from rest_framework.serializers import ValidationError as DRFValidationError
from django.utils import timezone
from datetime import date
from typing import Type, Tuple
from django.db.models import Model
from decimal import Decimal

class CustomValidator: 
    """ Validator for bet info """
    def __init__(self, info_class: Type[Model], bet_class: Type[Model]): 
        """ 
        Constructor, initializing appropriate bet info and user bet models 
        """
        self.info_class = info_class
        self.bet_class = bet_class


    def validate_create(self, create_data) -> Tuple:
        """ 
        Validate the data to be created for ```create()```, and return the list of bets 
        to be added and total bet amount
        """
        total_bet_amount = 0 # total amount the user bet from the list, 
        saved_bet_list = [] # list of bets to be saved to the database

        for i, item_data in enumerate(create_data): 
            # get the bet info based on the classes
            info_data = item_data.pop("bet_info")
            info_object = self.info_class.objects.get(**info_data)

            # validate if the bet info has been settled 
            if info_object.status == "Settled": 
                raise DRFValidationError({
                    "error": f"Bet {i + 1} can't be added because its bet info has been settled.",
                })

            # validate if the bet is still before the match 
            if timezone.now() >= info_object.match.date: 
                raise DRFValidationError({
                    "error": f"Bet {i + 1} can't be added after the match begins",
                    "detail": f"Match begins at {info_object.match.date}"
                })
            
            # validate if the bet with same bet info has been added by the user in the past 
            if self.bet_class.objects.filter(
                user=item_data["user"], bet_info=info_object
            ).exists(): 
                raise DRFValidationError({
                    "error": f"Bet {i + 1} in the list has already been placed",
                })
                    
            # increment the total and add the instance to the list 
            total_bet_amount += item_data["bet_amount"]
            saved_bet_list.append(self.bet_class(
                **item_data, 
                created_date=date.today(), 
                bet_info=info_object
            ))
    
        total_bet_amount *= Decimal(1.05) # extra fees for placing the bets 
        # validate if the user's balance is sufficient 
        user = item_data["user"]
        if user.balance < total_bet_amount: 
            raise DRFValidationError({
                "error": "Sufficient balance to place these bets", 
                "detail": f"Balance: ${user.balance}, total amount: ${total_bet_amount}"
            })
        
        # return the bet list, and total bet amount of the list 
        return saved_bet_list, total_bet_amount
    

    def validate_update(self, instance, update_data) -> None:
        """ 
        Validate the data to be updated (for method ```update()```).
        Return None
        """
        current_user = update_data["user"]
        try: 
            current_info = self.info_class.objects.get(**update_data["bet_info"])
        except self.info_class.DoesNotExist: 
            raise DRFValidationError({"error": "The bet info not defined."})

        # validate if the bet info has been settled 
        if instance.bet_info.status == "Settled": 
            raise DRFValidationError({
                "error": f"This bet can't be updated because the info has been settled."
            })

        # validate if other fields change 
        if instance.user != current_user or instance.bet_info != current_info: 
            # notify the client what has been changed for easier fix 
            detail_msg = ""
            if instance.user != current_user: 
                detail_msg += f"User has changed from {instance.user.pk} to {current_user.id}\n"
            if instance.bet_info != current_info: 
                detail_msg += f" Bet info has changed from {instance.bet_info.pk} to {current_info.id}\n"

            raise DRFValidationError({
                "error": "Only the bet amount can be updated.", 
                "detail": detail_msg
            })
            
        # validate if the it's still before the match 
        if timezone.now() >= instance.bet_info.match.date: 
            error_msg = "This bet can't be updated because the match has begun."
            raise DRFValidationError({
                "error": error_msg, 
                "detail": f"The match begins at: {instance.bet_info.match.date}"
            })
            
        # validate if the users' balance is sufficient 
        old_amount = instance.bet_amount
        old_bet_balance = current_user.balance + old_amount
        update_amount = update_data["bet_amount"]
        
        if old_bet_balance < update_data: 
            raise DRFValidationError({
                "error": "Insufficient balance to update bet to this amount",
                "detail": f"Balance: ${old_bet_balance}, new bet amount: ${update_amount}"
            })


    def validate_delete(self, instance) -> None:
        """ Validate the data to be deleted  """

        # validate if the bet's  still before the match 
        if timezone.now() >= instance.bet_info.match.date: 
            raise DRFValidationError({
                "error": "This bet can't be withdrawn because the match has begun.", 
                "detail": f"The match begins at: {instance.bet_info.match.date}"
            })