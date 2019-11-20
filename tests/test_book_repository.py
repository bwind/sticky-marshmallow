from dataclasses import dataclass

from marshmallow import fields, post_load, Schema
from sticky_marshmallow import Repository

from tests.db import connect


@dataclass
class Author:
    id: str
    name: str


@dataclass
class Book:
    id: str
    title: str
    author: Author


class AuthorSchema(Schema):
    id = fields.Str()
    name = fields.Str()

    @post_load
    def make_object(self, data, **kwargs):
        return Author(**data)


class BookSchema(Schema):
    id = fields.Str()
    title = fields.Str()
    author = fields.Nested(AuthorSchema, allow_none=True)

    @post_load
    def make_object(self, data, **kwargs):
        return Book(**data)


class BookRepository(Repository):
    class Meta:
        schema = BookSchema
        collection = "my_books"


class AuthorRepository(Repository):
    class Meta:
        schema = AuthorSchema


class TestBookRepository:
    def setup(self):
        connect()
        self.repository = BookRepository()
        self.repository.delete_many()
        AuthorRepository().delete_many()

    def test_save_and_get(self):
        book = Book(
            id=None,
            title="Nineteen Eighty-Four",
            author=Author(id=None, name="George Orwell"),
        )
        self.repository.save(book)
        book = self.repository.get(book.id)
        assert isinstance(book, Book)
        assert isinstance(book.author, Author)

    def test_empty_reference(self):
        book = Book(id=None, title="Nineteen Eighty-Four", author=None)
        self.repository.save(book)
        assert self.repository.get(book.id).author is None
