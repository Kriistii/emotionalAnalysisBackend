# chat/routing.py
from django.urls import path

from .consumers import *

websocket_urlpatterns = [
    path("chatSession/<int:employee_id>", ChatConsumer.as_asgi()),
]