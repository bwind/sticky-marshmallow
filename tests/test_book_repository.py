from dataclasses import dataclass

import pytest
from marshmallow import fields, post_load, Schema
from sticky_marshmallow import Repository
from sticky_marshmallow.cursor import Cursor

from tests.db import connect


@dataclass
class Author:
    id: str
    name: str


@dataclass
class Review:
    id: str
    text: str


@dataclass
class Book:
    id: str
    title: str
    author: Author
    # reviews: List[Review]


class AuthorSchema(Schema):
    id = fields.Str()
    name = fields.Str()

    @post_load
    def make_object(self, data, **kwargs):
        return Author(**data)


class ReviewSchema(Schema):
    id = fields.Str()
    text = fields.Str()


class BookSchema(Schema):
    id = fields.Str()
    title = fields.Str()
    author = fields.Nested(AuthorSchema, allow_none=True)
    # reviews = fields.Nested(ReviewSchema, allow_none=True, many=True)

    @post_load
    def make_object(self, data, **kwargs):
        return Book(**data)


class BookRepository(Repository):
    class Meta:
        schema = BookSchema
        collection = "my_books"  # not implemented yet.


class AuthorRepository(Repository):
    class Meta:
        schema = AuthorSchema


class ReviewRepository(Repository):
    class Meta:
        schema = ReviewSchema


class TestBookRepository:
    def setup(self):
        connect()
        self.repository = BookRepository()
        self.repository.delete_many()
        AuthorRepository().delete_many()
        ReviewRepository().delete_many()

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
        # assert all([isinstance(review, Review) for review in book.reviews])

    def test_delete(self):
        book = Book(
            id=None,
            title="Nineteen Eighty-Four",
            author=Author(id=None, name="George Orwell"),
        )
        self.repository.save(book)
        self.repository.delete(book)
        with pytest.raises(self.repository.DoesNotExist):
            self.repository.get(book.id)

    def test_empty_reference(self):
        book = Book(id=None, title="Nineteen Eighty-Four", author=None)
        self.repository.save(book)
        assert self.repository.get(book.id).author is None

    def test_find_returns_cursor(self):
        books = [
            Book(id=None, title="Nineteen Eighty-Four", author=None),
            Book(id=None, title="The Great Gatsby", author=None),
        ]
        for book in books:
            self.repository.save(book)
        cursor = self.repository.find()
        assert isinstance(cursor, Cursor)
        assert next(cursor).title == "Nineteen Eighty-Four"
        assert next(cursor).title == "The Great Gatsby"
        with pytest.raises(StopIteration):
            next(cursor)
