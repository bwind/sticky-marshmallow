import inspect

from bson import ObjectId
from marshmallow import fields

from sticky_marshmallow.connection import get_db
from sticky_marshmallow.utils.case import snake_case


class Core:
    @staticmethod
    def get_db():
        return get_db()

    @staticmethod
    def _get_collection_name_from_schema(schema):
        # Allows both the schema class and an instance to be passed
        if inspect.isclass(schema):
            cls_name = schema.__name__
        else:
            cls_name = schema.__class__.__name__
        collection_name = snake_case(cls_name.replace("Schema", ""))
        return collection_name

    def _get_collection_from_schema(self, schema):
        return self.get_db()[self._get_collection_name_from_schema(schema)]

    def _dereference(self, schema, document):
        if document is None:
            return
        for field_name, field in self._get_reference_fields(schema).items():
            nested_document = self._get_collection_from_schema(field.schema).\
                find_one({"_id": ObjectId(document[field_name])}
            )
            document[field_name] = self._dereference(field.schema,
                                                     nested_document)
        document["id"] = str(document.pop("_id"))
        return document

    @staticmethod
    def _get_reference_fields(schema):
        return {
            field_name: field
            for field_name, field, in schema._declared_fields.items()
            if isinstance(field, fields.Nested)
            and "id" in field.schema._declared_fields
        }

    def _to_object(self, schema, document):
        return schema.load(self._dereference(schema, document))
