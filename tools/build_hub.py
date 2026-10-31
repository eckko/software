#!/usr/bin/env python3
"""Check every book folder of this subject site and write books.json.

    python3 tools/build_hub.py           # check, then rewrite books.json
    python3 tools/build_hub.py --check   # check only; exit 1 on a problem
                                         # or when books.json is out of date

Every top-level folder is a book, except the reserved ones (tools, tests,
templates) and folders starting with a dot. A book folder may hold exactly
the four things a private book repo is allowed to publish:

    index.html            the loader that starts the quiz from the CDN
    questions.json        the book's questions
    images/favicon.png    the book's icon (used as its button on the hub)
    media/                encrypted pictures only (*.enc)

Anything else is a problem, so a reference file or a chapter map cannot
reach the public site by accident. Book ids must be unique within this
site. (Progress is saved per book id in the reader's browser and account,
and all your Pages sites share one address, so keep ids different across
your subject sites too; this tool can only check this one.)
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESERVED_FOLDERS = {"tools", "tests", "templates"}
ALLOWED_ROOT_FILES = {
    "index.html", "books.json", "subject.json", "README.md", "CLAUDE.md",
    ".gitignore", ".nojekyll", "CNAME", "LICENSE",
}
BOOK_ITEMS = {"index.html", "questions.json", "images", "media"}
FOLDER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
PINNED_LOADER = re.compile(r"@\d+(?:\.\d+){0,2}/js/boot\.js")
BOOKS_FILE = "books.json"


def load_subject(root):
    """Read subject.json.

    @param root: the subject site folder
    @return: (settings dict, list of problems)
    """
    path = root / "subject.json"
    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return {}, ["subject.json cannot be read: %s" % error]
    problems = []
    if not isinstance(settings.get("title"), str):
        problems.append("subject.json needs a text \"title\"")
    return settings, problems


def check_contents(folder):
    """Check that a book folder holds only the four allowed things.

    @param folder: path of the book folder
    @return: list of problems
    """
    problems = []
    name = folder.name
    for item in sorted(folder.iterdir()):
        if item.name not in BOOK_ITEMS:
            problems.append("%s/%s is not one of the four allowed items"
                            % (name, item.name))
    images = folder / "images"
    if images.is_dir():
        for item in sorted(images.rglob("*")):
            if item.is_file() and item.relative_to(images).as_posix() \
                    != "favicon.png":
                problems.append("%s/images/%s: only favicon.png is allowed"
                                % (name, item.relative_to(images).as_posix()))
    media = folder / "media"
    if media.is_dir():
        for item in sorted(media.rglob("*")):
            if item.is_file() and item.suffix != ".enc":
                problems.append("%s/media/%s is not an encrypted .enc file"
                                % (name, item.relative_to(media).as_posix()))
    if not (images / "favicon.png").is_file():
        problems.append("%s/images/favicon.png is missing" % name)
    return problems


def check_loader(folder):
    """Check that index.html starts the quiz from a pinned CDN tag.

    @param folder: path of the book folder
    @return: list of problems
    """
    page = folder / "index.html"
    try:
        text = page.read_text(encoding="utf-8")
    except OSError:
        return ["%s/index.html is missing" % folder.name]
    if not PINNED_LOADER.search(text):
        return ["%s/index.html does not load js/boot.js from an exact "
                "template tag (for example @2.2.1)" % folder.name]
    return []


def read_book(folder):
    """Read the id and title from a book's questions.json.

    @param folder: path of the book folder
    @return: (entry dict or None, list of problems)
    """
    try:
        data = json.loads(
            (folder / "questions.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return None, ["%s/questions.json cannot be read: %s"
                      % (folder.name, error)]
    book_id, title = data.get("id"), data.get("book")
    problems = []
    if not isinstance(book_id, str) or not ID_PATTERN.match(book_id):
        problems.append("%s/questions.json: \"id\" must be lower-case "
                        "letters, digits and dashes" % folder.name)
    if not isinstance(title, str) or not title.strip():
        problems.append("%s/questions.json: \"book\" (the title) is "
                        "missing" % folder.name)
    if problems:
        return None, problems
    return {"folder": folder.name, "id": book_id, "title": title.strip()}, []


def check_book(folder):
    """Check one book folder completely.

    @param folder: path of the book folder (its name is the URL name)
    @return: (entry dict or None, list of problems)
    """
    if not FOLDER_PATTERN.match(folder.name):
        return None, ["folder \"%s\": use lower-case letters, digits and "
                      "dashes" % folder.name]
    problems = check_contents(folder) + check_loader(folder)
    entry, more = read_book(folder) if (folder / "questions.json").is_file() \
        else (None, ["%s/questions.json is missing" % folder.name])
    problems += more
    return entry, problems


def book_folders(root):
    """@return: sorted list of the folders that count as books"""
    return sorted(
        item for item in root.iterdir()
        if item.is_dir() and not item.name.startswith(".")
        and item.name not in RESERVED_FOLDERS)


def check_site(root):
    """Check the whole site.

    @param root: the subject site folder
    @return: (list of book entries, list of problems)
    """
    settings, problems = load_subject(root)
    for item in sorted(root.iterdir()):
        if item.is_file() and item.name not in ALLOWED_ROOT_FILES:
            problems.append("%s: unexpected file at the top level" % item.name)
    entries = []
    for folder in book_folders(root):
        entry, found = check_book(folder)
        problems += found
        if entry:
            entries.append(entry)
    seen = {}
    for entry in entries:
        if entry["id"] in seen:
            problems.append("id \"%s\" is used by both %s and %s"
                            % (entry["id"], seen[entry["id"]],
                               entry["folder"]))
        seen[entry["id"]] = entry["folder"]
    entries.sort(key=lambda entry: (entry["title"].lower(), entry["folder"]))
    return entries, problems


def render(entries):
    """@return: the text of books.json for the given entries"""
    return json.dumps({"books": entries}, indent=2, ensure_ascii=False) + "\n"


def main(argv=None):
    """Run the tool. @return: the exit status"""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true",
                        help="do not write books.json; fail if it is stale")
    parser.add_argument("--subject-root", type=Path, default=ROOT,
                        help="the subject site folder (default: this repo)")
    args = parser.parse_args(argv)
    root = args.subject_root.resolve()
    entries, problems = check_site(root)
    for problem in problems:
        print("PROBLEM:", problem, file=sys.stderr)
    if problems:
        return 1
    wanted = render(entries)
    path = root / BOOKS_FILE
    current = path.read_text(encoding="utf-8") if path.is_file() else ""
    if args.check:
        if current != wanted:
            print("PROBLEM: books.json is out of date; run "
                  "python3 tools/build_hub.py", file=sys.stderr)
            return 1
        print("OK: %d book(s)" % len(entries))
        return 0
    if current != wanted:
        path.write_text(wanted, encoding="utf-8")
    print("books.json lists %d book(s)" % len(entries))
    return 0


if __name__ == "__main__":
    sys.exit(main())
