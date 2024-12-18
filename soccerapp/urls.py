from . import views
from django.urls import path

urlpatterns = [
    # endpoints for teams, matches, rankings
    path('teams/<str:league>', views.TeamList.as_view()),
    path('matches/<str:league>/<str:status>', views.MatchList.as_view()),
    path('users/<int:pk>', views.UserDetail.as_view()),

    # endpoints for the bet info
    path('match/<int:match_id>/moneyline_bet_info', views.MoneylineInfoList.as_view()),
    path('match/<int:match_id>/handicap_bet_info', views.HandicapInfoList.as_view()),
    path('match/<int:match_id>/total_goals_bet_info', views.TotalGoalsInfoList.as_view()),

    # endpoints for the list of bets of the user 
    path('users/<int:user_id>/moneyline_bets', views.UserMoneylineBetList.as_view()), 
    path('users/<int:user_id>/handicap_bets', views.UserHandicapBetList.as_view()),
    path('users/<int:user_id>/total_goals_bets', views.UserTotalGoalsBetList.as_view()),

    # endpoints for the detail of bet of the user 
    path('moneyline_bets/<int:pk>', views.UserMoneylineBetDetail.as_view()),
    path('handicap_bets/<int:pk>', views.UserHandicapBetDetail.as_view()), 
    path('total_goals_bets/<int:pk>', views.UserTotalGoalsBetDetail.as_view()),
]