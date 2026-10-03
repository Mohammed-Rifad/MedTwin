from django.urls import path

from .consumers import HospitalConsumer

websocket_urlpatterns = [
    path("ws/hospital/", HospitalConsumer.as_asgi()),
]

