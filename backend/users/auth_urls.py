from django.urls import path

from users.views import (
    UserLoginView,
    UserRegistrationView,
    UserTokenRefreshView,
)

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="user-register"),
    path("login/", UserLoginView.as_view(), name="user-login"),
    path(
        "token/refresh/",
        UserTokenRefreshView.as_view(),
        name="token-refresh",
    ),
]
