from __future__ import annotations

from .models import WorkingPdf


class History:
    def __init__(self, limit: int = 20) -> None:
        self.limit = limit
        self._states: list[list[WorkingPdf]] = []

    def push(self, documents: list[WorkingPdf]) -> None:
        self._states.append([d.clone(name=d.name) for d in documents])
        self._states = self._states[-self.limit:]

    def undo(self) -> list[WorkingPdf] | None:
        return self._states.pop() if self._states else None
