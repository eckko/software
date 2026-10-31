This repo is the shell for one subject site: a hub page (`index.html`,
`subject.json`, `books.json`) plus one folder per book. Book folders are
written by `tools/add_book.py` from private book repos and hold only
`index.html`, `questions.json`, `images/favicon.png` and `media/*.enc`.
Never add anything else to a book folder, never edit `books.json` by hand
(run `python3 tools/build_hub.py`), and never change a book's `id`.
Run `python3 tests/test_tools.py` and `python3 tools/build_hub.py --check`
after any change. See README.md.
