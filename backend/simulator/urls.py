from django.urls import path

from . import views

app_name = "simulator"

urlpatterns = [
    path("", views.simulator_status, name="status"),
    path("start/", views.start, name="start"),
    path("pause/", views.pause, name="pause"),
    path("surge/", views.surge, name="surge"),
    path("deteriorate/", views.deteriorate, name="deteriorate"),
    path("device-fault/", views.device_fault, name="device-fault"),
]
