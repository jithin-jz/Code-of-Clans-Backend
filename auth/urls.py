from django.urls import path
from .views import (
    GitHubAuthURLView,
    GitHubCallbackView,
    GoogleAuthURLView,
    GoogleCallbackView,
    DiscordAuthURLView,
    DiscordCallbackView,
    RefreshTokenView,
    LogoutView,
    DeleteAccountView,
    AdminLoginView
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
    
    # Auth endpoints
    path('refresh/', RefreshTokenView.as_view(), name='refresh_token'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('user/delete/', DeleteAccountView.as_view(), name='delete_account'),
    path('admin/login/', AdminLoginView.as_view(), name='admin_login'),
]
