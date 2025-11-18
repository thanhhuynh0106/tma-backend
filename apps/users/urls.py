from django.urls import path

from apps.users import views

app_name = "users"

urlpatterns = [
    path("", views.UserListView.as_view(), name="user-list"),
    path("me/", views.UserMeView.as_view(), name="user-me"),
    path("<str:user_id>/", views.UserDetailView.as_view(), name="user-detail"),
]

