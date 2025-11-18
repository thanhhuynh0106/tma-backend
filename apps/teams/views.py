from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import TeamSerializer
from .services import TeamService
from apps.core.exceptions import AppError


class TeamListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))

        teams = TeamService.list_teams(page=page, page_size=page_size)
        serializer = TeamSerializer(teams, many=True)
        total = teams.count() if hasattr(teams, 'count') else len(teams)
        
        return Response({
            "success": True,
            "data": serializer.data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
            },
        })

    def post(self, request):
        serializer = TeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            team = serializer.save()
            return Response({
                "success": True,
                "data": TeamSerializer(team).data,
            }, status=status.HTTP_201_CREATED)
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class TeamDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, team_id):
        try:
            team = TeamService._get_team(team_id)
            return Response({
                "success": True,
                "data": TeamSerializer(team).data,
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )

    def put(self, request, team_id):
        try:
            team = TeamService._get_team(team_id)
            serializer = TeamSerializer(team, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            updated_team = serializer.save()
            return Response({
                "success": True,
                "data": TeamSerializer(updated_team).data,
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )

    def delete(self, request, team_id):
        try:
            TeamService.delete_team(team_id)
            return Response({
                "success": True,
                "message": "Team deleted successfully",
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class TeamMembersView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, team_id):
        """Add member to team"""
        try:
            user_id = request.data.get("user_id")
            if not user_id:
                return Response(
                    {"success": False, "message": "user_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            team = TeamService.add_member(team_id, user_id)
            return Response({
                "success": True,
                "data": TeamSerializer(team).data,
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )

    def delete(self, request, team_id):
        """Remove member from team"""
        try:
            user_id = request.data.get("user_id")
            if not user_id:
                return Response(
                    {"success": False, "message": "user_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            team = TeamService.remove_member(team_id, user_id)
            return Response({
                "success": True,
                "data": TeamSerializer(team).data,
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )
