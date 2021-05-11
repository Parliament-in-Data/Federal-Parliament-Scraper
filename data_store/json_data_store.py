from data_store import DataStore
from os import path, makedirs
from collections import defaultdict
from models.enums import TopicType
import json


class JsonDataStore(DataStore):
    '''
    The JSON file data store.
    '''

    def __init__(self, base_path: str, base_URI: str):
        super().__init__()
        self._base_path = base_path
        self._base_URI = base_URI
        makedirs(base_path, exist_ok=True)

    def store_member(self, member):
        base_path = path.join(self._base_path, "members")
        base_URI_members = f'{self._base_URI}members/'
        resource_name = f'{member.uuid}.json'
        makedirs(base_path, exist_ok=True)

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

    def _json_representation_meeting_topic(self, meeting_topic):
        return {
            'id': meeting_topic.id,
            'title': {'NL': meeting_topic.title.NL, 'FR': meeting_topic.title.FR},
            'votes': [], # TODO
            'questions': [], # TODO
            'legislation': [], # TODO
            #'votes': [vote.to_dict(session_base_URI) for vote in self.votes],
            #'questions': [f'{session_base_URI}{question.uri()}' for question in self.related_questions],
            #'legislation': [f'{session_base_URI}{document.uri()}' for document in self.related_documents]
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
        #makedirs(meeting_dir_path, exist_ok=True) # TODO: not necessary?

        with open(path.join(meeting_dir_path, 'unfolded.json'), 'w') as fp:
            json.dump(map_topics_dict(self._json_representation_meeting_topic), fp, ensure_ascii=False)
