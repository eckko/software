#!/usr/bin/env python3
"""Tests for tools/build_hub.py and tools/add_book.py.

    python3 tests/test_tools.py
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import add_book  # noqa: E402
import build_hub  # noqa: E402

LOADER = ('<script src="https://cdn.jsdelivr.net/gh/eckko/'
          'recall-quiz-site-template@2.2.1/js/boot.js"></script>')


def make_subject(root):
    """Write a subject site with no books into root."""
    (root / "subject.json").write_text(json.dumps(
        {"title": "Coding"}), encoding="utf-8")
    (root / "books.json").write_text('{\n  "books": []\n}\n',
                                     encoding="utf-8")
    (root / "index.html").write_text("<html></html>", encoding="utf-8")


def make_book(folder, book_id="coding-clean-code", title="Clean Code",
              loader=LOADER, extra_media=None):
    """Write a private book repo checkout, with files that must not ship."""
    (folder / "images").mkdir(parents=True)
    (folder / "media" / "sample").mkdir(parents=True)
    (folder / "book-structure").mkdir()
    (folder / "reference").mkdir()
    (folder / "index.html").write_text(loader, encoding="utf-8")
    (folder / "questions.json").write_text(json.dumps(
        {"id": book_id, "book": title, "questions": []}), encoding="utf-8")
    (folder / "images" / "favicon.png").write_bytes(b"png")
    (folder / "images" / "extra.png").write_bytes(b"png")
    (folder / "media" / "sample" / "cover.enc").write_bytes(b"x")
    (folder / "book-structure" / "chapters.json").write_text("{}")
    (folder / "reference" / "book.pdf").write_bytes(b"pdf")
    if extra_media:
        (folder / "media" / extra_media).write_bytes(b"raw")


class ToolTests(unittest.TestCase):
    """Each test works in its own temporary folders."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.site = base / "site"
        self.site.mkdir()
        make_subject(self.site)
        self.book = base / "book"
        make_book(self.book)

    def test_adds_only_the_four_items(self):
        self.assertEqual(add_book.add_book(self.book, "clean-code",
                                           self.site), [])
        folder = self.site / "clean-code"
        names = sorted(item.name for item in folder.iterdir())
        self.assertEqual(names, ["images", "index.html", "media",
                                 "questions.json"])
        self.assertEqual([item.name for item in (folder / "images").iterdir()],
                         ["favicon.png"])
        self.assertFalse((folder / "book-structure").exists())
        self.assertFalse((folder / "reference").exists())

    def test_books_json_lists_the_book(self):
        add_book.add_book(self.book, "clean-code", self.site)
        data = json.loads((self.site / "books.json").read_text())
        self.assertEqual(data["books"], [{
            "folder": "clean-code", "id": "coding-clean-code",
            "title": "Clean Code"}])

    def test_check_passes_after_add(self):
        add_book.add_book(self.book, "clean-code", self.site)
        self.assertEqual(build_hub.main(
            ["--check", "--subject-root", str(self.site)]), 0)

    def test_check_fails_when_books_json_is_stale(self):
        add_book.add_book(self.book, "clean-code", self.site)
        (self.site / "books.json").write_text('{"books": []}\n')
        self.assertEqual(build_hub.main(
            ["--check", "--subject-root", str(self.site)]), 1)

    def test_adding_again_replaces_the_folder(self):
        add_book.add_book(self.book, "clean-code", self.site)
        (self.book / "media" / "sample" / "cover.enc").unlink()
        add_book.add_book(self.book, "clean-code", self.site)
        self.assertFalse(
            (self.site / "clean-code" / "media" / "sample" / "cover.enc")
            .exists())

    def test_accepts_any_valid_id(self):
        plain = Path(self.temp.name) / "plain"
        make_book(plain, book_id="clean-code")
        self.assertEqual(add_book.add_book(plain, "clean-code", self.site), [])

    def test_rejects_invalid_id(self):
        bad = Path(self.temp.name) / "bad"
        make_book(bad, book_id="Clean Code")
        problems = add_book.add_book(bad, "clean-code", self.site)
        self.assertTrue(any("\"id\" must be" in p for p in problems))

    def test_rejects_duplicate_id_in_another_folder(self):
        add_book.add_book(self.book, "clean-code", self.site)
        problems = add_book.add_book(self.book, "clean-code-copy", self.site)
        self.assertTrue(any("already used" in p for p in problems))
        self.assertFalse((self.site / "clean-code-copy").exists())

    def test_rejects_unencrypted_media(self):
        raw = Path(self.temp.name) / "raw"
        make_book(raw, extra_media="figure.png")
        problems = add_book.add_book(raw, "clean-code", self.site)
        self.assertTrue(any("not an encrypted" in p for p in problems))
        self.assertFalse((self.site / "clean-code").exists())

    def test_rejects_loader_pointing_at_a_branch(self):
        branch = Path(self.temp.name) / "branch"
        make_book(branch, loader='<script src="https://cdn.jsdelivr.net/gh/'
                  'eckko/recall-quiz-site-template@main/js/boot.js">'
                  '</script>')
        problems = add_book.add_book(branch, "clean-code", self.site)
        self.assertTrue(any("exact template tag" in p for p in problems))

    def test_rejects_bad_folder_name(self):
        problems = add_book.add_book(self.book, "Clean Code", self.site)
        self.assertTrue(any("lower-case" in p for p in problems))

    def test_check_flags_a_stray_folder_and_file(self):
        (self.site / "reference").mkdir()
        (self.site / "reference" / "book.pdf").write_bytes(b"pdf")
        (self.site / "notes.pdf").write_bytes(b"pdf")
        entries, problems = build_hub.check_site(self.site)
        self.assertEqual(entries, [])
        self.assertTrue(any("reference" in p for p in problems))
        self.assertTrue(any("notes.pdf" in p for p in problems))

    def test_hub_order_is_by_title(self):
        second = Path(self.temp.name) / "second"
        make_book(second, book_id="coding-abc", title="ABC of Code")
        add_book.add_book(self.book, "clean-code", self.site)
        add_book.add_book(second, "abc", self.site)
        data = json.loads((self.site / "books.json").read_text())
        self.assertEqual([book["folder"] for book in data["books"]],
                         ["abc", "clean-code"])


if __name__ == "__main__":
    unittest.main()
