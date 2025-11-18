from rest_framework import fields as drf_fields, serializers as drf_serializers
from rest_framework_mongoengine import serializers as mongo_serializers
from rest_framework_mongoengine.fields import ReferenceField
from apps.notifications.models import Notification
from apps.users.models import User


class NotificationSerializer(mongo_serializers.DocumentSerializer):
    user = ReferenceField(read_only=True)
    user_id = drf_fields.CharField(write_only=True)

    class Meta:
        model = Notification
        fields = (
            'id',
            'user',
            'user_id',
            'type',
            'title',
            'message',
            'related_id',
            'is_read',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

    def _get_user(self, user_id: str) -> User:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist as exc:
            raise drf_serializers.ValidationError(
                {'user_id': f'User {user_id} not found'}
            ) from exc

    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        validated_data['user'] = self._get_user(user_id)
        notification = Notification(**validated_data)
        notification.save()
        return notification

    def update(self, instance, validated_data):
        user_id = validated_data.pop('user_id', None)
        if user_id:
            instance.user = self._get_user(user_id)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

