from django.urls import path
from apps.attendance import views

app_name = "attendance"

urlpatterns = [
    path("", views.AttendanceListView.as_view(), name="attendance-list"),
    path("me/", views.MyAttendanceView.as_view(), name="my-attendance"),
    path("user/<str:user_id>/", views.UserAttendanceView.as_view(), name="user-attendance"),
    path("clock-in/", views.ClockInView.as_view(), name="clock-in"),
    path("clock-out/", views.ClockOutView.as_view(), name="clock-out"),
    path("<str:attendance_id>/", views.AttendanceDetailView.as_view(), name="attendance-detail"),
]

