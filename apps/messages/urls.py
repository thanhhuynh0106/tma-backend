from django.urls import path
from apps.messages import views

app_name = "messages"

urlpatterns = [
    path("conversations/<str:conversation_id>/", views.MessageListView.as_view(), name="message-list"),
    path("<str:message_id>/", views.MessageDetailView.as_view(), name="message-detail"),
    path("<str:message_id>/read/", views.MessageMarkReadView.as_view(), name="message-mark-read"),
]

