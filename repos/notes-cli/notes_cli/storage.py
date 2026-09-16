"""JSON-file-backed storage for notes."""
import datetime
import csv
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
    # Accept the original list format as well as the metadata-bearing format.
    if isinstance(raw, dict):
        raw = raw.get("notes", [])
    return [Note.from_dict(item) for item in raw]


def save_notes(path: str, notes: List[Note]) -> None:
    """Persist the given notes to the JSON file at `path`."""
    with open(path, "w") as f:
        json.dump([n.to_dict() for n in notes], f, indent=2)


def add_note(path: str, title: str, body: str, tags: Optional[List[str]] = None) -> Note:
    """Create a new note and append it to storage. Returns the created Note."""
    notes = load_notes(path)
    # Keep IDs monotonic even when the note with the greatest ID was deleted.
    next_id = _next_id(path, notes)
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


def _next_id(path: str, notes: List[Note]) -> int:
    """Return a new ID, retaining the counter separately from note contents."""
    counter_path = path + ".next-id"
    try:
        with open(counter_path, "r") as f:
            next_id = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        next_id = max((n.id for n in notes), default=0) + 1
    with open(counter_path, "w") as f:
        f.write(str(next_id + 1))
    return next_id


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
    query = query.casefold()
    return [n for n in notes if query in n.title.casefold() or query in n.body.casefold()]


def list_notes(
    path: str,
    sort_by: str = "date",
    tag: Optional[str] = None,
    include_archived: bool = False,
) -> List[Note]:
    """Return all notes, sorted by 'date' (created_at) or 'title'."""
    notes = load_notes(path)
    if not include_archived:
        notes = [n for n in notes if not n.archived]
    if tag is not None:
        notes = [n for n in notes if tag in n.tags]
    if sort_by == "date":
        return sorted(notes, key=lambda n: n.created_at)
    else:
        return sorted(notes, key=lambda n: n.title)


def _set_archived(path: str, note_id: int, archived: bool) -> bool:
    notes = load_notes(path)
    for note in notes:
        if note.id == note_id:
            note.archived = archived
            save_notes(path, notes)
            return True
    return False


def archive_note(path: str, note_id: int) -> bool:
    """Archive a note without removing it from storage."""
    return _set_archived(path, note_id, True)


def unarchive_note(path: str, note_id: int) -> bool:
    """Restore an archived note."""
    return _set_archived(path, note_id, False)


def export_notes(path: str, output_path: str) -> None:
    """Write all stored notes, including archived notes, to a CSV file."""
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "body", "tags", "created_at"])
        for note in load_notes(path):
            writer.writerow([note.id, note.title, note.body, ";".join(note.tags), note.created_at])


# Descriptive alias for callers that prefer an explicit CSV name.
export_notes_csv = export_notes
