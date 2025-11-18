from django.urls import path
from apps.notifications import views

app_name = "notifications"

urlpatterns = [
    path("", views.NotificationListView.as_view(), name="notification-list"),
    path("<str:notification_id>/", views.NotificationDetailView.as_view(), name="notification-detail"),
    path("<str:notification_id>/read/", views.NotificationMarkReadView.as_view(), name="notification-mark-read"),
]

