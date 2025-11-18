from django.urls import path
from apps.conversations import views

app_name = "conversations"

urlpatterns = [
    path("", views.ConversationListView.as_view(), name="conversation-list"),
    path("<str:conversation_id>/", views.ConversationDetailView.as_view(), name="conversation-detail"),
]

