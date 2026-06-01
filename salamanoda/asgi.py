import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "salamanoda.settings")

# If Channels is installed, wire websocket routing; otherwise fall back to standard ASGI app.
try:
	from channels.routing import ProtocolTypeRouter, URLRouter
	from channels.auth import AuthMiddlewareStack
	from django.core.asgi import get_asgi_application as django_asgi_app
	import dispatch.routing as dispatch_routing

	application = ProtocolTypeRouter(
		{
			"http": django_asgi_app(),
			"websocket": AuthMiddlewareStack(URLRouter(dispatch_routing.websocket_urlpatterns)),
		}
	)
except Exception:
	# channels not installed or routing unavailable — use default Django ASGI app
	application = get_asgi_application()
