from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser
from authentication.utils import decode_token

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
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        query_params = dict(qp.split("=") for qp in query_string.split("&") if "=" in qp)
        token = query_params.get("token")
        
        scope["user"] = await get_user(token) if token else AnonymousUser()
        return await self.app(scope, receive, send)