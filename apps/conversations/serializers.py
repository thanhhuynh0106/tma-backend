from rest_framework import fields as drf_fields, serializers as drf_serializers
from rest_framework_mongoengine import serializers as mongo_serializers
from rest_framework_mongoengine.fields import ReferenceField
from apps.conversations.models import Conversation
from apps.users.models import User


class ConversationSerializer(mongo_serializers.DocumentSerializer):
    participants = drf_fields.ListField(
        child=ReferenceField(read_only=True),
        read_only=True,
    )
    participant_ids = drf_fields.ListField(
        child=drf_fields.CharField(),
        write_only=True,
        min_length=2,
    )
    unread_count = drf_fields.DictField(
        child=drf_fields.IntegerField(min_value=0), required=False
    )

    class Meta:
        model = Conversation
        fields = (
            'id',
            'participants',
            'participant_ids',
            'last_message',
            'last_message_at',
            'unread_count',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'participants', 'last_message_at', 'created_at', 'updated_at')

    def _get_user(self, user_id: str) -> User:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist as exc:
            raise drf_serializers.ValidationError(
                {'detail': f'User with id {user_id} not found'}
            ) from exc

    def create(self, validated_data):
        participant_ids = validated_data.pop('participant_ids', [])
        if len(participant_ids) < 2:
            raise drf_serializers.ValidationError(
                {'participant_ids': 'Conversation requires at least two participants.'}
            )
        participants = [self._get_user(pid) for pid in participant_ids]
        validated_data['participants'] = participants

        conversation = Conversation(**validated_data)
        conversation.save()
        return conversation

    def update(self, instance, validated_data):
        participant_ids = validated_data.pop('participant_ids', None)
        if participant_ids is not None:
            if len(participant_ids) < 2:
                raise drf_serializers.ValidationError(
                    {'participant_ids': 'Conversation requires at least two participants.'}
                )
            instance.participants = [self._get_user(pid) for pid in participant_ids]

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

