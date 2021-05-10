from data_store import DataStore
from typing import List


class CompoundDataStore(DataStore):
    '''
    This data store internally calls multiple other data stores.
    '''

    def __init__(self, data_stores: List[DataStore]):
        super().__init__()
        self._data_stores = data_stores

    def store_member(self, member):
        for data_store in self._data_stores:
            data_store.store_member(member)