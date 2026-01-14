from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserProfile
from .serializers import UserSerializer, RefreshTokenSerializer, AdminLoginSerializer
from .utils import (
    generate_tokens,
    decode_token,
    generate_access_token,
    get_github_access_token,
    get_github_user,
    get_github_user_email,
    get_google_access_token,
    get_google_user,
    get_discord_access_token,
    get_discord_user,
)



class OAuthUserMixin:
    """Mixin to handle OAuth user creation/retrieval."""
    
    def get_or_create_oauth_user(self, provider, provider_id, email, username, name, avatar_url, access_token, refresh_token=''):
        """Find or create a user from OAuth data."""
        
        # Check if user with this provider exists
        try:
            profile = UserProfile.objects.get(provider=provider, provider_id=provider_id)
            user = profile.user
            
            # Update profile with new tokens
            # Update profile with new tokens
            profile.access_token = access_token
            if refresh_token:
                profile.refresh_token = refresh_token
            # Only set avatar if missing (don't overwrite custom uploads)
            if not profile.avatar_url:
                profile.avatar_url = avatar_url
            profile.save()
            
        except UserProfile.DoesNotExist:
            # Check if user with email exists
            user = User.objects.filter(email=email).first() if email else None
            
            if not user:
                # Create new user with unique username
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1
                
                # Split name into first and last
                name_parts = name.split(' ', 1) if name else ['', '']
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ''
                
                user = User.objects.create_user(
                    username=username,
                )
            
            # Check for existing profile (fix for IntegrityError)
            if hasattr(user, 'profile'):
                profile = user.profile
                profile.provider = provider
                profile.provider_id = provider_id
                # Only set avatar if missing
                if not profile.avatar_url:
                    profile.avatar_url = avatar_url
                profile.access_token = access_token
                if refresh_token:
                    profile.refresh_token = refresh_token
                profile.save()
            else:
                # Create profile for user
                profile = UserProfile.objects.create(
                    user=user,
                    provider=provider,
                    provider_id=provider_id,
                    avatar_url=avatar_url,
                    access_token=access_token,
                    refresh_token=refresh_token
                )
        
        # Generate JWT tokens
        tokens = generate_tokens(user)
        
        return user, tokens


