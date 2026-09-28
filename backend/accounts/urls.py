from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views

app_name = "accounts"

router = DefaultRouter()
router.register("users", views.StaffViewSet, basename="users")

urlpatterns = [
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("logout/", TokenBlacklistView.as_view(), name="logout"),
    path("me/", views.me, name="me"),
    path("me/password/", views.change_password, name="change-password"),
    path("", include(router.urls)),
]
