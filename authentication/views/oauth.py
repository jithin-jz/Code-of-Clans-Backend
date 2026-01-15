from urllib.parse import urlencode
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import UserProfile
from ..serializers import UserSerializer
from ..utils import (
    generate_tokens,
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
        
        if not user.is_active:
            return Response({'error': 'User account is disabled.'}, status=status.HTTP_403_FORBIDDEN)
        
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
        
        if not user.is_active:
             return Response({'error': 'User account is disabled.'}, status=status.HTTP_403_FORBIDDEN)

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
        
        if not user.is_active:
             return Response({'error': 'User account is disabled.'}, status=status.HTTP_403_FORBIDDEN)

        return Response({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'user': UserSerializer(user).data
        })
