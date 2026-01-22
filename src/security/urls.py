from django.urls import path
from security.apps import SecurityConfig
from security.views import login, authenticate, logout


app_name = SecurityConfig.name


urlpatterns = [
    path("login/", login, name="login"),
    path("authenticate/", authenticate, name="authenticate"),
    path("logout/", logout, name="logout"),
]
