from django.urls import path

from users.views import CurrentUserView, UserLoginView, UserRegistrationView

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="user-register"),
    path("login/", UserLoginView.as_view(), name="user-login"),
    path("me/", CurrentUserView.as_view(), name="user-current"),
]