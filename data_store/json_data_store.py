from data_store import DataStore
from os import path, makedirs
from collections import defaultdict
from models.enums import TopicType
from models import GenericVote, LanguageGroupVote, ElectronicGenericVote, ElectronicAdvisoryVote
import json


# TODO: split this class using multiple inheritance
class JsonDataStore(DataStore):
    '''
    The JSON file data store.
    '''

    def __init__(self, session, start_date, end_date, base_path: str, base_URI: str):
        super().__init__()
        self._session = session
        self._start_date = start_date
        self._end_date = end_date

        self._base_path = base_path
        self._base_URI = base_URI
        makedirs(base_path, exist_ok=True)

        self._vote_type_to_handler = dict()
        self._vote_type_to_handler[GenericVote] = self._json_representation_generic_vote
        self._vote_type_to_handler[LanguageGroupVote] = self._json_representation_language_group_vote
        self._vote_type_to_handler[ElectronicGenericVote] = self._json_representation_electronic_generic_vote
        self._vote_type_to_handler[ElectronicAdvisoryVote] = self._json_representation_electronic_advisory_vote

        self._legislation_index = dict()
        self._legislation_unfolded = dict()
        self._question_index = dict()
        self._question_unfolded = dict()
        self._meeting_URIs = []
        self._member_URIs = []

    def finish(self):
        with open(path.join(self._base_path, 'legislation', 'index.json'), 'w') as fp:
            json.dump(self._legislation_index, fp)

        with open(path.join(self._base_path, 'questions', 'index.json'), 'w') as fp:
            json.dump(self._question_index, fp)

        with open(path.join(self._base_path, 'legislation', 'unfolded.json'), 'w') as fp:
            json.dump(self._legislation_unfolded, fp)

        with open(path.join(self._base_path, 'questions', 'unfolded.json'), 'w') as fp:
            json.dump(self._question_unfolded, fp)

        with open(path.join(self._base_path, 'session.json'), 'w') as fp:
            json.dump({
                'id': self._session,
                'start': self._start_date,
                'end': self._end_date,
                'members': self._member_URIs,
                'legislation': f'{self._base_URI}legislation/index.json',
                'questions': f'{self._base_URI}questions/index.json',
                'meetings': {'plenary': self._meeting_URIs}}, fp)

    def store_member(self, member):
        base_path = path.join(self._base_path, "members")
        base_URI_members = f'{self._base_URI}members/'
        resource_name = f'{member.uuid}.json'
        makedirs(base_path, exist_ok=True)

        self._member_URIs.append(f'{base_URI_members}{resource_name}')

        with open(path.join(base_path, resource_name), 'w') as fp:
            replaces = list(map(lambda replacement: {
                            'member': f'{base_URI_members}{replacement["member"]}.json', 'dates': replacement['dates']}, member.replaces))
            activity_dict = defaultdict(lambda: defaultdict(list))
            # TODO: fix activities
            #for activity in member.activities:
            #    activity_dict[str(activity.date.year)][str(
            #        activity.date.isoformat())].append(activity.dict(base_URI))
            activities_dir = path.join(base_path, str(member.uuid))
            makedirs(activities_dir, exist_ok=True)

            activity_uris = {}

            for year in activity_dict:
                with open(path.join(activities_dir, f'{year}.json'), 'w') as afp:
                    json.dump(activity_dict[year], afp)
                activity_uris[year] = f'{base_URI_members}{member.uuid}/{year}.json'

            json.dump({
                'id': str(member.uuid),
                'first_name': member.first_name,
                'last_name': member.last_name,
                'gender': member.gender,
                'date_of_birth': member.date_of_birth.isoformat(),
                'language': member.language,
                'province': member.province,
                'party': member.party,
                'wiki': member.url,
                'replaces': replaces,
                'activities': activity_uris,
                'photo_url': member.photo_url
            }, fp, ensure_ascii=False)

    def _get_member_uri(self, member):
        return f'{self._base_URI}members/{member.uuid}.json'

    def _json_representation_generic_vote(self, vote):
        return {
            'id': vote.vote_number,
            'type': 'generic',
            'yes': vote.yes,
            'no': vote.no,
            'abstention': vote.abstention,
            'unsure': vote.unsure,
            'passed': vote.has_passed(),
            'voters': {
                'yes': list(map(self._get_member_uri, vote.yes_voters)),
                'no': list(map(self._get_member_uri, vote.yes_voters)),
                'abstention': list(map(self._get_member_uri, vote.yes_voters)),
            }
        }

    def _json_representation_language_group_vote(self, vote):
        data = self._json_representation_generic_vote(vote)
        data['detail'] = {
            'NL': self._json_representation_generic_vote(vote.vote_NL),
            'FR': self._json_representation_generic_vote(vote.vote_FR),
        }
        return data

    def _json_representation_electronic_generic_vote(self, vote):
        return {
            'id': vote.vote_number,
            'type': 'electronic_generic',
            'yes': vote.yes,
            'no': vote.no,
            'passed': vote.has_passed(),
        }

    def _json_representation_electronic_advisory_vote(self, vote):
        return {
            'id': vote.vote_number,
            'type': 'electronic_advisory',
            'yes': vote.yes,
            'passed': vote.has_passed(),
        }

    def _json_representation_votes(self, vote):
        return self._vote_type_to_handler[type(vote)](vote)

    def store_legislation(self, legislation):
        legislation_dir_path = path.join(self._base_path, 'legislation')
        makedirs(legislation_dir_path, exist_ok=True)
        data = {
            'document_number': legislation.document_nr,
            'document_type': legislation.document_type,
            'title': legislation.title,
            'source': legislation.source,
            'date': legislation.date.isoformat(),
            'authors': list(map(self._get_member_uri, legislation.authors)),
            'descriptor': legislation.descriptor,
            'keywords': legislation.keywords,
        }
        self._legislation_unfolded[legislation.document_nr] = data
        with open(path.join(legislation_dir_path, f'{legislation.document_nr}.json'), 'w') as fp:
            json.dump(data, fp, ensure_ascii=False)

    def store_question(self, question):
        question_dir_path = path.join(self._base_path, 'questions')
        makedirs(question_dir_path, exist_ok=True)
        data = {
            'document_number': question.document_nr,
            'title': question.title,
            'source': question.source,
            'date': question.date.isoformat(),
            'responding_minister': question.responding_minister,
            'responding_department': question.responding_department,
            'authors': list(map(self._get_member_uri, question.authors)),
        }
        self._question_unfolded[question.document_nr] = data
        with open(path.join(question_dir_path, f'{question.document_nr}.json'), 'w') as fp:
            json.dump(data, fp, ensure_ascii=False)

    def _legislation_uri(self, legislation):
        uri = f'{self._base_URI}legislation/{legislation.document_nr}.json'
        self._legislation_index[legislation.document_nr] = uri
        return uri

    def _question_uri(self, question):
        uri = f'{self._base_URI}questions/{question.document_nr}.json'
        self._question_index[question.document_nr] = uri
        return uri

    def _json_representation_meeting_topic(self, meeting_topic):
        return {
            'id': meeting_topic.id,
            'title': {'NL': meeting_topic.title.NL, 'FR': meeting_topic.title.FR},
            'votes': list(map(self._json_representation_votes, meeting_topic.votes)),
            'questions': list(map(self._question_uri, meeting_topic.questions)),
            'legislation': list(map(self._legislation_uri, meeting_topic.legislations)),
        }

    def _store_meeting_topic(self, meeting_topic):
        topic_path = path.join(self._base_path, 'meetings', str(meeting_topic.meeting_id))
        makedirs(topic_path, exist_ok=True)

        with open(path.join(topic_path, f'{meeting_topic.id}.json'), 'w') as fp:
            json.dump(self._json_representation_meeting_topic(meeting_topic), fp, ensure_ascii=False)

        return f'{self._base_URI}meetings/{meeting_topic.meeting_id}/{meeting_topic.id}.json'

    def store_meeting(self, meeting):
        base_meeting_path = path.join(self._base_path, "meetings")
        base_meeting_URI = f'{self._base_URI}meetings/'
        resource_name = f'{meeting.id}.json'

        makedirs(base_meeting_path, exist_ok=True)

        self._meeting_URIs.append(f'{base_meeting_URI}{resource_name}')

        def map_topics_dict(f):
            return {
                str(TopicType(topic_type)): {
                    topic_id: f(topic)
                    for topic_id, topic in topic_type_dict.items()
                }
                for topic_type, topic_type_dict in meeting.topics.items()
            }

        with open(path.join(base_meeting_path, resource_name), 'w') as fp:
            json.dump({
                'id': meeting.id,
                'time_of_day': str(meeting.time_of_day),
                'date': meeting.date.isoformat(),
                'topics': map_topics_dict(self._store_meeting_topic),
            }, fp, ensure_ascii=False)

        meeting_dir_path = path.join(base_meeting_path, str(meeting.id))
        with open(path.join(meeting_dir_path, 'unfolded.json'), 'w') as fp:
            json.dump(map_topics_dict(self._json_representation_meeting_topic), fp, ensure_ascii=False)
