import sqlite3
import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QMessageBox

from bookshelf.gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("MyBookShelf")
    app.setOrganizationName("MyBookShelf")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyle("Fusion")

    try:
        window = MainWindow()
    except (OSError, RuntimeError, sqlite3.Error) as error:
        QMessageBox.critical(
            None,
            "MyBookShelf could not start",
            f"The library database could not be opened.\n\n{error}",
        )
        return 1

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
