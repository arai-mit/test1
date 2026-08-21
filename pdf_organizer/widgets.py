from __future__ import annotations

import fitz
from PySide6.QtCore import QMimeData, Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QImage, QPixmap
from PySide6.QtWidgets import QLabel, QListWidget

from .models import PageRef


class FileDropList(QListWidget):
    filesDropped = Signal(list)
    orderChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            self.filesDropped.emit([u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()])
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
            self.orderChanged.emit()


def page_pixmap(page: PageRef, width: int) -> QPixmap:
    with fitz.open(page.source) as doc:
        pdf_page = doc.load_page(page.index)
        scale = width / max(pdf_page.rect.width, 1)
        matrix = fitz.Matrix(scale, scale).prerotate(page.rotation)
        pix = pdf_page.get_pixmap(matrix=matrix, alpha=False)
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888).copy()
    return QPixmap.fromImage(image)