# GitHub OAuth Views
class GitHubAuthURLView(APIView):
    """Return the GitHub OAuth authorization URL."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        params = {
            'client_id': settings.GITHUB_CLIENT_ID,
            'redirect_uri': settings.GITHUB_REDIRECT_URI,
            'scope': 'user:email',
        }
        url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
        return Response({'url': url})


class GitHubCallbackView(OAuthUserMixin, APIView):
    """Handle GitHub OAuth callback."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        code = request.data.get('code')
        
        if not code:
            return Response(
                {'error': 'Authorization code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Exchange code for access token
        token_data = get_github_access_token(code)
        
        if 'error' in token_data:
            error_msg = token_data.get('error_description') or token_data.get('error') or 'Failed to get access token'
            debug_info = f" (Status: {token_data.get('error')})"
            return Response(
                {'error': f"{error_msg}{debug_info}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        access_token = token_data.get('access_token')
        
        # Get user data from GitHub
        github_user = get_github_user(access_token)
        
        if 'id' not in github_user:
            return Response(
                {'error': 'Failed to get user data from GitHub'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        github_id = str(github_user['id'])
        email = github_user.get('email') or get_github_user_email(access_token)
        username = github_user.get('login')
        name = github_user.get('name', '')
        avatar_url = github_user.get('avatar_url', '')
        
        # Find or create user
        user, tokens = self.get_or_create_oauth_user(
            provider='github',
            provider_id=github_id,
            email=email,
            username=username,
            name=name,
            avatar_url=avatar_url,
            access_token=access_token
        )
        
        return Response({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'user': UserSerializer(user).data
        })


# Google OAuth Views
class GoogleAuthURLView(APIView):
    """Return the Google OAuth authorization URL."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        params = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'response_type': 'code',
            'scope': 'https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile',
            'access_type': 'offline',
            'prompt': 'select_account',
        }
        url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return Response({'url': url})


class GoogleCallbackView(OAuthUserMixin, APIView):
    """Handle Google OAuth callback."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        code = request.data.get('code')
        
        if not code:
            return Response(
                {'error': 'Authorization code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Exchange code for access token
        token_data = get_google_access_token(code)
        
        if 'error' in token_data:
            error_msg = token_data.get('error_description') or token_data.get('error') or 'Failed to get access token'
            debug_info = f" (Status: {token_data.get('error')})"
            return Response(
                {'error': f"{error_msg}{debug_info}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token', '')
        
        # Get user data from Google
        google_user = get_google_user(access_token)
        
        if 'id' not in google_user:
            return Response(
                {'error': 'Failed to get user data from Google'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        google_id = str(google_user['id'])
        email = google_user.get('email', '')
        username = email.split('@')[0] if email else f"google_{google_id}"
        name = google_user.get('name', '')
        avatar_url = google_user.get('picture', '')
        
        # Find or create user
        user, tokens = self.get_or_create_oauth_user(
            provider='google',
            provider_id=google_id,
            email=email,
            username=username,
            name=name,
            avatar_url=avatar_url,
            access_token=access_token,
            refresh_token=refresh_token
        )
        
        return Response({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'user': UserSerializer(user).data
        })


# Discord OAuth Views
class DiscordAuthURLView(APIView):
    """Return the Discord OAuth authorization URL."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        params = {
            'client_id': settings.DISCORD_CLIENT_ID,
            'redirect_uri': settings.DISCORD_REDIRECT_URI,
            'response_type': 'code',
            'scope': 'identify email',
        }
        url = f"https://discord.com/api/oauth2/authorize?{urlencode(params)}"
        return Response({'url': url})


class DiscordCallbackView(OAuthUserMixin, APIView):
    """Handle Discord OAuth callback."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        code = request.data.get('code')
        
        if not code:
            return Response(
                {'error': 'Authorization code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Exchange code for access token
        token_data = get_discord_access_token(code)
        
        if 'error' in token_data:
            error_msg = token_data.get('error_description') or token_data.get('error') or 'Failed to get access token'
            # Append detailed debug info if available
            debug_info = f" (Status: {token_data.get('error')})"
            return Response(
                {'error': f"{error_msg}{debug_info}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token', '')
        
        # Get user data from Discord
        discord_user = get_discord_user(access_token)
        
        if 'id' not in discord_user:
            return Response(
                {'error': 'Failed to get user data from Discord'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        discord_id = str(discord_user['id'])
        email = discord_user.get('email', '')
        username = discord_user.get('username', f"discord_{discord_id}")
        name = discord_user.get('global_name', username)
        
        # Discord avatar URL construction
        avatar_hash = discord_user.get('avatar')
        if avatar_hash:
            avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_hash}.png"
        else:
            # Default avatar
            discriminator = discord_user.get('discriminator', '0')
            avatar_url = f"https://cdn.discordapp.com/embed/avatars/{int(discriminator) % 5}.png"
        
        # Find or create user
        user, tokens = self.get_or_create_oauth_user(
            provider='discord',
            provider_id=discord_id,
            email=email,
            username=username,
            name=name,
            avatar_url=avatar_url,
            access_token=access_token,
            refresh_token=refresh_token
        )
        
        return Response({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'user': UserSerializer(user).data
        })





# User Views
class CurrentUserView(APIView):
    """Get the currently authenticated user."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class RefreshTokenView(APIView):
    """Refresh the access token using a refresh token."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        token = serializer.validated_data['refresh_token']
        payload = decode_token(token)
        
        if not payload:
            return Response(
                {'error': 'Invalid or expired refresh token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if payload.get('type') != 'refresh':
            return Response(
                {'error': 'Invalid token type'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            user = User.objects.get(id=payload['user_id'])
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        new_access_token = generate_access_token(user)
        
        return Response({
            'access_token': new_access_token,
            'user': UserSerializer(user).data
        })


class LogoutView(APIView):
    """Logout the user (client should delete tokens)."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # In a stateless JWT system, logout is handled client-side
        # We just return success here
        return Response({'message': 'Successfully logged out'})


class AdminLoginView(APIView):
    """Admin login view."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.validated_data['user']
        tokens = generate_tokens(user)
        
        return Response({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'user': UserSerializer(user).data
        })
        
        
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
            from .supabase_client import StorageService
            try:
                avatar_url = StorageService.upload_file(
                    request.FILES['avatar'], 
                    f"avatars/{user.id}_{request.FILES['avatar'].name}"
                )
                profile.avatar_url = avatar_url
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
                
        if 'banner' in request.FILES:
            from .supabase_client import StorageService
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
            
        from .models import UserFollow
        
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
        
        # We also might want to award XP to the referrer? 
        # The prompt says "user enter referal code and get xp", implying the one entering gets it.
        # It doesn't explicitly say the referrer gets it, but usually they do. 
        # I'll stick to the prompt: only the user entering gets XP for now, but commonly both do.
        # "user enter referal code and get xp only one time" -> Focus on the enterer.
        
        return Response({
            'message': 'Referral code redeemed successfully',
            'xp_awarded': 100,
            'new_total_xp': profile.xp
        })


class DeleteAccountView(APIView):
    """View to delete the user account."""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        user = request.user
        user.delete()
        return Response({'message': 'Account deleted successfully'})
