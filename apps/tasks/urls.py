from django.urls import path
from apps.tasks import views

app_name = "tasks"

urlpatterns = [
    path("", views.TaskListView.as_view(), name="task-list"),
    path("<str:task_id>/", views.TaskDetailView.as_view(), name="task-detail"),
    path("<str:task_id>/status/", views.TaskStatusView.as_view(), name="task-status"),
    path("<str:task_id>/comment/", views.TaskCommentView.as_view(), name="task-comment"),
    path("<str:task_id>/attachment/", views.TaskAttachmentView.as_view(), name="task-attachment"),
]

