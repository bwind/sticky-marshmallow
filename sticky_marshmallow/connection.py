import pymongo


__all__ = [
    "connect",
    "get_db",
    "register_db",
]

_connections = {}
_dbs = {}

DEFAULT_ALIAS = "default"


def connect(db="test", host=None):
    connection = pymongo.MongoClient(host=host)
    register_connection(connection)
    register_db(connection[db])


def get_db(alias=DEFAULT_ALIAS):
    return _dbs[alias]


def register_connection(connection, alias=DEFAULT_ALIAS):
    _connections[alias] = connection


def register_db(db, alias=DEFAULT_ALIAS):
    _dbs[alias] = db
