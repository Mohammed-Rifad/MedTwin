import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django_app = get_asgi_application()
from twin.middleware import JWTAuthMiddleware  # noqa: E402

# These imports must come after get_asgi_application(), which sets Django up first.
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402
from twin.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_app,
       "websocket": AllowedHostsOriginValidator(JWTAuthMiddleware(URLRouter(websocket_urlpatterns))),

})
