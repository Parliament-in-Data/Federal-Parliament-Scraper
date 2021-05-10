from data_store import DataStore
from os import path, makedirs
from collections import defaultdict
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
            for activity in member.activities:
                activity_dict[str(activity.date.year)][str(
                    activity.date.isoformat())].append(activity.dict(base_URI))
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