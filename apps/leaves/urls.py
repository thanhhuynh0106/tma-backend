from django.urls import path
from apps.leaves import views

app_name = "leaves"

urlpatterns = [
    path("", views.LeaveListView.as_view(), name="leave-list"),
    path("me/", views.MyLeaveView.as_view(), name="my-leave"),
    # detail, update, delete
    path("<str:leave_id>/", views.LeaveDetailView.as_view(), name="leave-detail"),

    # approval, reject
    path("<str:leave_id>/approve/", views.LeaveApprovalView.as_view(), name="leave-approve"),
    path("<str:leave_id>/reject/", views.LeaveRejectionView.as_view(), name="leave-reject"),
]