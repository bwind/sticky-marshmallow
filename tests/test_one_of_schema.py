from dataclasses import dataclass
from typing import List

import bson
from sticky_marshmallow import Repository
from marshmallow_oneofschema import OneOfSchema
from marshmallow import fields, post_load, Schema

from tests.db import connect


@dataclass
class Foo:
    id: str
    foo: str


@dataclass
class A(Foo):
    bar: str


@dataclass
class B(Foo):
    baz: str


class BaseSchema(Schema):
    id = fields.Str(allow_none=True)
    foo = fields.Str()


class ASchema(BaseSchema):
    bar = fields.Str()

    @post_load
    def make_object(self, data, **kwargs):
        return A(**data)


class BSchema(BaseSchema):
    baz = fields.Str()


class FooSchema(OneOfSchema):
    type_schemas = {"a": ASchema, "b": BSchema}

    def get_obj_type(self, obj):
        return obj.__class__.__name__.lower()


class FooRepository(Repository):
    class Meta:
        schema = FooSchema


@dataclass
class Master:
    foos: List[Foo]


class MasterSchema(Schema):
    foos = fields.Nested(FooSchema, many=True)


class MasterRepository(Repository):
    class Meta:
        schema = MasterSchema


class TestOneOfSchema:
    def setup(self):
        connect()
        FooRepository().delete_many()
        MasterRepository().delete_many()

    def teardown(self):
        FooRepository().delete_many()
        MasterRepository().delete_many()

    def test_collection_name(self):
        assert FooRepository().collection.name == "foo"

    def test_saves_reference(self):
        a = A(id=None, foo="x", bar="y")
        master = Master(foos=[a])
        MasterRepository().save(master)
        assert isinstance(
            MasterRepository().collection.find_one()["foos"][0], bson.ObjectId
        )
        assert FooRepository().collection.find_one()
