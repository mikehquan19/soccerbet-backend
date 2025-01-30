from . import views
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView
from django.urls import path

urlpatterns = [
    # endpoints for authentication 
    path('login', views.Login.as_view()),
    path('register', views.Register.as_view()),
    path('login/refresh', TokenRefreshView.as_view()),
    path('logout', TokenBlacklistView.as_view()),
    path('detail', views.UserDetail.as_view()),

    # endpoints for teams, matches, rankings
    path('teams', views.TeamList.as_view()), # params: 'league' to indicate the list of teams from league 
    path('teams/<int:pk>', views.TeamDetail.as_view()),
    path('standings', views.Standings.as_view()), # params: 'league' to indicate the list of teams from league 
    path('matches', views.MatchList.as_view()),
    path('matches/<int:match_id>', views.MatchDetail.as_view()),

    # endpoints for comments 
    path('comments', views.CommentList.as_view()), # params: 'reply_to' to indicate the parent comment, 'team' to indicate user's pk
    path('comments/<int:pk>', views.CommentDetail.as_view()),
    path('like_comment/<int:pk>', views.LikeComment.as_view()),

    # endpoints for the bet info
    path('match/<int:match_id>/moneyline_bet_info', views.MoneylineInfoList.as_view()),
    path('match/<int:match_id>/handicap_bet_info', views.HandicapInfoList.as_view()),
    path('match/<int:match_id>/total_bet_info', views.TotalObjectsInfoList.as_view()), 

    # endpoints for the list of bets of the user 
    path('moneyline_bets', views.UserMoneylineBetList.as_view()), 
    path('handicap_bets', views.UserHandicapBetList.as_view()),
    path('total_bets', views.UserTotalGoalsBetList.as_view()),

    # endpoints for the detail of bet of the user 
    path('moneyline_bets/<int:pk>', views.UserMoneylineBetDetail.as_view()),
    path('handicap_bets/<int:pk>', views.UserHandicapBetDetail.as_view()), 
    path('total_bets/<int:pk>', views.UserTotalGoalsBetDetail.as_view()),
]