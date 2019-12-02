import pymongo

from sticky_marshmallow.core import Core


class Cursor:
    def __init__(self, schema, collection, filter):
        self._schema = schema
        self._filter = filter
        self._collection = collection
        self._pymongo_cursor = self._collection.find(filter)
        self._method_name = None
        self._method_chain = []

    def __iter__(self):
        return self

    def __next__(self):
        document = next(self._pymongo_cursor)
        return Core()._to_object(self._schema, document)

    def __getattr__(self, name, *args, **kwargs):
        """
        Guido is not a fan of method chaining:
        https://mail.python.org/pipermail/python-dev/2003-October/038855.html
        """
        if name in ("find", "limit", "skip", "sort"):
            self._method_name = name
            return self
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def __call__(self, *args, **kwargs):
        if self._method_name is not None:

            if self._method_name == "sort":
                sort_args = []
                for idx, sort_arg in enumerate(args):
                    sort_field = sort_arg.lstrip("-")
                    sort_order = (
                        pymongo.DESCENDING
                        if sort_arg.startswith("-")
                        else pymongo.ASCENDING
                    )
                    sort_args.append((sort_field, sort_order))
                method_args = [sort_args]
            else:
                method_args = args

            self._method_chain.append((self._method_name, method_args, kwargs))
            self._pymongo_cursor = getattr(
                self._pymongo_cursor, self._method_name
            )(*method_args, **kwargs)
        return self

    def count(self):
        return self._collection.count_documents(self._filter)
