from mongoengine.document import Document

class Model(Document):
    meta = { 'abstract': True }
