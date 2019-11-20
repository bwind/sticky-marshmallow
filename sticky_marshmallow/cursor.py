from sticky_marshmallow.core import _to_object


class Cursor:
    def __init__(self, schema, pymongo_cursor):
        self._schema = schema
        self._pymongo_cursor = pymongo_cursor

    def __iter__(self):
        return self

    def __next__(self):
        document = next(self._pymongo_cursor)
        return _to_object(self._schema, document)
