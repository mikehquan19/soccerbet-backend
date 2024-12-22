from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.User)
admin.site.register(models.Team)
admin.site.register(models.TeamRanking)
admin.site.register(models.Match)
admin.site.register(models.MoneylineBetInfo)
admin.site.register(models.UserMoneylineBet)
admin.site.register(models.HandicapBetInfo)
admin.site.register(models.UserHandicapBet)
admin.site.register(models.TotalObjectsBetInfo)
admin.site.register(models.UserTotalObjectsBet)
