"""Command-line interface for notes-cli."""
import argparse
import sys

from . import storage

DEFAULT_STORE = "notes.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="notes")
    parser.add_argument("--file", default=DEFAULT_STORE, help="path to the notes JSON store")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add a note")
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--body", required=True)
    p_add.add_argument("--tags", default="", help="comma-separated tags")

    p_list = sub.add_parser("list", help="list notes")
    p_list.add_argument("--sort", choices=["date", "title"], default="date")
    p_list.add_argument("--tag")
    p_list.add_argument("--all", action="store_true", dest="include_archived")

    p_delete = sub.add_parser("delete", help="delete a note by id")
    p_delete.add_argument("id", type=int)

    for name in ("archive", "unarchive"):
        p_archive = sub.add_parser(name, help=f"{name} a note by id")
        p_archive.add_argument("id", type=int)

    p_export = sub.add_parser("export", help="export notes to CSV")
    p_export.add_argument("output_path")

    p_search = sub.add_parser("search", help="search notes by title/body")
    p_search.add_argument("query")

    return parser


def _print_note(note) -> None:
    tags = ",".join(note.tags) if note.tags else "-"
    print(f"[{note.id}] {note.title} (tags: {tags}, created: {note.created_at})")


def run(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "add":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        note = storage.add_note(args.file, args.title, args.body, tags)
        print(f"Added note {note.id}")
        return 0

    if args.command == "list":
        notes = storage.list_notes(
            args.file,
            sort_by=args.sort,
            tag=args.tag,
            include_archived=args.include_archived,
        )
        for note in notes:
            _print_note(note)
        return 0

    if args.command == "delete":
        removed = storage.delete_note(args.file, args.id)
        print("Deleted" if removed else "Not found")
        return 0 if removed else 1

    if args.command == "search":
        notes = storage.search_notes(args.file, args.query)
        for note in notes:
            _print_note(note)
        return 0

    if args.command in ("archive", "unarchive"):
        operation = storage.archive_note if args.command == "archive" else storage.unarchive_note
        changed = operation(args.file, args.id)
        print("Archived" if args.command == "archive" and changed else
              "Unarchived" if args.command == "unarchive" and changed else "Not found")
        return 0 if changed else 1

    if args.command == "export":
        storage.export_notes(args.file, args.output_path)
        return 0

    parser.print_help()
    return 1


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
