from django.urls import path

from users.views import (
    CurrentUserView,
    MyTicketsView,
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
    path("me/", CurrentUserView.as_view(), name="user-current"),
    path("me/tickets/", MyTicketsView.as_view(), name="user-my-tickets"),
]
