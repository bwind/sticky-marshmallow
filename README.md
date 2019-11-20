# sticky-marshmallow

sticky-marshmallow is a Python library that provides mongoDB persistence for marshmallow schema based data. It dereferences nested entities and stores them in their own collections. sticky-marshmallow uses a few practices from DDD (repositories, entities, value objects).

This project follows the convention-over-configuration philosophy and makes the following assumptions:

* Root-level objects as well as nested objects (using `fields.Nested`) that need to be stored in their own collection require an `id = fields.Str()` field.
* The schema name excluding `Schema` is used as its collection name (except when explicitly provided through its Meta class).
* Schemas have a `@post_load` decorated method that returns a Python class that allows its `id` attribute to be set.

## Defining repositories

There are two ways of defining repositories to store objects. The first and easiest is to instantiate sticky-marshmallow's Repository object directly with your schema as its only argument: `Repository(BookSchema)`. The second method provides more configuration options through its Meta class and requires subclassing `Repository`:

```
from sticky_marshmallow import Repository

class BookRepository(Repository):
    class Meta:
        schema = BookSchema
        collection = 'book'
```

## Database connection

sticky-marshmallow needs to be aware of your database connection. You have two options here:

1. Use sticky-marshmallow's `connect()` pymongo wrapper to connect to a database, which automatically registers the database:

```
from sticky_marshmallow import connect

db = connect('test', host='localhost')
```
Or:

2. Use your own code to connect to a database, then register the database:

```
import pymongo
from sticky_marshmallow import register_db

db = pymongo.MongoClient(**connection_settings)['test']
register_db(db)
```

## Example


## Notes

This library is not built with performance in mind.

# TODO

* Implement Cursor that lazily loads MongoDB documents
* Implement save() with iterables
* Use `collection` from Repository.Meta
