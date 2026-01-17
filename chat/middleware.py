from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser
from auth.utils import decode_token

@database_sync_to_async
def get_user(token):
    try:
        payload = decode_token(token)
        if payload:
            return User.objects.get(id=payload['user_id'])
        return AnonymousUser()
    except:
        return AnonymousUser()

class JWTAuthMiddleware:
    """
    Custom Middleware for Django Channels to handle JWT Authentication.
    
    Problem: WebSockets don't natively send headers in the initial handshake in browser JS API.
    Solution: Pass the JWT token via Query Param `?token=...`.
    
    This middleware:
    1.  Intercepts the scope.
    2.  Extracts `token` from the query string.
    3.  Decodes it to find the user.
    4.  Attaches the `user` object to the scope for consumers to use.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Parse query string: e.g. b'token=eyJhb...' -> 'eyJhb...'
        query_string = scope.get("query_string", b"").decode()
        query_params = dict(qp.split("=") for qp in query_string.split("&") if "=" in qp)
        token = query_params.get("token")
        
        # Resolve user from token (async)
        scope["user"] = await get_user(token) if token else AnonymousUser()
        return await self.app(scope, receive, send)