from django.urls import path
from apps.teams import views

app_name = "teams"

urlpatterns = [
    path("", views.TeamListView.as_view(), name="team-list"),
    path("<str:team_id>/", views.TeamDetailView.as_view(), name="team-detail"),
    path("<str:team_id>/members/", views.TeamMembersView.as_view(), name="team-members"),
]

