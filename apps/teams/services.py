from typing import List, Optional

from mongoengine.queryset import QuerySet

from apps.teams.models import Team
from apps.users.models import User
from apps.core.exceptions import NotFoundError, ValidationError


class TeamService:
    """Business logic cho Team."""

    # --------- Helpers ---------
    @staticmethod
    def _get_user(user_id: str) -> User:
        user = User.objects(id=user_id).first()
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user

    @staticmethod
    def _get_team(team_id: str) -> Team:
        team = Team.objects(id=team_id).first()
        if not team:
            raise NotFoundError(f"Team {team_id} not found")
        return team

    # --------- CRUD ---------
    @staticmethod
    def list_teams(page: int = 1, page_size: int = 20) -> QuerySet:
        skip = (page - 1) * page_size
        return Team.objects.skip(skip).limit(page_size).order_by("-created_at")

    @staticmethod
    def create_team(name: str, leader_id: str, description: str = "", member_ids: Optional[List[str]] = None) -> Team:
        if Team.objects(name=name).first():
            raise ValidationError(f"Team name '{name}' already exists")

        leader = TeamService._get_user(leader_id)
        members = [TeamService._get_user(uid) for uid in (member_ids or [])]

        team = Team(
            name=name,
            description=description,
            leaderId=leader,
            memberIds=members,
        )
        team.save()
        return team

    @staticmethod
    def update_team(team_id: str, **data) -> Team:
        team = TeamService._get_team(team_id)

        if "name" in data and data["name"] != team.name:
            if Team.objects(name=data["name"]).first():
                raise ValidationError(f"Team name '{data['name']}' already exists")

        if "leader_id" in data:
            team.leaderId = TeamService._get_user(data.pop("leader_id"))

        if "member_ids" in data:
            team.memberIds = [TeamService._get_user(uid) for uid in data.pop("member_ids")]

        for attr, value in data.items():
            setattr(team, attr, value)

        team.save()
        return team

    @staticmethod
    def delete_team(team_id: str) -> None:
        team = TeamService._get_team(team_id)
        team.delete()

    # --------- Members management ---------
    @staticmethod
    def add_member(team_id: str, user_id: str) -> Team:
        team = TeamService._get_team(team_id)
        user = TeamService._get_user(user_id)

        if user in team.memberIds:
            raise ValidationError("User already in team")

        team.memberIds.append(user)
        team.save()
        return team

    @staticmethod
    def remove_member(team_id: str, user_id: str) -> Team:
        team = TeamService._get_team(team_id)
        user = TeamService._get_user(user_id)

        team.memberIds = [member for member in team.memberIds if str(member.id) != str(user.id)]
        team.save()
        return team

    @staticmethod
    def change_leader(team_id: str, new_leader_id: str) -> Team:
        team = TeamService._get_team(team_id)
        new_leader = TeamService._get_user(new_leader_id)

        team.leaderId = new_leader
        team.save()
        return team

