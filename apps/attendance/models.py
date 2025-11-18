from django.db import models
from mongoengine import fields
from apps.core.models import BaseDocument
from apps.users.models import User


class Location(fields.EmbeddedDocument):
    lat = fields.FloatField(required=True)
    lng = fields.FloatField(required=True)

class Attendance(BaseDocument):
    user = fields.ReferenceField(User, required=True)
    date = fields.DateField(required=True)
    clock_in = fields.DateTimeField(required=True)
    clock_out = fields.DateTimeField(default=None)
    location = fields.EmbeddedDocumentField(Location, required=True)
    status = fields.StringField(
        choices=('present', 'late', 'absent'), required=True
    )
    work_hours = fields.FloatField(default=0.0)

    meta = {
        'collection': 'attendances',
        'indexes': [
            'user',
            'date',
        ],
        'ordering': ['-created_at'],
    }