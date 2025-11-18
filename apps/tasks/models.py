from django.db import models
from mongoengine import Document, fields
from datetime import datetime
from apps.core.models import BaseDocument
from apps.users.models import User


class Attachment(fields.EmbeddedDocument):
    name = fields.StringField(required=True)
    url = fields.StringField(required=True)


class Comment(fields.EmbeddedDocument):
    user = fields.ReferenceField(User, required=True)
    text = fields.StringField(required=True)
    created_at = fields.DateTimeField(default=datetime.utcnow)


class Task(BaseDocument):
    STATUS_CHOICES = ('todo', 'in_progress', 'done')
    PRIORITY_CHOICES = ('low', 'medium', 'high')

    title = fields.StringField(required=True)
    description = fields.StringField(default='')
    status = fields.StringField(choices=STATUS_CHOICES, default='todo')
    priority = fields.StringField(choices=PRIORITY_CHOICES, default='medium')
    assigned_to = fields.ListField(fields.ReferenceField(User))
    assigned_by = fields.ReferenceField(User, required=True)
    team_id = fields.ObjectIdField(required=True)
    start_date = fields.DateTimeField()
    due_date = fields.DateTimeField()
    progress = fields.IntField(min_value=0, max_value=100, default=0)
    attachments = fields.EmbeddedDocumentListField(Attachment)
    comments = fields.EmbeddedDocumentListField(Comment)
    tags = fields.ListField(fields.StringField())

    meta = {
        'collection': 'tasks',
        'indexes': ['status', 'priority', 'assigned_to', 'team_id'],
        'strict': False
    }