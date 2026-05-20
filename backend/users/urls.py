from django.urls import path

from users.views import (
    CurrentUserView,
    MyTicketsView,
)

urlpatterns = [
    path("me/", CurrentUserView.as_view(), name="user-current"),
    path("me/tickets/", MyTicketsView.as_view(), name="user-my-tickets"),
]
