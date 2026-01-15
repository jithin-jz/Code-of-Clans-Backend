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
    RedeemReferralView,
    DeleteAccountView,
    UserFollowersView,
    UserFollowingView,
    UserListView,
    UserBlockToggleView
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
    path('user/redeem-referral/', RedeemReferralView.as_view(), name='redeem_referral'),
    path('user/delete/', DeleteAccountView.as_view(), name='delete_account'),
    path('users/<str:username>/', ProfileDetailView.as_view(), name='profile_detail'),
    path('users/<str:username>/follow/', FollowToggleView.as_view(), name='toggle_follow'),
    path('users/<str:username>/followers/', UserFollowersView.as_view(), name='user_followers'),
    path('users/<str:username>/following/', UserFollowingView.as_view(), name='user_following'),
    path('refresh/', RefreshTokenView.as_view(), name='refresh_token'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('admin/login/', AdminLoginView.as_view(), name='admin_login'),
    path('admin/users/', UserListView.as_view(), name='admin_user_list'),
    path('admin/users/<str:username>/toggle-block/', UserBlockToggleView.as_view(), name='admin_toggle_block_user'),
]
