from rest_framework import fields as drf_fields, serializers as drf_serializers
from rest_framework_mongoengine import serializers as mongo_serializers

from apps.teams.models import Team
from apps.users.models import User
from rest_framework_mongoengine.fields import ReferenceField

class TeamSerializer(mongo_serializers.DocumentSerializer):
    """
    Serializer cho Team document.
    - leader_id & member_ids dùng để ghi (write-only)
    - leader & members dùng để đọc (read-only)
    """

    leader = ReferenceField(read_only=True, source='leaderId')
    members = drf_fields.ListField(
        child=ReferenceField(read_only=True), source='memberIds', read_only=True
    )

    leader_id = drf_fields.CharField(write_only=True, required=True)
    member_ids = drf_fields.ListField(
        child=drf_fields.CharField(),
        write_only=True,
        required=False,
        allow_empty=True,
        default=list,
    )

    class Meta:
        model = Team
        fields = (
            'id',
            'name',
            'description',
            'leader',
            'leader_id',
            'members',
            'member_ids',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'leader', 'members', 'created_at', 'updated_at')

    def _get_user(self, user_id: str) -> User:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist as exc:
            raise drf_serializers.ValidationError(
                {'detail': f'User with id {user_id} not found'}
            ) from exc

    def create(self, validated_data):
        leader_id = validated_data.pop('leader_id')
        member_ids = validated_data.pop('member_ids', [])

        validated_data['leaderId'] = self._get_user(leader_id)
        validated_data['memberIds'] = [self._get_user(mid) for mid in member_ids]

        team = Team(**validated_data)
        team.save()
        return team

    def update(self, instance, validated_data):
        leader_id = validated_data.pop('leader_id', None)
        member_ids = validated_data.pop('member_ids', None)

        if leader_id:
            instance.leaderId = self._get_user(leader_id)

        if member_ids is not None:
            instance.memberIds = [self._get_user(mid) for mid in member_ids]

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

