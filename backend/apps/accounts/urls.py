# backend/apps/accounts/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Autenticação
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Perfil
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/<int:pk>/', views.UserProfileView.as_view(), name='user-profile'),
    
    # Follow/Unfollow
    path('follow/<int:user_id>/', views.FollowView.as_view(), name='follow'),
    path('unfollow/<int:user_id>/', views.UnfollowView.as_view(), name='unfollow'),
    path('followers/<int:user_id>/', views.FollowersListView.as_view(), name='followers'),
    path('following/<int:user_id>/', views.FollowingListView.as_view(), name='following'),
    
    # Atividades
    path('activities/', views.UserActivityView.as_view(), name='activities'),
]