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


def _clean():
    # pass
    BookRepository().delete_many()
    AuthorRepository().delete_many()
    ReviewRepository().delete_many()


connect()


class TestBookRepository:
    def setup(self):
        _clean()

    def teardown(self):
        _clean()

    def test_save_and_get(self):
        book = Book(
            id=None,
            title="Nineteen Eighty-Four",
            author=Author(id=None, name="George Orwell"),
        )
        repo = BookRepository()
        repo.save(book)
        book = repo.get(book.id)
        assert isinstance(book, Book)
        assert isinstance(book.author, Author)
        # assert all([isinstance(review, Review) for review in book.reviews])

    def test_delete(self):
        book = Book(
            id=None,
            title="Nineteen Eighty-Four",
            author=Author(id=None, name="George Orwell"),
        )
        repo = BookRepository()
        repo.save(book)
        repo.delete(book)
        with pytest.raises(repo.DoesNotExist):
            repo.get(book.id)

    def test_empty_reference(self):
        book = Book(id=None, title="Nineteen Eighty-Four", author=None)
        repo = BookRepository()
        repo.save(book)
        assert repo.get(book.id).author is None


class TestCursor:
    def setup(self):
        _clean()
        books = [
            Book(id=None, title="Nineteen Eighty-Four", author=None),
            Book(id=None, title="The Great Gatsby", author=None),
        ]
        repo = BookRepository()
        for book in books:
            repo.save(book)

    def teardown(self):
        _clean()

    def test_find_returns_cursor(self):
        cursor = BookRepository().find()
        assert isinstance(cursor, Cursor)
        assert next(cursor).title == "Nineteen Eighty-Four"
        assert next(cursor).title == "The Great Gatsby"
        with pytest.raises(StopIteration):
            next(cursor)

    def test_count(self):
        assert BookRepository().find().count() == 2

    def test_magic_methods(self):
        cursor = BookRepository().find().sort("-title")
        assert next(cursor).title == "The Great Gatsby"
        assert next(cursor).title == "Nineteen Eighty-Four"
