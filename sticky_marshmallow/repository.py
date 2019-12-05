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

    def _save_recursive(self, schema, obj):
        document = schema.dump(obj)
        for field_name, field in self._get_reference_fields(schema).items():
            if getattr(obj, field_name) is not None:
                document[field_name] = self._save_recursive(
                    field.schema, getattr(obj, field_name)
                )["_id"]
        document["_id"] = ObjectId(document.pop("id"))
        result = self.collection.update_one(
            {"_id": document["_id"]}, {"$set": document}, upsert=True
        )
        if obj.id is None:
            if hasattr(result, "upserted_id"):
                obj.id = str(result.upserted_id)
            elif hasattr(result, "inserted_id"):
                obj.id = str(result.inserted_id)
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
        self.collection.delete_one(
            {"_id": ObjectId(obj.id)}
        )

    def delete_many(self, **filter):
        self.collection.delete_many(filter)
