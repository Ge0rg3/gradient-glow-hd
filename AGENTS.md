# Gradient Glow - Agents Guide

This file is the canonical map of the codebase for LLM agents.
- For a human-facing overview, the repository layout, the tech stack, setup, and every command, read [README.md](README.md).

Four commands in `src/` share one fitted model file, `src/data/gradient-glow.json`, and one set of modules that evaluate it.

---

## General info
<details>
<summary><b>Documentation policy</b></summary>

Treat every `*.md` file as part of the codebase, and edit them surgically. A doc earns an edit when one of two things is true:

- A line in it is wrong. Change those lines and leave the rest of the section alone.
- Reading the code will not tell you why it works that way.

Nothing else earns an edit. Skip whatever the code already shows.

The docs that matter most:

- [AGENTS.md](AGENTS.md): this file. Code map, conventions, project context.
- [README.md](README.md): human-facing overview, setup, commands.

### Docs are a knowledge base

- Write what the system does. Don't preserve past behaviour, don't leave "previously" notes, and don't call out recent changes.
- No "updated", "as of X" or "this used to be" phrasing. No changelog entries inline.
- When the code changes, edit the text to match. If a section stops applying, delete it - don't leave a stale paragraph beside the new one.
- The git history is the journal. Docs are the source of truth.
- Write what the code can't tell an agent: another system's behaviour, a rule that spans files, how to run or deploy something, and where things live. Point at the file for the rest. A line restating a function's steps or values drifts from the code it copies.

### Style

- Write short paragraphs and bullets. One or two sentences each.
- Plain ASCII: write `->` instead of an arrow, `-` instead of an em dash, `...` instead of an ellipsis character.
- When you compare values across categories, like one colour against another, use a markdown table.
- Link to other docs with relative paths.

### Check what you wrote

Prose drifts from these rules even after you read them. After writing or reworking markdown or comments, run the style-review skill over the diff. At minimum, grep it for non-ASCII characters, semicolons in prose, `Label:` prefixes, "X, not Y" mirroring, a trailing `, which` or `, so` clause on a docstring, and `is`, `are`, `was` or `were` in front of a past participle.

Comment shape is a count, not a judgement. Run this over what you changed - every line it prints is
a comment that runs to a second line or past fifteen words, and each one needs cutting back to a
label:

```bash
awk 'FNR==1{p=""} /^[ \t]*#/ && !/^#!/ {if (p ~ /^[ \t]*#/) print FILENAME":"FNR" second line"; if (NF>16) print FILENAME":"FNR" "NF-1" words"} {p=$0}' <changed files>
```

Two more slip past a grep. Read for them:

- A sentence rating how hard or how important the subject is - "the hard part here", "one of the hardest problems". Delete it.
- A small example paired with a large one to show range - "for a small daily purchase and for a large annual tax payment". Keep one example.

</details>

<details>
<summary><b>Code style</b></summary>

Prioritise readability over cleverness. Optimise for the next person scanning the file.

These rules apply across the whole repository - the commands, the fitting stages, and everything they share.

Every rule takes an id (NM1, CP3, PY7) so reviews can cite the exact rule a finding rests on.

### Naming (NM)

- **NM1** Names describe what a thing is for. Prefer `visibleNotes` over `filteredArray`, `activeVenues` over `data`. Never name one after its type or shape.
- **NM2** Booleans read as a yes or no question: `isEditing`, `hasUnsavedChanges`, `canDelete`. Never `editing`, `flag`, `check`.
- **NM3** Event handlers always indicate the event or action.
- **NM4** Single-letter names only in trivial lambdas (`n => n.id`, `x for x in items`) or loop counters.
- **NM5** Avoid generic names (`data`, `info`, `item`, `result`, `value`, `handler`) when a specific name exists.

### Comments and markdown prose (CP)

Read [prose_rules.md](.claude/skills/style-review/prose_rules.md) before you write a comment or a line of markdown. It carries the worked examples and the wording faults, and it is where the shape of a comment is settled. The rules below are the project's own and win wherever the two disagree.

