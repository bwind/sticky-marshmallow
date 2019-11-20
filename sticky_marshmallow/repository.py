from bson import ObjectId

from sticky_marshmallow.core import (
    _get_collection_from_schema,
    _get_reference_fields,
    _to_object,
)

from sticky_marshmallow.cursor import Cursor


__all__ = ["Repository"]


class DoesNotExist(Exception):
    pass


class MultipleObjectsReturned(Exception):
    pass


class Meta(object):
    schema = None


class BaseRepository(type):
    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)

        # If new_class is of type Repository, return straight away
        if object in new_class.__bases__:
            return new_class

        # Merge exceptions
        classes_to_merge = (DoesNotExist, MultipleObjectsReturned)
        for c in classes_to_merge:
            exc = type(c.__name__, (c,), {"__module__": name})
            setattr(new_class, c.__name__, exc)

        # Merge Meta
        m_name = Meta.__name__

        # Get user defined Meta data
        meta_data = {}
        if hasattr(new_class, m_name):
            meta_data = dict(
                [
                    (k, getattr(new_class.Meta, k))
                    for k in dir(new_class.Meta)
                    if not k.startswith("_")
                ]
            )

        # Merge Meta class and set user defined data
        meta = type(m_name, (Meta,), {"__module__": name})
        setattr(new_class, m_name, meta)
        for k, v in meta_data.items():
            setattr(new_class.Meta, k, v)

        return new_class


class Repository(metaclass=BaseRepository):
    def _save_recursive(self, schema, obj):
        document = schema.dump(obj)
        for field_name, field in _get_reference_fields(schema).items():
            if getattr(obj, field_name) is not None:
                document[field_name] = self._save_recursive(
                    field.schema, getattr(obj, field_name)
                )["_id"]
        document["_id"] = ObjectId(document.pop("id"))
        result = _get_collection_from_schema(schema).update_one(
            {"_id": document["_id"]}, {"$set": document}, upsert=True
        )
        if obj.id is None:
            if hasattr(result, "upserted_id"):
                obj.id = str(result.upserted_id)
            elif hasattr(result, "inserted_id"):
                obj.id = str(result.inserted_id)
        return document

    def to_mongo(self, obj):
        pass

    def get(self, id=None, **filter):
        if id is not None:
            filter["_id"] = ObjectId(id)
        schema = self.Meta.schema()
        collection = _get_collection_from_schema(schema)
        count = collection.count_documents(filter)
        if count > 1:
            raise self.MultipleObjectsReturned()
        if count == 0:
            raise self.DoesNotExist()
        document = collection.find_one(filter)
        return _to_object(schema, document)

    def find(self, **filter):
        schema = self.Meta.schema()
        pymongo_cursor = _get_collection_from_schema(schema).find(filter)
        return Cursor(schema=schema, pymongo_cursor=pymongo_cursor)

    def save(self, obj):
        self._save_recursive(schema=self.Meta.schema(), obj=obj)

    def delete(self, obj):
        pass

    def delete_many(self, **filter):
        _get_collection_from_schema(self.Meta.schema).delete_many(filter)
