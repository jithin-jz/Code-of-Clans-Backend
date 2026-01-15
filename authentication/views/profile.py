from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import UserProfile
from ..serializers import UserSerializer

class ProfileUpdateView(APIView):
    """View to update user profile (avatar, banner, bio)."""
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        user = request.user
        data = request.data
        
        # Update User model fields
        if 'username' in data:
            user.username = data['username']
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        user.save()
        
        # Update UserProfile fields
        profile = user.profile
        if 'bio' in data:
            profile.bio = data['bio']
            
        # Handle file uploads
        if 'avatar' in request.FILES:
            from ..supabase_client import StorageService
            try:
                avatar_url = StorageService.upload_file(
                    request.FILES['avatar'], 
                    f"avatars/{user.id}_{request.FILES['avatar'].name}"
                )
                profile.avatar_url = avatar_url
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
                
        if 'banner' in request.FILES:
            from ..supabase_client import StorageService
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
            
        from ..models import UserFollow
        
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
