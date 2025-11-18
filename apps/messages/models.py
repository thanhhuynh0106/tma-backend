from django.db import models
from mongoengine import fields
from apps.core.models import BaseDocument
from apps.users.models import User
from apps.conversations.models import Conversation


class Attachment(fields.EmbeddedDocument):
    name = fields.StringField(required=True)
    url = fields.StringField(required=True)


class Message(BaseDocument):
    conversation = fields.ReferenceField(Conversation, required=True)
    sender = fields.ReferenceField(User, required=True)
    message = fields.StringField(required=True)
    attachments = fields.EmbeddedDocumentListField(Attachment, default=[])
    is_read = fields.BooleanField(default=False)

    meta = {
        'collection': 'messages',
        'indexes': [
            'conversation',
            'sender',
            'is_read',
        ],
        'ordering': ['-created_at'],
    }