- **CP1** Clear on the first pass. Rewrite anything you had to read twice.
- **CP2** Write like a developer leaving a quick note. Two to six words over each step, most landing on three, including the obvious steps and the steps that are one line. One comment is one line and one sentence, and fifteen words is the ceiling.
- **CP3** Name the real variable, column, table or field. Naming them is what keeps a comment concrete.
- **CP4** Plain English, and the standard technical word is the plain word. `iterate`, `hash`, `cache`, `upsert`, `regex` and `deduplicate` all stay.
- **CP5** No in-house coinage. Use the name in the code, or the name that a stranger would use. A word the project itself uses is not a coinage.
- **CP6** A step takes a verb. A value, a section or a group of names takes a noun phrase.
- **CP7** A docstring names the thing. A function takes a verb phrase, a class or a module a noun phrase. Saying the name back is fine, and so is restating the whole signature.
- **CP8** One thought per comment. A second clause stays where it carries a reason the code cannot show.
- **CP9** State the positive. A flat ban stays, and so does naming the wrong turn where that turn is a fact.
- **CP10** Cut a word if the line means the same without it. A comment that reads as a paragraph about the code has already lost.
- **CP11** Never describe the caller, the screen or anything downstream.
- **CP12** Put the reason in brackets after the label - `Worker limit (vendor throttles above 5 concurrently)`. Magic numbers, regexes, retry limits, fallbacks, workarounds and business rules all earn one. In markdown, a table cell or the line leading into a list is a label too, so it takes no bracketed reason.
- **CP13** No full stop on a one-line comment or docstring.
- **CP14** One-line label at the top of each file. Skip it when the filename is the label.
- **CP15** Brief comment above a non-trivial function saying why it exists.
- **CP16** Label each stage of a longer function, two to six words. A stage is two or three lines, so
  a label lands about every three. One label over a block that repeats a pattern, a label per line
  where each line does something different.
- **CP17** Blank line above a comment that heads code, unless it opens the function or block.
- **CP19** No previous logic and no design justification. State the business rule the code enforces.
- **CP20** A trailing comment saying its own statement back is noise (`removed += 1  # Increment the removed counter`). A label on its own line is not, over a block or over one statement.
- **CP21** Delete a label a block of names already shows - `/* Families */` above `--font-hero`.
- **CP22** One line by default. A second line only where one line is not enough.
- **CP23** Markdown paragraphs of one or two sentences, or bullets.
- **CP24** Descriptive headings, one idea per section.
- **CP25** Same voice in markdown as in the comments.
- **CP26** Active voice by default. Passive stays only where the paragraph names no actor - `Login via root is disabled`. Where it does, use it.
- **CP27** Drop the articles - `Validate response`, not `Validate the response`.
- **CP28** Spelling and punctuation follow the repository, British or American. Never convert a file from one to the other.

`CP18` is deleted. Its content is now in `CP12`, and the gap marks the removal rather than renumbering the rules below it.

Prefer this:

```python
# Check id takeovers
for old_id in stale_ids:
    if creator_of(old_id) != expected[old_id]:
        takeovers.append(old_id)
```

Over this:

```python
# Old ids whose username now belongs to a different creator, checked for takeover below.
```

And through a function that runs in stages, prefer this:

```python
# Check email in use
taken = db.session.scalar(...)
if taken is not None:
    abort(...)

# Create user
user = Users(...)
```

Over a bare block with one clever aside:

```python
# A departed user's address stays reserved for an admin restore
taken = db.session.scalar(...)
```

And in a docstring, prefer the right-hand column. A function takes the verb phrase, a class or a dataclass the noun phrase:

| Padded | Says the same |
|---|---|
| Settings and options that more than one part of the builder needs | Common settings |
| Keep every attachment once under its hash, with its text pulled out for grep | Store unique attachments and their extracted text |
| Every file the mailboxes carry, saved once per distinct set of bytes | All unique files in the mailbox by hash |
| Check that a message the store already knows still has both its files | Check both files exist |
| Process one message and say what became of it | Process one message |


### Files and modules (FM)

- **FM1** One concern per file. Don't let files grow into monoliths.
- **FM2** Helpers live in the same file as their caller unless shared.
- **FM3** Magic numbers and repeated strings go in a config or constants file.
- **FM4** Imports at top level only (never inside functions). Group: stdlib, third-party, local - blank line between groups.
- **FM5** Module-level constants go right after imports.
- **FM6** Never modify vendored or third-party files. Override or extend in project files.

### AI-tells to avoid (AI)

These patterns make code look obviously machine-generated.

#### Formatting
- **AI1** No decorative comment separators (dashes, box-drawing, ASCII art, `========` section breaks).
- **AI2** No fancy Unicode: write `->` instead of an arrow, `-` instead of an em dash, `...` instead of an ellipsis character.
- **AI3** No auto-generated boilerplate headers or `END` markers.
- **AI4** `noqa` comments are bare codes only (`# noqa: F401`), no trailing explanation.
- **AI5** Don't column-align trailing comments with extra spaces - two spaces before `#`, left ragged (`x = 1  # note`, not `x = 1    # note`). `black` strips the alignment anyway.

