"""Data model for a single note."""
from dataclasses import dataclass, field, asdict
from typing import List


@dataclass
class Note:
    id: int
    title: str
    body: str
    tags: List[str] = field(default_factory=list)
    created_at: str = ""  # ISO date string, e.g. "2026-07-23"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Note":
        return cls(
            id=data["id"],
            title=data["title"],
            body=data["body"],
            tags=data.get("tags", []),
            created_at=data.get("created_at", ""),
        )
