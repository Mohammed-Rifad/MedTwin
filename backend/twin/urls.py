from django.urls import path

from . import views

app_name = "twin"

urlpatterns = [
    path("summary/", views.summary, name="summary"),
]
