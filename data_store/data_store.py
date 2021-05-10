class DataStore:
    '''
    An interface to transparantly store and get data objects.
    '''

    def store_member(self, member):
        raise NotImplementedError()
