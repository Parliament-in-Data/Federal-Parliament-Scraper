from mongoengine.document import Document, EmbeddedDocument

class Model(Document):
    meta = { 'abstract': True }

class CompoundKey(EmbeddedDocument):
    meta = { 'abstract': True }
