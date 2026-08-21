import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QListView

from pdf_organizer.main_window import MainWindow


@pytest.fixture(scope="module")
def application() -> QApplication:
    app = QApplication.instance() or QApplication([])
    yield app


def test_main_window_starts_without_error(application: QApplication) -> None:
    window = MainWindow()
    try:
        window.show()
        application.processEvents()

        assert window.isVisible()
        assert window.pages.viewMode() == QListView.ViewMode.IconMode
        assert window.pages.resizeMode() == QListView.ResizeMode.Adjust
    finally:
        window.close()
