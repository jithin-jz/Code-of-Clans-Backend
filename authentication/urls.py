from django.urls import path
from .views import (
    GitHubAuthURLView,
    GitHubCallbackView,
    GoogleAuthURLView,
    GoogleCallbackView,
    DiscordAuthURLView,
    DiscordCallbackView,
    CurrentUserView,
    RefreshTokenView,
    LogoutView,
    AdminLoginView,
    ProfileUpdateView,
    FollowToggleView,
    ProfileDetailView,
)

urlpatterns = [
    # GitHub OAuth
    path('github/', GitHubAuthURLView.as_view(), name='github_auth_url'),
    path('github/callback/', GitHubCallbackView.as_view(), name='github_callback'),
    
    # Google OAuth
    path('google/', GoogleAuthURLView.as_view(), name='google_auth_url'),
    path('google/callback/', GoogleCallbackView.as_view(), name='google_callback'),
    
    # Discord OAuth
    path('discord/', DiscordAuthURLView.as_view(), name='discord_auth_url'),
    path('discord/callback/', DiscordCallbackView.as_view(), name='discord_callback'),
    
    # User endpoints
    path('user/', CurrentUserView.as_view(), name='get_current_user'),
    path('user/update/', ProfileUpdateView.as_view(), name='update_profile'),
    path('users/<str:username>/', ProfileDetailView.as_view(), name='profile_detail'),
    path('users/<str:username>/follow/', FollowToggleView.as_view(), name='toggle_follow'),
    path('refresh/', RefreshTokenView.as_view(), name='refresh_token'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('admin/login/', AdminLoginView.as_view(), name='admin_login'),
]
