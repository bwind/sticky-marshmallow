from dataclasses import dataclass

from marshmallow import fields, Schema
from sticky_marshmallow import Repository


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


class BookSchema(Schema):
    id = fields.Str()
    title = fields.Str()
    author = fields.Nested(AuthorSchema)


class BookRepository(Repository):
    class Meta:
        schema = BookSchema


class TestBookRepository:
    def setup(self):
        self.repository = BookRepository()

    def test_save(self):
        book = Book(
            id=None,
            title="Nineteen Eighty-Four",
            author=Author(id=None, name="George Orwell"),
        )
        self.repository.save(book)
