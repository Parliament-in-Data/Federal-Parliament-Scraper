from persistence.controller.controller import Controller
from persistence.model.member import Member

class MemberController(Controller):
    def create(self, **kwargs):
        Member(
            id=kwargs.id,
            first_name=kwargs.first_name,
            last_name=kwargs.last_name,
            party=kwargs.party,
            province=kwargs.province,
            language=kwargs.language,
            alternative_names=kwargs.alternative_names,
            replaces=kwargs.replaces,
            activities=kwargs.activities,
            url=kwargs.url,
            date_of_birth=kwargs.date_of_birth,
            gender=kwargs.gender,
            photo_url=kwargs.photo_url
        ).save()
