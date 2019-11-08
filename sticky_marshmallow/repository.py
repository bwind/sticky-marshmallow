from bson import ObjectId

from marshmallow import fields
from sticky_marshmallow.utils.case import snake_case


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
    def _get_collection_name(self):
        return snake_case(self.__class__.__name__.replace("Repository", ""))

    def _get_recursive(self, collection_name, filter):
        document = self.db[collection_name].find_one(filter)
        refs = {
            key: value
            for key, value in document.items()
            if isinstance(key, ObjectId)
        }
        for key, value in refs.items():
            setattr(document, key, self._get_recursive(key, {"_id": value}))

    def _save_recursive(self, schema, obj):
        document = schema.dump(obj)
        for field_name, field in schema._declared_fields.items():
            if isinstance(field, fields.Nested):
                if "id" in field.schema._declared_fields:
                    document[field_name] = self._save_recursive(
                        field.schema, getattr(obj, field_name)
                    )["_id"]
        document["_id"] = ObjectId(document.pop("id"))
        # todo: save this document
        return document

    def to_mongo(self, obj):
        pass

    def to_object(self, document):
        pass

    def get(self, **filter):
        if "id" in filter:
            filter["_id"] = filter.pop("id")

    def find(self, **filter):
        pass

    def save(self, obj):
        self._save_recursive(schema=self.Meta.schema(), obj=obj)

    def delete(self, obj):
        pass

    def delete_many(self, **filter):
        pass
