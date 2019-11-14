import pymongo


__all__ = [
    "connect",
    "register_db",
]

_connections = {}
_dbs = {}


def connect(db="test", host=None):
    connection = pymongo.MongoClient(host=host)
    register_connection(connection)
    register_db(connection[db])


def get_db(alias="test"):
    return _dbs[alias]


def register_connection(connection):
    _connections["default"] = connection


def register_db(db):
    _dbs[db.name] = db