#### Comment style
- **AI6** No `Label: description` comments (`// Cleanup: remove stale entries`, `# Note: this is important`). Write the comment naturally without the prefix.
- **AI7** No trailing `, which ...` or `, so ...` clause hung off the end of a docstring. One correct thought, then the quote marks close. A comment may keep a `, so ...` clause carrying a fact the code cannot show.
- **AI8** No "X, not Y" flourish where Y is just X said back in the negative. Give the positive half and stop.
- **AI9** No trailing comment that says its own line back. A label on its own line above a step is not an echo, however short the step - see CP16.
- **AI10** No semicolons in prose - comments, docstrings, log lines, help text, error messages. A semicolon joining two clauses reads as written-up prose, a reliable AI tell. Split the facts apart, drop one, or join with a comma.
- **AI11** No `TODO` or `FIXME` for hypothetical future work.
- **AI17** No anthropomorphism. Code does not say, know, want, decide, carry, hold, witness, hand, ask, answer, refuse, win or agree. A function returns a value, it never "says what became of it", and a service that will not start exits with an error.

#### Unnecessary code
- **AI12** No try/catch around code that can't throw.
- **AI13** No `else` after a block that returns - use early return.
- **AI14** No default cases or fallbacks for values that are always defined.
- **AI15** No single-use abstractions, wrapper functions, or "helper" files for one-off logic.
- **AI16** No defensive error handling at internal boundaries. Validate at system boundaries only.

### Coauthorship and attribution (AT)

- **AT1** Never reference Claude, Anthropic, or "AI assistance" in any artifact - no `Co-Authored-By` lines in commits, no mentions in PR descriptions, no inline comments, no docs. The work ships unattributed.

### Python (PY)

- **PY1** `snake_case` for variables, functions, and files, `PascalCase` for classes, `UPPER_SNAKE_CASE` for module constants, `_prefix` for private helpers.
- **PY2** Formatter: `black` defaults. Linter: `flake8` with `E501` and `E203` ignored. Config in `tox.ini`.
- **PY3** Module structure, top to bottom: module docstring, imports (grouped), module constants, private helpers (`_`-prefixed), public functions/classes/routes, `if __name__ == "__main__"`.
- **PY4** Class structure, top to bottom: `__init__`, private methods (`_`-prefixed), public methods.
- **PY5** A helper that only one class calls belongs on that class, as a `_`-prefixed method. Give it `@staticmethod` when it never touches `self`.
- **PY6** Never interleave helpers between public functions or methods. A function called only from inside the same file is a helper - prefix it with `_` and put it above the public code it serves.
- **PY7** Type-annotate all function signatures.
- **PY8** One-line docstring on every function, six words or fewer wherever it fits. No JSDoc-style parameter listings. When the name already says it, say the name back and stop.
- **PY9** Use `logging` (`logger = logging.getLogger(__name__)`) for output. Never `print()`. Errors go through `logger.exception()` to preserve stack traces.
- **PY10** Catch specific exceptions. Never a bare `except Exception`, and never silently swallow errors.

### JavaScript (JS)

The gallery page and the Plasma script are vanilla JS, no framework or npm.

- **JS1** `camelCase` for variables and functions, `PascalCase` for classes and types, `UPPER_SNAKE_CASE` for constants.
- **JS2** `const` over `let`, never `var`.
- **JS3** `function` declarations for named module-scope functions. Arrows only for inline callbacks.
- **JS4** Ternaries only when short and on one line. Never nest them.
- **JS5** `addEventListener` for event binding. Fetch API for async.
- **JS6** One JS file per page feature.

### CSS (CS)

- **CS1** Per-page or per-component CSS files. No monolithic stylesheet.
- **CS2** Never modify vendored or theme CSS - override in project files.
- **CS3** Prefer classes over inline styles.

</details>

<details>
<summary><b>Workflow rules</b></summary>

### Verify changes

A clean lint proves nothing about the picture. After a change under `src/`, render and compare:

```bash
python src/compare.py
```

Every colour's PSNR without grain should stay within 0.05 dB of its ceiling. The figures to match are in the **How close the renders are** section of [README.md](README.md).

Open a crop sheet in `compare/` and look at it. If you can't look at the output, say so.

A change under `extras/plasma/` only shows on a running Plasma desktop. Re-applying the current images (the `Image=` lines in `~/.config/plasma-org.kde.plasma.desktop-appletsrc`) is a safe check.

### Tests

