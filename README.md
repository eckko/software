# Software

A subject site whose books are **encrypted**: a
public GitHub Pages site with a hub page that lists the subject's books. Each
book is a folder holding only encrypted files and a few tiny pages. This repo
holds no code of its own. It is built from the same shell as
[`eckko/habit-reader`](https://github.com/eckko/habit-reader):

- The **hub UI** (sign-in screen, shelf with covers, search, sort, filters,
  gear) is loaded by the fixed `index.html` from
  [`eckko/subject-site-template`](https://github.com/eckko/subject-site-template)
  on jsDelivr, at the version in `subject.json`'s `uiVersion` (`"2"` = newest
  2.x.x). Change the UI in that repo, never here. A new major version is
  adopted by hand by editing `uiVersion`.
- This subject's **own look** (the "Terminal" sign-in screen and its icons) is the
  one UI thing kept here, in `.theme/`, named by `theme` in `subject.json`; the
  template loads it (UI 2.1.0 or newer).
- The **book pages** (the gate, the reader and the quiz) load from
  [`eckko/recall-quiz-site-template`](https://github.com/eckko/recall-quiz-site-template)
  on jsDelivr by an exact tag such as `3.2.5` (no `v`, never a branch).
  `subject.json`'s `templateTag` names the tag whose tools check this site.

```
index.html          the hub loader (fixed, never edited)
subject.json        title, templateTag, uiVersion, theme, optional bookDetails
.theme/             this subject's look: gate.css, terminal.svg, icon.svg,
                    apple-touch-icon.png (no book content)
books.json          written by the template's tools/site/build_hub.py
<book>/             pushed by the private book repo's publish workflow
  index.html  read.html  quiz.html  book.json
  data/  media/  quiz/       encrypted *.enc files only
.github/workflows/check.yml  runs the template's checks at templateTag
```

Nothing readable from a book is stored here: only ciphertext. The key is never
stored in any repo; one key opens every book of the subject (Firestore
`users/<uid>/mediaKeys/subject`, field `key`, or pasted in the page).

## Add a book

In the private book repo: save the token as `READER_SUBJECT_REPO_TOKEN` and
the key as `SUBJECT_KEY`, copy `templates/publish-encrypted-book.yml` from the
quiz template to `.github/workflows/`, set the values at the top (the target
repo is `eckko/software`, the folder name is lower-case letters, digits and
dashes) and run it. It builds the book, checks it and commits it here with the
rewritten `books.json`.

To remove a book: delete its folder, run the template's
`tools/site/build_hub.py` to rewrite `books.json`, commit.

## Change the template version

Re-run each book's publish workflow with the new `TEMPLATE_TAG`, then set
`templateTag` in `subject.json` to the same tag. A tag is immutable: a fix is a
new tag.

## Book ids and progress

Progress is saved under the book's `id`. Every Pages site of one account shares
one address (`<user>.github.io`), so two books with the same id would share
progress. **Never change a book's id.**

## Checks

`.github/workflows/check.yml` runs the template's `build_hub.py --check` on
every push. Run the `check-copywright` skill before the repo goes public: it
must show 0 HIGH.
