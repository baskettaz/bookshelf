from dataclasses import dataclass
from enum import StrEnum


class BookStatus(StrEnum):
    TO_READ = "To Read"
    READING = "Reading"
    COMPLETED = "Completed"
    ON_HOLD = "On Hold"
    ABANDONED = "Abandoned"


class SortField(StrEnum):
    TITLE = "title"
    AUTHOR = "author"
    PUBLICATION_YEAR = "publication_year"
    RATING = "rating"
    DATE_ADDED = "date_added"


@dataclass(frozen=True, slots=True)
class Book:
    title: str
    author: str
    isbn: str | None = None
    publisher: str | None = None
    publication_year: int | None = None
    genre: str | None = None
    language: str | None = None
    description: str | None = None
    page_count: int | None = None
    rating: int | None = None
    status: BookStatus = BookStatus.TO_READ
    date_finished: str | None = None
    notes: str | None = None
    id: int | None = None
    date_added: str | None = None


@dataclass(frozen=True, slots=True)
class BookFilters:
    search: str = ""
    genre: str | None = None
    status: BookStatus | None = None
    rating: int | None = None
    publication_year: int | None = None
    sort_by: SortField = SortField.TITLE
    descending: bool = False


@dataclass(frozen=True, slots=True)
class CollectionSummary:
    total: int
    reading: int
    completed: int
