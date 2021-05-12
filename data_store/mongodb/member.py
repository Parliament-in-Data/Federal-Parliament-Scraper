from mongoengine.fields import StringField, ListField, ReferenceField, URLField, DateTimeField, UUIDField

from persistence.model.model import Model

class Member(Model):
    id = StringField(required=True, primary_key=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    party = StringField(required=True)
    province = StringField(required=True)
    language = StringField(required=True)
    alternative_names = ListField(StringField())
    replaces = ListField(ReferenceField('Member'))
    url = URLField()
    date_of_birth = DateTimeField(required=True)
    gender = StringField(required=True)
    photo_url = URLField()

def wrap_member(func):
    def wrapper(self, member):
        wrapped_member = Member(
            id = member.uuid,
            first_name = member.first_name,
            last_name = member.last_name,
            party = member.party,
            province = member.province,
            language = member.language,
            alternative_names = member.alternative_names,
            replaces = member.replaces,
            url = member.url,
            date_of_birth = member.date_of_birth,
            gender = member.gender,
            photo_url = member.photo_url
        )
        return func(self, wrapped_member)
    return wrapper


