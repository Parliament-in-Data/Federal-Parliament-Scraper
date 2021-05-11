class DataStore:
    '''
    An interface to transparantly store and get data objects.
    '''

    def store_member(self, member):
        raise NotImplementedError()

    def store_meeting(self, meeting):
        raise NotImplementedError()

    def store_legislation(self, legislation):
        raise NotImplementedError()

    def store_question(self, question):
        raise NotImplementedError()
