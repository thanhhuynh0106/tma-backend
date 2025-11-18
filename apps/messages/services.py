from typing import List, Optional, Dict

from mongoengine.queryset import QuerySet

from apps.messages.models import Message, Attachment
from apps.users.models import User
from apps.conversations.models import Conversation
from apps.core.exceptions import NotFoundError, ValidationError


class MessageService:
    """Business logic cho Message."""

    @staticmethod
    def _get_message(message_id: str) -> Message:
        message = Message.objects(id=message_id).first()
        if not message:
            raise NotFoundError(f"Message {message_id} not found")
        return message

    @staticmethod
    def _get_conversation(conversation_id: str) -> Conversation:
        conversation = Conversation.objects(id=conversation_id).first()
        if not conversation:
            raise NotFoundError(f"Conversation {conversation_id} not found")
        return conversation

    @staticmethod
    def _get_user(user_id: str) -> User:
        user = User.objects(id=user_id).first()
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user

    # --------- CRUD ---------
    @staticmethod
    def list_messages(conversation_id: str, page: int = 1, page_size: int = 20) -> QuerySet:
        conversation = MessageService._get_conversation(conversation_id)
        skip = (page - 1) * page_size
        return Message.objects(conversation=conversation).skip(skip).limit(page_size).order_by("-created_at")

    @staticmethod
    def send_message(
        conversation_id: str,
        sender_id: str,
        message: str,
        attachments: Optional[List[Dict[str, str]]] = None,
    ) -> Message:
        conversation = MessageService._get_conversation(conversation_id)
        sender = MessageService._get_user(sender_id)

        if sender not in conversation.participants:
            raise ValidationError("Sender is not part of the conversation")

        msg = Message(
            conversation=conversation,
            sender=sender,
            message=message,
        )

        if attachments:
            msg.attachments = [Attachment(**data) for data in attachments]

        msg.save()
        conversation.last_message = message
        conversation.last_message_at = msg.created_at
        conversation.save()

        return msg

    @staticmethod
    def mark_as_read(message_id: str) -> Message:
        message = MessageService._get_message(message_id)
        message.is_read = True
        message.save()
        return message

    @staticmethod
    def mark_conversation_messages_as_read(conversation_id: str, user_id: str) -> None:
        conversation = MessageService._get_conversation(conversation_id)
        user = MessageService._get_user(user_id)

        if user not in conversation.participants:
            raise ValidationError("User not part of conversation")

        Message.objects(conversation=conversation, sender__ne=user, is_read=False).update(is_read=True)

