from typing import List, Optional

from mongoengine.queryset import QuerySet

from apps.conversations.models import Conversation
from apps.users.models import User
from apps.core.exceptions import NotFoundError, ValidationError


class ConversationService:
    """Business logic cho Conversation."""

    @staticmethod
    def _get_user(user_id: str) -> User:
        user = User.objects(id=user_id).first()
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user

    @staticmethod
    def _get_conversation(conversation_id: str) -> Conversation:
        conversation = Conversation.objects(id=conversation_id).first()
        if not conversation:
            raise NotFoundError(f"Conversation {conversation_id} not found")
        return conversation

    # --------- CRUD ---------
    @staticmethod
    def list_conversations(user_id: Optional[str] = None, page: int = 1, page_size: int = 20) -> QuerySet:
        query = {}
        if user_id:
            user = ConversationService._get_user(user_id)
            query["participants"] = user

        skip = (page - 1) * page_size
        return Conversation.objects(**query).skip(skip).limit(page_size).order_by("-last_message_at")

    @staticmethod
    def create_conversation(participant_ids: List[str]) -> Conversation:
        if len(set(participant_ids)) < 2:
            raise ValidationError("Conversation requires at least two participants")

        participants = [ConversationService._get_user(pid) for pid in participant_ids]
        conversation = Conversation(participants=participants)
        conversation.save()
        return conversation

    @staticmethod
    def update_last_message(conversation_id: str, message: str) -> Conversation:
        conversation = ConversationService._get_conversation(conversation_id)
        conversation.last_message = message
        conversation.last_message_at = conversation.updated_at
        conversation.save()
        return conversation

    @staticmethod
    def add_participant(conversation_id: str, user_id: str) -> Conversation:
        conversation = ConversationService._get_conversation(conversation_id)
        user = ConversationService._get_user(user_id)

        if user in conversation.participants:
            raise ValidationError("User already in conversation")

        conversation.participants.append(user)
        conversation.save()
        return conversation

    @staticmethod
    def remove_participant(conversation_id: str, user_id: str) -> Conversation:
        conversation = ConversationService._get_conversation(conversation_id)
        if len(conversation.participants) <= 2:
            raise ValidationError("Conversation must have at least two participants")

        conversation.participants = [
            participant
            for participant in conversation.participants
            if str(participant.id) != str(user_id)
        ]
        conversation.save()
        return conversation

