import pytest

from bookshelf.core import (
    Book,
    BookFilters,
    BookRepository,
    BookService,
    BookStatus,
    Database,
    SortField,
)
from bookshelf.core.service import BookValidationError


@pytest.fixture
def library():
    with Database(":memory:") as database:
        yield BookService(BookRepository(database.connection))


def test_add_book_normalizes_data_and_sets_database_fields(library):
    book = library.add_book(
        Book(
            title="  The Left Hand of Darkness  ",
            author=" Ursula K. Le Guin ",
            isbn="  9780441478125 ",
            genre=" Science Fiction ",
        )
    )

    assert book.id is not None
    assert book.title == "The Left Hand of Darkness"
    assert book.author == "Ursula K. Le Guin"
    assert book.isbn == "9780441478125"
    assert book.genre == "Science Fiction"
    assert book.status is BookStatus.TO_READ
    assert book.date_added is not None


def test_optional_date_can_be_blank(library):
    book = library.add_book(Book(title="Title", author="Author", date_finished="  "))

    assert book.date_finished is None


@pytest.mark.parametrize(
    ("book", "field"),
    [
        (Book(title=" ", author="Author"), "title"),
        (Book(title="Title", author="\t"), "author"),
        (Book(title="Title", author="Author", publication_year=0), "publication_year"),
        (Book(title="Title", author="Author", page_count=0), "page_count"),
        (Book(title="Title", author="Author", rating=6), "rating"),
        (
            Book(title="Title", author="Author", date_finished="not-a-date"),
            "date_finished",
        ),
    ],
)
def test_add_book_rejects_invalid_data(library, book, field):
    with pytest.raises(BookValidationError) as error:
        library.add_book(book)

    assert field in error.value.errors
    assert library.collection_summary().total == 0


def test_search_filters_sorting_and_summary(library):
    library.add_book(
        Book(
            title="The Hobbit",
            author="J. R. R. Tolkien",
            genre="Fantasy",
            rating=5,
            publication_year=1937,
            status=BookStatus.COMPLETED,
        )
    )
    library.add_book(
        Book(
            title="The Silmarillion",
            author="J. R. R. Tolkien",
            genre="Fantasy",
            rating=4,
            publication_year=1977,
            status=BookStatus.READING,
        )
    )
    library.add_book(
        Book(title="A Brief History of Time", author="Stephen Hawking", genre="Science")
    )

    results = library.list_books(
        BookFilters(
            search="tolkien",
            genre="fantasy",
            sort_by=SortField.PUBLICATION_YEAR,
            descending=True,
        )
    )
    assert [book.title for book in results] == ["The Silmarillion", "The Hobbit"]
    assert library.collection_summary().total == 3
    assert library.collection_summary().reading == 1
    assert library.collection_summary().completed == 1


def test_search_treats_wildcards_as_literal_text(library):
    library.add_book(Book(title="100% Ready", author="Writer"))
    library.add_book(Book(title="1000 Ready", author="Writer"))

    results = library.list_books(BookFilters(search="%"))

    assert [book.title for book in results] == ["100% Ready"]


def test_update_and_delete_preserve_record_identity(library):
    original = library.add_book(Book(title="Old title", author="Author"))

    updated = library.update_book(
        original.id,
        Book(title="New title", author="Author", status=BookStatus.READING),
    )

    assert updated is not None
    assert updated.id == original.id
    assert updated.date_added == original.date_added
    assert updated.title == "New title"
    assert library.delete_book(original.id)
    assert library.get_book(original.id) is None
    assert not library.delete_book(original.id)


def test_database_persists_books_between_connections(tmp_path):
    database_path = tmp_path / "bookshelf.db"
    with Database(database_path) as database:
        created = BookService(BookRepository(database.connection)).add_book(
            Book(title="Persistent book", author="Author")
        )
    assert created.id is not None

    with Database(database_path) as database:
        loaded = BookService(BookRepository(database.connection)).get_book(created.id)

    assert loaded == created
