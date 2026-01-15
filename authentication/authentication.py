from rest_framework import authentication, exceptions
from django.contrib.auth.models import User
from .utils import decode_token


class JWTAuthentication(authentication.BaseAuthentication):
    """Custom JWT authentication for Django REST Framework."""
    
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None
        
        try:
            prefix, token = auth_header.split(' ')
            if prefix.lower() != 'bearer':
                return None
        except ValueError:
            return None
        
        payload = decode_token(token)
        
        if not payload:
            raise exceptions.AuthenticationFailed('Invalid or expired token')
        
        if payload.get('type') != 'access':
            raise exceptions.AuthenticationFailed('Invalid token type')
        
        try:
            user = User.objects.get(id=payload['user_id'])
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')

        if not user.is_active:
            raise exceptions.AuthenticationFailed('User account is disabled.')
        
        return (user, token)
