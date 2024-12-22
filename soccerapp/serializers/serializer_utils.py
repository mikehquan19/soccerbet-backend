""" SUPPLEMENTAL LOGIC FOR SERIALIZERS """

from rest_framework.serializers import ValidationError as DRFValidationError
from django.utils import timezone
from datetime import timedelta
from typing import Type
from django.db.models import Model


# validate the data to be created (for create() method)
# return the list of bets to be added and total bet amount
def validate_create_data(bet_info_class: Type[Model], user_bet_class: Type[Model], create_data): 
    total_bet_amount = 0 # total amount the user bet from the list
    saved_bet_list = [] # list of bets to be saved to the database 

    for i, item_data in enumerate(create_data): 
        # get the bet info based on the classes
        this_user = item_data["user"]
        bet_info_data = item_data.pop("bet_info")
        bet_info_obj = bet_info_class.objects.get(**bet_info_data)

        # validate if the bet info has been settled 
        if bet_info_obj.status == "Settled": 
            raise DRFValidationError({"error": f"Bet {i+1} can't be added because the info has been settled."})

        # validate if the it's still an hour before the match 
        if timezone.now() >= bet_info_obj.match.date - timedelta(hours=1): 
            if timezone.now() > bet_info_obj.match.date: 
                error_msg = f"Bet {i + 1} can't be added because the match has begun"
            else: 
                error_msg = f"Bet {i + 1} can't added because it's too close to when the match begin"
            raise DRFValidationError({
                "error": error_msg,
                "detail": f"The time match begins: {bet_info_obj.match.date}"
            })
            
        # validate whether the bet with same bet info has been added by the user in the past 
        if user_bet_class.objects.filter(user=this_user, bet_info=bet_info_obj).exists(): 
            raise DRFValidationError({"error": f"Bet {i + 1} in the list has been added by the user."})
            
        # increment the total and add the instance to the list 
        total_bet_amount += item_data["bet_amount"]
        saved_bet_list.append(user_bet_class(**item_data, bet_info=bet_info_obj))
        
    # validate the sufficiency of the user's balance
    if this_user.balance < total_bet_amount: 
        raise DRFValidationError({
            "error": f"The user's balance is insufficient to create this bet.", 
            "detail": f"User balance: ${this_user.balance}, total amount: ${total_bet_amount}"
        })
    # return 
    return total_bet_amount, saved_bet_list
    

# validate the data to be updated (for update() method)
# return none 
def validate_update_data(bet_info_class: Type[Model], instance, update_data): 
    current_user = update_data["user"]
    current_info_id = bet_info_class.objects.get(**update_data["bet_info"]).id

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
        else: 
            error_msg = "This bet can't be updated because it's too close to when the match begins."
            
        raise DRFValidationError({
            "error": error_msg, 
            "detail": f"The time match begins: {instance.bet_info.match.date}"
        })
        
    # validate the sufficiency of the users' balance 
    old_bet_amount = instance.bet_amount
    prior_bet_balance = current_user.balance + old_bet_amount
    if prior_bet_balance < update_data["bet_amount"]: 
        raise DRFValidationError({
            "error": "The user's balance is insufficient to update this to bet to this amount",
            "detail": f"The user's balance: ${prior_bet_balance}, new bet amount: ${update_data["bet_amount"]}"
        })
