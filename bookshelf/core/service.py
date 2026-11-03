from dataclasses import replace
from datetime import date, datetime

from bookshelf.core.models import Book, BookFilters, BookStatus, CollectionSummary
from bookshelf.core.repository import BookRepository


class BookValidationError(ValueError):
    def __init__(self, errors: dict[str, str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors.values()))


class BookService:
    def __init__(self, repository: BookRepository) -> None:
        self._repository = repository

    def add_book(self, book: Book) -> Book:
        return self._repository.create(self._validated(book))

    def get_book(self, book_id: int) -> Book | None:
        return self._repository.get(book_id)

    def list_books(self, filters: BookFilters = BookFilters()) -> list[Book]:
        return self._repository.list_books(filters)

    def update_book(self, book_id: int, book: Book) -> Book | None:
        return self._repository.update(book_id, self._validated(book))

    def delete_book(self, book_id: int) -> bool:
        return self._repository.delete(book_id)

    def collection_summary(self) -> CollectionSummary:
        return self._repository.summary()

    @staticmethod
    def _validated(book: Book) -> Book:
        errors: dict[str, str] = {}
        title = book.title.strip()
        author = book.author.strip()
        if not title:
            errors["title"] = "Title is required."
        if not author:
            errors["author"] = "Author is required."

        current_year = datetime.now().year
        if book.publication_year is not None and (
            not isinstance(book.publication_year, int)
            or isinstance(book.publication_year, bool)
            or not 1 <= book.publication_year <= current_year + 1
        ):
            errors["publication_year"] = "Publication year must be a plausible year."
        if book.page_count is not None and (
            not isinstance(book.page_count, int)
            or isinstance(book.page_count, bool)
            or book.page_count < 1
        ):
            errors["page_count"] = "Page count must be a positive integer."
        if book.rating is not None and (
            not isinstance(book.rating, int)
            or isinstance(book.rating, bool)
            or not 1 <= book.rating <= 5
        ):
            errors["rating"] = "Rating must be between 1 and 5."

        date_finished = _optional_text(book.date_finished)
        try:
            status = BookStatus(book.status)
        except ValueError:
            errors["status"] = "Choose a valid reading status."
            status = BookStatus.TO_READ

        if date_finished is not None:
            try:
                date.fromisoformat(date_finished)
            except ValueError:
                errors["date_finished"] = "Date finished must use ISO 8601 format."

        if errors:
            raise BookValidationError(errors)

        return replace(
            book,
            title=title,
            author=author,
            status=status,
            isbn=_optional_text(book.isbn),
            publisher=_optional_text(book.publisher),
            genre=_optional_text(book.genre),
            language=_optional_text(book.language),
            description=_optional_text(book.description),
            date_finished=date_finished,
            notes=_optional_text(book.notes),
        )


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None
