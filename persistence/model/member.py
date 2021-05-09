from mongoengine.fields import StringField, ListField, ReferenceField, URLField, DateTimeField

from persistence.model.model import Model
from persistence.model.activity import Activity

class Member(Model):
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    party = StringField(required=True)
    province = StringField(required=True)
    language = StringField(required=True)
    alternative_names = ListField(StringField())
    replaces = ListField(ReferenceField(Member))
    activities = ListField(ReferenceField(Activity))
    url = URLField()
    date_of_birth = DateTimeField(required=True)
    gender = StringField(required=True)
    photo_url = URLField()
