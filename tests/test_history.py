from pathlib import Path

from pdf_organizer.history import History
from pdf_organizer.models import PageRef, WorkingPdf


def test_history_is_deep_copy() -> None:
    docs = [WorkingPdf("a.pdf", [PageRef(Path("a.pdf"), 0)], Path("."))]
    history = History(); history.push(docs); docs[0].pages[0].rotation = 90
    restored = history.undo()
    assert restored is not None and restored[0].pages[0].rotation == 0

