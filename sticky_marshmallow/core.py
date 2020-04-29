import inspect

import marshmallow
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
        for field_name, field in self._get_reference_fields(
            schema, document=document
        ).items():
            if isinstance(document[field_name], list):
                nested_documents = [
                    self._get_collection_from_schema(field.schema).find_one(
                        {"_id": ObjectId(oid)}
                    )
                    for oid in document[field_name]
                ]
                document[field_name] = [
                    self._dereference(field.schema, nested_document)
                    for nested_document in nested_documents
                ]
            else:
                nested_document = self._get_collection_from_schema(
                    field.schema
                ).find_one({"_id": ObjectId(document[field_name])})
                document[field_name] = self._dereference(
                    field.schema, nested_document
                )
        if "_id" in document:
            _id = document.pop("_id")
            document["id"] = str(_id)
        return document

    def _get_schema_from_nested_field(self, field_name, field, obj=None):
        reference_schema = field.schema
        if obj is not None and hasattr(field.schema, "get_obj_type"):
            nested_objs = getattr(obj, field_name)
            if nested_objs:
                if field.schema.many is True:
                    nested_obj = nested_objs[0]
                else:
                    nested_obj = nested_objs
                reference_schema = field.schema.type_schemas[
                    field.schema.get_obj_type(nested_obj)
                ]
        return reference_schema

    def _get_reference_fields(self, schema, obj=None, document=None):
        reference_fields = {}
        for field_name, field, in schema._declared_fields.items():
            if isinstance(field, fields.Nested):
                reference_schema = self._get_schema_from_nested_field(
                    field_name, field, obj
                )
                if "id" in reference_schema._declared_fields:
                    reference_fields[field_name] = field
                elif document:
                    nested_objs = document[field_name]
                    nested_obj = (
                        nested_objs[0]
                        if reference_schema.many is True
                        else nested_objs
                    )
                    if isinstance(nested_obj, ObjectId):
                        """
                        When we encounter an ObjectId in a nested document, we
                        are assuming we are dealing with a dereferenced field.
                        """
                        reference_fields[field_name] = field
        return reference_fields

    def _to_object(self, schema, document):
        try:
            return schema.load(self._dereference(schema, document))
        except marshmallow.exceptions.ValidationError as exc:
            """
            An ugly hack to support marshmallow_oneofschema.

            When provided with a master schema, we don't have the
            _declared_fields of the subschemas. Here we delete the 'id' value
            from the document and try again.
            """
            if exc.messages == {"id": ["Unknown field."]} and "id" in document:
                document.pop("id")
                return schema.load(self._dereference(schema, document))
            raise exc
