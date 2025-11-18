from django.db import models
from mongoengine import Document, fields
from apps.core.models import BaseDocument
from apps.users.models import User


class Team(BaseDocument):
    name = fields.StringField(required=True, trim=True)
    description = fields.StringField(default='')
    leaderId = fields.ReferenceField(User, required=True)
    memberIds = fields.ListField(fields.ReferenceField(User))
    
    meta = {
        'collection': 'teams',
        'indexes': ['name', 'leaderId'],
        'strict': False
    }