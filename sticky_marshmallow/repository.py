import datetime
from bson import ObjectId

from sticky_marshmallow.core import Core

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


class Repository(Core, metaclass=BaseRepository):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            schema = self.Meta.schema()
            self._collection = self._get_collection_from_schema(schema)

        return self._collection

    def _get_primary_key_filter(self, document):
        primary_key_fields = getattr(self.Meta, "primary_key", ["id"])
        filter = {k: document[k] for k in primary_key_fields}
        if "id" in filter:
            filter["_id"] = ObjectId(filter.pop("id"))
        return filter

    def _save_recursive(self, schema, obj):
        dates = {
            k: v
            for k, v in obj.__dict__.items()
            if isinstance(v, datetime.datetime)
        }
        document = {**schema.dump(obj), **dates}
        for field_name, field in self._get_reference_fields(schema).items():
            reference_field = getattr(obj, field_name)
            if reference_field is not None:
                if isinstance(reference_field, list):
                    document[field_name] = [
                        self._save_recursive(
                            field.schema.__class__(many=False), item
                        )["_id"]
                        for item in reference_field
                    ]
                else:
                    document[field_name] = self._save_recursive(
                        field.schema, reference_field
                    )["_id"]
        filter = self._get_primary_key_filter(document)
        result = self._get_collection_from_schema(schema).update_one(
            filter, {"$set": document}, upsert=True
        )
        obj_id = (
            result.upserted_id
            if hasattr(result, "upserted_id")
            else (
                result.inserted_id if hasattr(result, "inserted_id") else None
            )
        ) or document.pop("id", None)
        if hasattr(obj, "id"):
            obj.id = str(obj_id) if obj_id else None
        document["_id"] = obj_id
        return document

    def get(self, id=None, **filter):
        schema = self.Meta.schema()
        if id is not None:
            filter["_id"] = ObjectId(id)
        count = self.collection.count_documents(filter)
        if count > 1:
            raise self.MultipleObjectsReturned()
        if count == 0:
            raise self.DoesNotExist()
        document = self.collection.find_one(filter)
        return self._to_object(schema, document)

    def find(self, **filter):
        schema = self.Meta.schema()
        return Cursor(schema=schema, collection=self.collection, filter=filter)

    def save(self, obj):
        self._save_recursive(schema=self.Meta.schema(), obj=obj)
        return obj

    def delete(self, obj):
        self.collection.delete_one({"_id": ObjectId(obj.id)})

    def delete_many(self, **filter):
        self.collection.delete_many(filter)
