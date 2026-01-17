from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserProfile, UserFollow
from .serializers import UserSerializer

# Helper to handle file uploads
from auth.supabase_client import StorageService


class CurrentUserView(APIView):
    """Get the currently authenticated user."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ProfileUpdateView(APIView):
    """
    Updates the authenticated user's profile.
    
    Supports:
    - **Text Fields**: username, first_name, last_name, bio, external links.
    - **File Uploads**: avatar, banner (handled via StorageService).
    """
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        user = request.user
        data = request.data
        
        # 1. Update Core User Model Fields
        if 'username' in data:
            user.username = data['username']
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        user.save()
        
        # 2. Update Extended UserProfile Fields
        profile = user.profile
        if 'bio' in data:
            profile.bio = data['bio']
        if 'github_username' in data:
            profile.github_username = data['github_username']
        if 'leetcode_username' in data:
            profile.leetcode_username = data['leetcode_username']
            
        # 3. Handle File Uploads (to Supabase Storage)
        if 'avatar' in request.FILES:
            try:
                avatar_url = StorageService.upload_file(
                    request.FILES['avatar'], 
                    f"avatars/{user.id}_{request.FILES['avatar'].name}"
                )
                profile.avatar_url = avatar_url
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
                
        if 'banner' in request.FILES:
            try:
                banner_url = StorageService.upload_file(
                    request.FILES['banner'], 
                    f"banners/{user.id}_{request.FILES['banner'].name}"
                )
                profile.banner_url = banner_url
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        profile.save()
        
        return Response(UserSerializer(user).data)


class ProfileDetailView(APIView):
    """View to get public profile details."""
    permission_classes = [AllowAny]
    
    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            
        data = UserSerializer(user).data
        
        # Add stats
        data['followers_count'] = user.followers.count()
        data['following_count'] = user.following.count()
        
        # Check if requesting user is following
        if request.user.is_authenticated:
            data['is_following'] = user.followers.filter(follower=request.user).exists()
        else:
            data['is_following'] = False
            
        return Response(data)


class FollowToggleView(APIView):
    """View to toggle follow status."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, username):
        try:
            target_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            
        if target_user == request.user:
            return Response({'error': 'Cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)
            
        follow, created = UserFollow.objects.get_or_create(
            follower=request.user,
            following=target_user
        )
        
        if not created:
            # If relationship exists, unfollow
            follow.delete()
            is_following = False
        else:
            is_following = True
            
        return Response({
            'is_following': is_following,
            'follower_count': target_user.followers.count(),
            'following_count': target_user.following.count()
        })


class UserFollowersView(APIView):
    """View to get list of followers for a user."""
    permission_classes = [AllowAny]

    def get(self, request, username):
        try:
            target_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        followers = target_user.followers.all()
        # We want to show: username, avatar, and if the *requesting user* is following them
        
        data = []
        auth_user = request.user
        
        for rel in followers:
            follower_user = rel.follower
            is_following = False
            if auth_user.is_authenticated:
                is_following = auth_user.following.filter(following=follower_user).exists()
            
            profile = getattr(follower_user, 'profile', None)
            
            data.append({
                'username': follower_user.username,
                'first_name': follower_user.first_name,
                'avatar_url': profile.avatar_url if profile else None,
                'is_following': is_following
            })
            
        return Response(data)


class UserFollowingView(APIView):
    """View to get list of users a user is following."""
    permission_classes = [AllowAny]

    def get(self, request, username):
        try:
            target_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        following = target_user.following.all()
        
        data = []
        auth_user = request.user
        
        for rel in following:
            following_user = rel.following
            is_following = False
            if auth_user.is_authenticated:
                 # Check if auth user is following this person (who target_user is also following)
                is_following = auth_user.following.filter(following=following_user).exists()
                
            profile = getattr(following_user, 'profile', None)
            
            data.append({
                'username': following_user.username,
                'first_name': following_user.first_name,
                'avatar_url': profile.avatar_url if profile else None,
                'is_following': is_following
            })
            
        return Response(data)


class RedeemReferralView(APIView):
    """View to redeem a referral code."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        code = request.data.get('code')
        
        if not code:
            return Response({'error': 'Referral code is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)
            
        if profile.referred_by:
            return Response({'error': 'You have already redeemed a referral code'}, status=status.HTTP_400_BAD_REQUEST)
            
        if profile.referral_code == code:
            return Response({'error': 'Cannot redeem your own referral code'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            referrer_profile = UserProfile.objects.get(referral_code=code)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Invalid referral code'}, status=status.HTTP_404_NOT_FOUND)
            
        # Update user profile
        profile.referred_by = referrer_profile.user
        profile.xp += 100  # Award 100 XP
        profile.save()
        
        return Response({
            'message': 'Referral code redeemed successfully',
            'xp_awarded': 100,
            'new_total_xp': profile.xp
        })


class UserListView(APIView):
    """View to list all users for admin."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
             return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        users = User.objects.all().order_by('-date_joined')
        return Response(UserSerializer(users, many=True).data)


class UserBlockToggleView(APIView):
    """View to toggle user active status."""
    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        if not (request.user.is_staff or request.user.is_superuser):
             return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
             return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if user == request.user:
             return Response({'error': 'Cannot block yourself'}, status=status.HTTP_400_BAD_REQUEST)

        # Toggle status directly on user model
        user.is_active = not user.is_active
        user.save()
        
        return Response({
            'message': f"User {'unblocked' if user.is_active else 'blocked'} successfully",
            'is_active': user.is_active
        })
