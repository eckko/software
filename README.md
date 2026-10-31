# Subject site shell

A template for one **subject** (for example "Coding"): a public GitHub Pages
site with a hub page that lists the subject's books. Each book is a folder
with a Recall Quiz book site inside it. The books are written and kept in
**private** repos (made from
[`eckko/recall-quiz-book-shell`](https://github.com/eckko/recall-quiz-book-shell));
a GitHub Action in each private repo publishes only the quiz files here.

```
<subject repo>/            public, Pages from main, folder /
  index.html               the hub: one button per book
  subject.json             the subject's title
  books.json               written by tools/build_hub.py (do not edit)
  clean-code/              pushed by the private repo "clean-code"
    index.html             loader; the quiz code comes from the CDN
    questions.json
    images/favicon.png     also the book's button on the hub
    media/                 encrypted pictures (*.enc) only
  tools/  tests/  templates/
```

## Start a new subject

1. **Use this template → Create a new repository** (public).
2. Edit `subject.json`: `{ "title": "Coding" }`.
3. **Settings → Pages → Deploy from a branch**, branch `main`, folder
   `/ (root)`. The hub is at `https://<user>.github.io/<repository>/`.
4. Create a fine-grained personal access token limited to this repository
   with **Contents: Read and write**.

## Add a book

In the private book repo:

1. Save the token as the secret `SUBJECT_REPO_TOKEN` in the book repo.
2. Open `.github/workflows/publish-to-subject.yml` and set `SUBJECT_REPO`
   (book repos made from `recall-quiz-book-shell` already contain it; for
   an older repo, copy `templates/publish-to-subject.yml` there). Until
   `SUBJECT_REPO` is set the workflow does nothing.
   The book's folder name defaults to the repo's name; it must be lower-case
   letters, digits and dashes.
3. Push to `main`, or run the workflow by hand. It runs
   `tools/publish_book.sh`, which copies the book and rewrites `books.json`
   in one commit.

To do the same by hand: `python3 tools/add_book.py ../my-book --name my-book`,
then commit.

To remove a book: delete its folder, run `python3 tools/build_hub.py`, commit.

## What is copied, and what is refused

Exactly four things: `index.html`, `questions.json`, `images/favicon.png`
and `media/`. Nothing else in the private repo is read (so `book-structure/`
and any reference files stay private).

`add_book.py` and the check workflow refuse a book when:

- its folder holds anything other than those four items, `images/` holds
  anything other than `favicon.png`, or `media/` holds a file that is not
  `*.enc`;
- `index.html` does not load `js/boot.js` from an exact template tag
  (a branch such as `@main` changes under the site);
- its `id` is missing, is not lower-case letters, digits and dashes, or is
  already used by another book in this site.

When a book is refused, nothing in the site changes.

## Book ids and progress

Progress is saved under the book's `id`, in the reader's browser and in
their account. Every Pages site of one account shares one address
(`<user>.github.io`), so two books with the same id would share progress,
even in different subjects. The tools check ids within this site only, so
give each book an id that no other book of yours uses. **Never change a
book's id** once readers have progress.

## Sign-in sync

Sync needs no setup here. Its settings come with the template tag your book
loads (`js/sync/sync-config.js`), and one Firebase project serves all books.
What is stored is already separate per book: each book has its own progress
document, its own settings document and its own picture key, all named by
the book's id. Add `<user>.github.io` once to Firebase's authorised domains.

## Pictures and copyright

Pictures are published only as encrypted `media/*.enc`. Files made with the
`placeholder` key are hidden, not secret: anyone can decrypt them. For
pictures from copyrighted books, encrypt with a real book key (kept in
Firebase, never in a repo) or leave the pictures out. Keep the questions in
your own words.

## Checks

```
python3 tests/test_tools.py
python3 tools/build_hub.py --check
```

The `check.yml` workflow runs both on every push.

## Try the hub on your computer

Run `python3 -m http.server` in this folder and open
<http://localhost:8000/>. Book pages need an internet connection, because
the quiz code comes from the CDN.
