from sticky_marshmallow import connect as _connect


def connect():
    return _connect(host="db", db="test")
