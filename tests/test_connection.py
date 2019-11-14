import pytest

from sticky_marshmallow import connection, get_db, register_db


class TestConnection:
    def setup(self):
        connection._dbs = {}

    def test_register_and_get_default_db(self):
        register_db("foo")
        assert get_db() == "foo"

    def test_register_and_get_db_with_alias(self):
        register_db("foo", alias="bar")
        assert get_db("bar") == "foo"

    def test_get_db_with_alias_does_not_exist(self):
        register_db("foo")
        with pytest.raises(KeyError):
            get_db("bar")

    def test_get_db_without_alias_does_not_exist(self):
        register_db("foo", alias="bar")
        with pytest.raises(KeyError):
            get_db()
