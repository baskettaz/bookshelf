from pathlib import Path

from PyQt6 import uic
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
)

from bookshelf.core.models import Book, BookStatus

_UI_DIRECTORY = Path(__file__).parent


class BookDialog(QDialog):
    saveRequested = pyqtSignal(object)
    authorInput: QLineEdit
    cancelButton: QPushButton
    dateFinishedInput: QLineEdit
    descriptionInput: QTextEdit
    dialogSubtitle: QLabel
    dialogTitle: QLabel
    formError: QLabel
    genreInput: QLineEdit
    isbnInput: QLineEdit
    languageInput: QLineEdit
    notesInput: QTextEdit
    pageCountInput: QLineEdit
    publisherInput: QLineEdit
    ratingInput: QComboBox
    saveButton: QPushButton
    statusInput: QComboBox
    titleInput: QLineEdit
    yearInput: QLineEdit

    def __init__(self, book: Book | None = None, parent=None) -> None:
        super().__init__(parent)
        uic.loadUi(str(_UI_DIRECTORY / "book_dialog.ui"), self)
        self._book = book
        self.setWindowTitle("Edit book" if book is not None else "Add a book")
        self.dialogTitle.setText("Edit book" if book is not None else "Add a book")
        self.dialogSubtitle.setText(
            "Update the details on your shelf."
            if book is not None
            else "A few details now make it easy to find again later."
        )
        self.saveButton.setText("Save changes" if book is not None else "Save book")

        self.ratingInput.addItem("Not rated", None)
        for rating in range(1, 6):
            self.ratingInput.addItem(f"{rating} / 5", rating)
        for status in BookStatus:
            self.statusInput.addItem(status.value, status.value)

        self._populate(book)
        self.saveButton.clicked.connect(self._submit)
        self.cancelButton.clicked.connect(self.reject)

    def set_error(self, message: str) -> None:
        self.formError.setText(message)
        self.formError.setVisible(bool(message))

    def book_from_form(self) -> Book:
        year = _optional_integer(self.yearInput.text(), "Publication year")
        page_count = _optional_integer(self.pageCountInput.text(), "Page count")

        return Book(
            id=self._book.id if self._book is not None else None,
            date_added=self._book.date_added if self._book is not None else None,
            title=self.titleInput.text(),
            author=self.authorInput.text(),
            isbn=self.isbnInput.text(),
            publisher=self.publisherInput.text(),
            publication_year=year,
            genre=self.genreInput.text(),
            language=self.languageInput.text(),
            description=self.descriptionInput.toPlainText(),
            page_count=page_count,
            rating=self.ratingInput.currentData(),
            status=BookStatus(self.statusInput.currentData()),
            date_finished=self.dateFinishedInput.text(),
            notes=self.notesInput.toPlainText(),
        )

    def _submit(self) -> None:
        try:
            book = self.book_from_form()
        except ValueError as error:
            self.set_error(str(error))
            return
        self.set_error("")
        self.saveRequested.emit(book)

    def _populate(self, book: Book | None) -> None:
        if book is None:
            return

        self.titleInput.setText(book.title)
        self.authorInput.setText(book.author)
        self.isbnInput.setText(book.isbn or "")
        self.publisherInput.setText(book.publisher or "")
        self.yearInput.setText(
            str(book.publication_year) if book.publication_year is not None else ""
        )
        self.genreInput.setText(book.genre or "")
        self.languageInput.setText(book.language or "")
        self.pageCountInput.setText(
            str(book.page_count) if book.page_count is not None else ""
        )
        self.descriptionInput.setPlainText(book.description or "")
        self.dateFinishedInput.setText(book.date_finished or "")
        self.notesInput.setPlainText(book.notes or "")
        self.ratingInput.setCurrentIndex(self.ratingInput.findData(book.rating))
        self.statusInput.setCurrentIndex(self.statusInput.findData(book.status.value))
        self.titleInput.setFocus(Qt.FocusReason.OtherFocusReason)


class BookDetailsDialog(QDialog):
    changeStatusButton: QPushButton
    detailsAuthor: QLabel
    detailsCloseButton: QPushButton
    detailsDescription: QLabel
    detailsEditButton: QPushButton
    detailsMetadata: QLabel
    detailsNotes: QLabel
    detailsRating: QLabel
    detailsStatus: QLabel
    detailsTitle: QLabel
    statusInput: QComboBox
    statusChangeRequested = pyqtSignal(str)

    def __init__(self, book: Book, parent=None) -> None:
        super().__init__(parent)
        uic.loadUi(str(_UI_DIRECTORY / "book_details.ui"), self)
        self.book = book
        self.edit_requested = False
        self.setWindowTitle(book.title)

        for widget in (
            self.detailsTitle,
            self.detailsAuthor,
            self.detailsStatus,
            self.detailsRating,
            self.detailsMetadata,
            self.detailsDescription,
            self.detailsNotes,
        ):
            widget.setTextFormat(Qt.TextFormat.PlainText)

        for status in BookStatus:
            self.statusInput.addItem(status.value, status.value)
        self.set_book(book)
        self.detailsEditButton.clicked.connect(self._edit)
        self.detailsCloseButton.clicked.connect(self.reject)
        self.changeStatusButton.clicked.connect(self._request_status_change)

    def set_book(self, book: Book) -> None:
        self.book = book
        self.detailsTitle.setText(book.title)
        self.detailsAuthor.setText(f"by {book.author}")
        self.detailsStatus.setText(book.status.value)
        self.statusInput.setCurrentIndex(self.statusInput.findData(book.status.value))
        self.detailsRating.setText(
            f"{book.rating} / 5" if book.rating is not None else "Not rated"
        )
        self.detailsMetadata.setText(
            "  |  ".join(
                value
                for value in (
                    book.genre,
                    str(book.publication_year) if book.publication_year else None,
                    book.publisher,
                    f"ISBN {book.isbn}" if book.isbn else None,
                    f"{book.page_count} pages" if book.page_count else None,
                    book.language,
                    f"Finished {book.date_finished}" if book.date_finished else None,
                    f"Added {book.date_added}" if book.date_added else None,
                )
                if value
            )
            or "No additional publication details."
        )
        self.detailsDescription.setText(book.description or "No description added.")
        self.detailsNotes.setText(book.notes or "No personal notes.")

    def _edit(self) -> None:
        self.edit_requested = True
        self.accept()

    def _request_status_change(self) -> None:
        self.statusChangeRequested.emit(self.statusInput.currentData())


def _optional_integer(value: str, field_name: str) -> int | None:
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"{field_name} must be a whole number.") from error
