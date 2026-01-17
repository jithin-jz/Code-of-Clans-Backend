from django.urls import path
from .views import (
    CurrentUserView,
    ProfileUpdateView,
    RedeemReferralView,
    ProfileDetailView,
    FollowToggleView,
    UserFollowersView,
    UserFollowingView,
    UserListView,
    UserBlockToggleView
)

urlpatterns = [
    path('user/', CurrentUserView.as_view(), name='get_current_user'),
    path('user/update/', ProfileUpdateView.as_view(), name='update_profile'),
    path('user/redeem-referral/', RedeemReferralView.as_view(), name='redeem_referral'),
    
    path('users/<str:username>/', ProfileDetailView.as_view(), name='profile_detail'),
    path('users/<str:username>/follow/', FollowToggleView.as_view(), name='toggle_follow'),
    path('users/<str:username>/followers/', UserFollowersView.as_view(), name='user_followers'),
    path('users/<str:username>/following/', UserFollowingView.as_view(), name='user_following'),
    
    # Admin routes (moved from auth)
    path('admin/users/', UserListView.as_view(), name='admin_user_list'),
    path('admin/users/<str:username>/toggle-block/', UserBlockToggleView.as_view(), name='admin_toggle_block_user'),
]
