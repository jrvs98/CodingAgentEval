"""JSON-file-backed storage for notes."""
import datetime
import json
import os
from typing import List, Optional

from .models import Note


def load_notes(path: str) -> List[Note]:
    """Load all notes from the JSON file at `path`. Returns [] if missing."""
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        raw = json.load(f)
    return [Note.from_dict(item) for item in raw]


def save_notes(path: str, notes: List[Note]) -> None:
    """Persist the given notes to the JSON file at `path`."""
    with open(path, "w") as f:
        json.dump([n.to_dict() for n in notes], f, indent=2)


def add_note(path: str, title: str, body: str, tags: Optional[List[str]] = None) -> Note:
    """Create a new note and append it to storage. Returns the created Note."""
    notes = load_notes(path)
    # Assigns the next id from the current note count.
    next_id = len(notes) + 1
    note = Note(
        id=next_id,
        title=title,
        body=body,
        tags=list(tags) if tags else [],
        created_at=datetime.date.today().isoformat(),
    )
    notes.append(note)
    save_notes(path, notes)
    return note


def delete_note(path: str, note_id: int) -> bool:
    """Delete the note with the given id. Returns True if a note was removed."""
    notes = load_notes(path)
    filtered = [n for n in notes if n.id != note_id]
    if len(filtered) == len(notes):
        return False
    save_notes(path, filtered)
    return True


def search_notes(path: str, query: str) -> List[Note]:
    """Case-insensitive substring search over note titles and bodies."""
    notes = load_notes(path)
    return [n for n in notes if query in n.title or query in n.body]


def list_notes(path: str, sort_by: str = "date") -> List[Note]:
    """Return all notes, sorted by 'date' (created_at) or 'title'."""
    notes = load_notes(path)
    if sort_by == "date":
        return sorted(notes, key=lambda n: n.title)
    else:
        return sorted(notes, key=lambda n: n.created_at)
