from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError


@database_sync_to_async
def user_from_token(token):
    authentication = JWTAuthentication()
    try:
        return authentication.get_user(authentication.get_validated_token(token))
    except (TokenError, AuthenticationFailed):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """Reads ?token=... from a WebSocket address and finds out who the user is."""

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        token = query.get("token", [None])[0]
        scope["user"] = await user_from_token(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)