The project has no unit tests. `compare.py` is the regression check.

For numeric code, add ad-hoc test scripts while you work, but don't check them in. A refactor of `field.py`, `curves.py`, `splines.py`, or `palettes.py` should leave every rendered pixel unchanged. A refactor of `fit.py`, `originals.py`, or anything under `fitting/` should leave `gradient-glow.json` unchanged.

When you add a test suite, document the runner here and in [README.md](README.md).

### Lint before you commit

Format, then lint:

```bash
black src/ extras/
flake8 src/ extras/
```


</details>

## Project-specific info
<details>
<summary><b>Commands - <code>src/*.py</code></b></summary>

Run each command from the repository root as `python src/{command}.py`. The commands import their sibling modules by bare name, so `src/` has to be the script's folder.

</details>

<details>
<summary><b>The model and its conventions</b></summary>

`src/data/gradient-glow.json` is the whole design: a lighting lattice, four curve splines, two glow band tables and a stroke opacity spline per curve, stroke width and level, and one palette per original.

These conventions span `field.py`, `curves.py`, `palettes.py`, and everything under `fitting/`:

- **Design space** is the originals' 1920x1080 frame, with pixel centres on whole numbers.
- **Brightness** is in green levels of the Blue original. A palette converts it to RGB as `brightness * tint + offset`.
- **Distance across a curve** is positive on the inner, lit side. `inner` and `outer` are the band tables for the two sides.
- **Position along a curve** counts from the top of its off-frame extension, `extend_top` before the first knot. Band tables, stroke opacity, and curve shifts all use that origin.
- **Edge softness** `edge_sigma` is in output pixels.
- **Strokes** are painted over the background toward `stroke.level`. Where strokes overlap, the most opaque one sets the coverage.

`fit.py` renders through the same `field.py` functions as `render.py`, but `fitting/smooth.py` and `fitting/strokes.py` rebuild the lattice, band, and stroke terms as design matrices. Change the model's form in all three together, then refit.

Renaming a model key in the code needs a refit, or the same rename in `gradient-glow.json`.

</details>

<details>
<summary><b>What the originals are</b></summary>

The originals are [Gradient Glow](https://store.kde.org/p/1239429) by antechdesigns, from the KDE Store. The store page states no licence.

These facts come from the JPEGs:

- All six are one brightness field under different tints. The tint recipe and the hues are in the **Colours and shades** section of [README.md](README.md).
- The grain adds the same value to R, G, and B. `REFERENCE_COLOUR` has to stay a coloured original.
- Under the grain every channel is banded, and the red channel of Blue moves one level for every four of green.
- The files are JPEGs at about quality 99 with 4:4:4 chroma. `compare.py` and the grain calibration encode renders the same way before measuring them.
- Each curve leaves the frame through the top edge and ends inside it at its tail.

</details>

<details>
<summary><b>Fitting stages - <code>src/fit.py</code> and <code>src/fitting/</code></b></summary>

`fit.py` calls the stages under `fitting/` in order.

The trace seeds in `config.py` are rows, columns, and a node position of this design. Another image needs its own.

</details>

<details>
<summary><b>Shades and the gallery</b></summary>

The gallery page loads `gallery.css` and `gallery.js` from its folder, and `shades.py` copies both from `src/static/` on every run. Edit them under `src/static/`.

</details>

<details>
<summary><b>Plasma helper - <code>extras/plasma/</code></b></summary>

`apply.py` imports nothing from `src/`, and `src/` has no desktop-specific code. Keep it that way.

What Plasma does:

- Plasma keeps one wallpaper per activity per screen. `desktopsForActivity` returns the desktops of one activity, including screens that are not connected.
- `plasmashell` holds the wallpaper config in memory and writes `~/.config/plasma-org.kde.plasma.desktop-appletsrc` itself.
- `plasma-apply-wallpaperimage` sets every desktop of every activity to one image. Never use it here.

</details>

<details>
<summary><b>Where to look next</b></summary>

- Model evaluation -> [src/field.py](src/field.py), [src/curves.py](src/curves.py), [src/splines.py](src/splines.py)
- Tints, shade names, and grain -> [src/palettes.py](src/palettes.py)
- Tuning constants and paths -> [src/config.py](src/config.py)
- Gallery page -> [src/templates/gallery.html](src/templates/gallery.html), [src/static/gallery.css](src/static/gallery.css), [src/static/gallery.js](src/static/gallery.js)
- Plasma helper -> [extras/plasma/](extras/plasma/)
- README images -> [docs/img/](docs/img/)

</details>
