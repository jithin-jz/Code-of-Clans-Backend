from rest_framework import authentication, exceptions
from django.contrib.auth.models import User
from .utils import decode_token


class JWTAuthentication(authentication.BaseAuthentication):
    """
    Custom JWT authentication for Django REST Framework.
    
    This class verifies the 'Authorization: Bearer <token>' header, 
    decodes the JWT, and ensures the associated user is valid and active.
    """
    
    def authenticate(self, request):
        # 1. Retrieve the Authorization header from the incoming request
        auth_header = request.headers.get('Authorization')
        
        # If no header is provided, return None to allow other 
        # authentication schemes to be attempted.
        if not auth_header:
            return None
        
        # 2. Extract the prefix and the token string
        try:
            prefix, token = auth_header.split(' ')
            # Only process headers starting with 'bearer'
            if prefix.lower() != 'bearer':
                return None
        except ValueError:
            # Handle malformed headers (e.g., header missing a space)
            return None
        
        # 3. Decode and validate the token signature and expiration
        payload = decode_token(token)
        
        # If decoding fails (invalid signature or expired), raise 401 Unauthorized
        if not payload:
            raise exceptions.AuthenticationFailed('Invalid or expired token')
        
        # 4. Enforce token usage policies (e.g., must be an 'access' token)
        if payload.get('type') != 'access':
            raise exceptions.AuthenticationFailed('Invalid token type')
        
        # 5. Identify and validate the user associated with the token
        try:
            user = User.objects.get(id=payload['user_id'])
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')

        # 6. Ensure the user account is still permitted to access the system
        if not user.is_active:
            raise exceptions.AuthenticationFailed('User account is disabled.')
        
        # 7. Return the (user, auth) tuple required by DRF
        # This sets request.user and request.auth in the view
        return (user, token)