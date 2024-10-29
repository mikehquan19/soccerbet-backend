from . import views
from django.urls import path

urlpatterns = [
    # endpoints for teams, matches, rankings
    path('teams/<str:league>', views.team_list),
    path('matches/<str:league>/<str:status>', views.match_list), 

    # endpoints for the bet info
    path('match/<int:match_id>/moneyline_info', views.moneyline_info_list),
    path('match/<int:match_id>/handicap_info', views.HandicapInfoList.as_view()),
    path('match/<int:match_id>/total_goals_info', views.TotalGoalsInfoList.as_view()),

    # endpoints for the list of bets of the user 
    path('users/<int:user_id>/moneyline_bets', views.UserMoneylineBetList.as_view()), 
    path('users/<int:user_id>/handicap_bets', views.UserHandicapBetList.as_view()),
    path('users/<int:user_id>/total_goals_bets', views.UserTotalGoalsBetList.as_view()),

    # endpoints for the detail of bet of the user 
    path('moneyline_bets/<int:pk>', views.UserMoneylineBetDetail.as_view()),
    path('handicap_bets/<int:pk>', views.UserHandicapBetDetail.as_view()), 
    path('total_goals_bets/<int:pk>', views.UserTotalGoalsBetDetail.as_view()),
]