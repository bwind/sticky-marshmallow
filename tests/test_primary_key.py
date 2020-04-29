from dataclasses import dataclass

from sticky_marshmallow import Repository
from marshmallow import fields, Schema

from tests.db import connect


@dataclass
class Foo:
    bar: str
    baz: str
    qux: str


class FooSchema(Schema):
    bar = fields.Str()
    baz = fields.Str()
    qux = fields.Str()


class FooRepository(Repository):
    class Meta:
        schema = FooSchema
        primary_key = ["bar", "baz"]


@dataclass
class Bar:
    id: str


class BarSchema(Schema):
    id = fields.Str()


class BarRepository(Repository):
    class Meta:
        schema = BarSchema


class TestPrimaryKey:
    def setup(self):
        connect()
        FooRepository().delete_many()
        BarRepository().delete_many()

    def teardown(self):
        FooRepository().delete_many()
        BarRepository().delete_many()

    def test_replaces_id(self):
        bar = Bar(id=None)
        BarRepository().save(bar)
        assert "id" not in BarRepository().collection.find_one().keys()

    def test_overwrites_object(self):
        foo = Foo(bar="1", baz="2", qux="3")
        FooRepository().save(foo)
        assert FooRepository().find().count() == 1
        foo.qux = "4"
        FooRepository().save(foo)
        assert FooRepository().find().count() == 1

    def test_saves_new_object(self):
        foo = Foo(bar="1", baz="2", qux="3")
        FooRepository().save(foo)
        assert FooRepository().find().count() == 1
        foo.bar = "4"
        FooRepository().save(foo)
        assert FooRepository().find().count() == 2
