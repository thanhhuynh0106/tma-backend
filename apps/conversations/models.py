from django.db import models
from mongoengine import Document, fields
from apps.core.models import BaseDocument
from apps.users.models import User


class Conversation(BaseDocument):
    participants = fields.ListField(fields.ReferenceField(User), required=True)
    last_message = fields.StringField(default=None)
    last_message_at = fields.DateTimeField(default=None)
    unread_count = fields.MapField(
        field=fields.IntField(), default={}
    )

    meta = {
        'collection': 'conversations',
        'indexes': [
            'participants',
            'last_message_at',
        ],
        'ordering': ['-created_at'],
    }