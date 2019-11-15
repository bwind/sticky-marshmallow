import inspect

from bson import ObjectId

from marshmallow import fields
from sticky_marshmallow.connection import get_db

# from sticky_marshmallow.cursor import Cursor
from sticky_marshmallow.utils.case import snake_case


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
    def _get_db(self):
        return get_db()

    def _get_reference_fields(self, schema):
        return {
            field_name: field
            for field_name, field, in schema._declared_fields.items()
            if isinstance(field, fields.Nested)
            and "id" in field.schema._declared_fields
        }

    def _dereference(self, schema, document):
        if document is None:
            return
        for field_name, field in self._get_reference_fields(schema).items():
            nested_document = self.get_collection(field.schema).find_one(
                {"_id": ObjectId(document[field_name])}
            )
            document[field_name] = self._dereference(
                field.schema, nested_document
            )
        document["id"] = str(document.pop("_id"))
        return document

    def _meta(self, schema, name):
        if hasattr(schema, "Meta"):
            return getattr(schema.Meta, name, None)

    def _save_recursive(self, schema, obj):
        document = schema.dump(obj)
        for field_name, field in self._get_reference_fields(schema).items():
            if getattr(obj, field_name) is not None:
                document[field_name] = self._save_recursive(
                    field.schema, getattr(obj, field_name)
                )["_id"]
        document["_id"] = ObjectId(document.pop("id"))
        result = self.get_collection(schema).update_one(
            {"_id": document["_id"]}, {"$set": document}, upsert=True
        )
        if obj.id is None:
            if hasattr(result, "upserted_id"):
                obj.id = str(result.upserted_id)
            elif hasattr(result, "inserted_id"):
                obj.id = str(result.inserted_id)
        return document

    def get_collection(self, schema):
        return self._get_db()[self.get_collection_name(schema)]

    def get_collection_name(self, schema):
        if self._meta(schema, "collection"):
            return self._meta("collection")
        # Allows both the schema class and an instance to be passed
        if inspect.isclass(schema):
            cls_name = schema.__name__
        else:
            cls_name = schema.__class__.__name__
        collection_name = snake_case(cls_name.replace("Schema", ""))
        return collection_name

    def to_mongo(self, obj):
        pass

    def to_object(self, schema, document):
        return schema.load(document)

    def get(self, id=None, **filter):
        if id is not None:
            filter["_id"] = ObjectId(id)
        schema = self.Meta.schema()
        pymongo_cursor = self.get_collection(schema).find(filter).limit(2)
        if pymongo_cursor.count() > 1:
            raise self.MultipleObjectsReturned()
        if pymongo_cursor.count() == 0:
            raise self.DoesNotExist()
        return self.to_object(
            schema, self._dereference(schema, pymongo_cursor[0])
        )

    # def find(self, **filter):
    #     return Cursor(schema=schema, pymongo_cursor=pymongo_cursor)

    def save(self, obj):
        self._save_recursive(schema=self.Meta.schema(), obj=obj)

    def delete(self, obj):
        pass

    def delete_many(self, **filter):
        self.get_collection(self.Meta.schema).delete_many(filter)
