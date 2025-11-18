from rest_framework import fields as drf_fields, serializers as drf_serializers
from rest_framework_mongoengine import serializers as mongo_serializers
from rest_framework_mongoengine.fields import ReferenceField
from apps.messages.models import Message, Attachment
from apps.users.models import User
from apps.conversations.models import Conversation


class AttachmentSerializer(mongo_serializers.EmbeddedDocumentSerializer):
    class Meta:
        model = Attachment
        fields = ('name', 'url')


class MessageSerializer(mongo_serializers.DocumentSerializer):
    attachments = AttachmentSerializer(many=True, required=False)
    conversation = ReferenceField(read_only=True)
    sender = ReferenceField(read_only=True)

    conversation_id = drf_fields.CharField(write_only=True)
    sender_id = drf_fields.CharField(write_only=True)

    class Meta:
        model = Message
        fields = (
            'id',
            'conversation',
            'conversation_id',
            'sender',
            'sender_id',
            'message',
            'attachments',
            'is_read',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'conversation', 'sender', 'created_at', 'updated_at')

    def _get_conversation(self, conversation_id: str) -> Conversation:
        try:
            return Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist as exc:
            raise drf_serializers.ValidationError(
                {'conversation_id': f'Conversation {conversation_id} not found'}
            ) from exc

    def _get_user(self, user_id: str) -> User:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist as exc:
            raise drf_serializers.ValidationError(
                {'sender_id': f'User {user_id} not found'}
            ) from exc

    def create(self, validated_data):
        attachments_data = validated_data.pop('attachments', [])
        conversation_id = validated_data.pop('conversation_id')
        sender_id = validated_data.pop('sender_id')

        validated_data['conversation'] = self._get_conversation(conversation_id)
        validated_data['sender'] = self._get_user(sender_id)

        message = Message(**validated_data)
        if attachments_data:
            message.attachments = [Attachment(**att) for att in attachments_data]
        message.save()
        return message

    def update(self, instance, validated_data):
        attachments_data = validated_data.pop('attachments', None)
        conversation_id = validated_data.pop('conversation_id', None)
        sender_id = validated_data.pop('sender_id', None)

        if conversation_id:
            instance.conversation = self._get_conversation(conversation_id)
        if sender_id:
            instance.sender = self._get_user(sender_id)

        if attachments_data is not None:
            instance.attachments = [Attachment(**att) for att in attachments_data]

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

