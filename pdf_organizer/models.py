from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4


@dataclass
class PageRef:
    source: Path
    index: int
    rotation: int = 0


@dataclass
class WorkingPdf:
    name: str
    pages: list[PageRef]
    source_dir: Path
    id: str = field(default_factory=lambda: uuid4().hex)

    def clone(self, *, name: str | None = None) -> "WorkingPdf":
        return WorkingPdf(
            name or self.name,
            [PageRef(p.source, p.index, p.rotation) for p in self.pages],
            self.source_dir,
        )

