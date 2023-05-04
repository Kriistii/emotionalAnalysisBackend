import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stressWork.settings')

from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from django.core.asgi import get_asgi_application
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack

import employee.routing


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(employee.routing.websocket_urlpatterns))
        ),
})

