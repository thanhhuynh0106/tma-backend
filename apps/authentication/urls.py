from django.urls import path

from apps.authentication import views

app_name = "authentication"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change-password"),
    path("force-reset-password/", views.ForceResetPasswordView.as_view(), name="force-reset-password"),
    path("deactivate/", views.DeactivateUserView.as_view(), name="deactivate"),
    path("reactivate/", views.ReactivateUserView.as_view(), name="reactivate"),
]

