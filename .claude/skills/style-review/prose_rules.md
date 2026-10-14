# Prose rules

Write like a developer leaving a quick note, not documentation prose.

Covers every comment, docstring and line of markdown in this repository.

Read the examples first and copy their wording.

Ids take the form `CM1`, `DS2`, `TR3`, `MD4`. Nothing here changes a rule number in `AGENTS.md`.

## Comments

Put a label over each step, two or three words. Label the obvious steps, and label a step that is
one line. One line each - a comment that has grown into a sentence about the code has gone wrong.

```python
# Validate config
config = self.validate_config(config)
self.company = config.company_name

# Get articles
articles = fetch_google_news(company, limit=30)
articles = [a for a in articles if a.timestamp]

# Handle empty result
if not articles:
    logger.error("No articles found")
    return None

# Store results
self.report.articles = articles
self.report.article_count = len(articles)
```

More of them:

```python
# Create logging instance
# Run module classes
# Skip if module not enabled
# Attempt 3 times
# Exit if unrecoverable error
# Otherwise attempt again
# Provide full traceback
# Parse uri
# Retain original order
# Filter out duplicate hashes
# Iterate filters not in any seed file
# Keep the town from the venue list
# Set key vars if exist
```

The same labels in JavaScript and TypeScript. A declaration takes a noun phrase, and the articles
drop the same way they do in Python:

```ts
// Attachments folder name
// Stored reference and path
// Extension per pasted mime type
// List files in attachments folder
// Read note text, undefined when unreadable
// Check basename appears in text
// Drop dot-only stem
// Suffix -1, -2 until free
// Convert wheel delta to pixels
// Set pan to keep anchor under cursor
// Elapsed cap per frame (a stalled tab would jump the zoom)
```

- **CM1** Two to six words, and most land on three. About one in six runs past six and one in
  twenty past ten. Fifteen is the ceiling for any comment, a reason and its second line included.
- **CM2** One line. Thirty-nine comments in forty are a single line. A second line is for a `CM9`
  reason that will not fit in brackets, and the two count as one comment against `CM1`.
- **CM3** Drop the articles. `Validate response`, not `Validate the response`.
- **CM4** A step takes a verb. A value, a section or a group of names takes a noun phrase, unless the
  names already show it - delete `/* Families */` over `--font-hero`.
- **CM5** Fold the condition into the object where it folds - `Skip stale rows`,
  `Retry rate limited requests`. Otherwise put it after the verb - `Skip if module not enabled`.
- **CM6** Name the real variable, column, table or field, with no backticks. Backticks belong in
  markdown, where they render.
- **CM7** No full stop on a one-line comment, and a capital first letter. A leading `ie` stays
  lowercase. Write one sentence. Two sentences take a stop between them and come up about once in
  five hundred comments.
- **CM8** A label on its own line is right over any step, including a step of one statement -
  `# Delete zipfile` above `zip_file_path.unlink()`. What is noise is a trailing comment saying the
  statement back - `removed += 1  # Increment the removed counter`.
- **CM8a** One label over a block that repeats a pattern. A label per line where each line does
  something different. Two neighbouring steps that do different things take two labels, however short
  each one is.
- **CM8b** A step is two or three lines, so a label lands about every three lines of code. A function
  carrying one label per six lines is half commented.
- **CM9** Put the reason in brackets after the label - `Worker limit (vendor throttles above 5
  concurrently)`. Magic numbers, regexes, retry limits, fallbacks, workarounds, business rules all earn
  one. The brackets are what keep it short. Give it its own second line only where it will not fit
  in brackets, and cut it back to `CM1` length either way.
- **CM10** `e.g.` and the literal value where a shape is not obvious: `# e.g. ["GPU", "Hardware"]`.
- **CM11** No `Label:` or `Label.` prefix. Cut `Note:`, `Cleanup:` and `Important:`.
- **CM12** No `TODO` or `FIXME` for unscheduled work. State the rule that the code enforces.
- **CM13** Blank line above a comment that heads code, unless it opens the function or block.
- **CM14** One-line label at the top of each file. Skip it when the filename is the label.
- **CM15** No commented-out code. The old version is in git.
- **CM16** Two spaces before a trailing comment, left ragged. Never column-aligned.

`CM9` over a magic constant:

```python
# Worker limit (vendor throttles a single key above 5 in flight)
MAX_WORKERS = 5
```

Three comments written over real code, each of which ran past twenty words before it was cut back.
The reason survives in all three. What went was the second line, the second sentence and the half
that said the code back:

```python
# Daily rate first, monthly second
# Names live outside the database
# Stated columns only (a named None would beat the schema default)
```

## Docstrings

Five to eight words. No full stop.

```python
def validate_config(self, config):
    """Validate module config"""

def process_message(msg):
    """Process one message"""

def zip_and_upload_logs(bucket):
    """Zip logs folder and upload to S3"""

class BuilderSettings:
    """Common settings"""

class SearchResult(BaseModel):
    """Single creator profile"""
```

- **DS1** A function takes a verb phrase. A class, a module or a dataclass takes a noun phrase.
- **DS2** Saying the name back is fine, and so is restating the whole signature.
  `validate_config` -> `"""Validate module config and return validated config"""`.
- **DS3** Never describe the caller, the screen or anything downstream.
- **DS4** No trailing `, so ...` or `, which ...` on a docstring.
- **DS5** Whether a function takes an Args and Returns block is the project's own call. Where it does
  not, a prerequisite or a raised exception goes in the phrase: `"""Validate config, raises on a
  missing key"""`.

## Wording faults

`TR1` to `TR5` apply to comments, docstrings and any markdown sentence about what runs. `TR6` to `TR8`
apply to every line.

**TR1 An inanimate subject with a human verb.** Running code acts, but a file, a table, a row, a
document, a message or an archive does not carry, know, say, hold, witness, hand, ask, decide, answer,
refuse, win or agree.

| Wrong | Right |
|---|---|
| Every file the mailboxes carry, saved once per distinct set of bytes | All unique files in the mailbox by hash |
| Check that a message the store already knows still has both its files | Check both files exist |
| A document the archive has dropped stays only while it still witnesses a row | Archived docs dropped if not referenced by row |
| What v1 knew about each file | What v1 recorded about each file |
| Say what a pass returned | Log what a pass returns |

**TR2 A relative clause hanging off the subject.** With `that` dropped the line reads wrong on the
first pass.

| Wrong | Right |
|---|---|
| Walk the filters no seed file names | Iterate filters not in any seed file |
| A filter row no vendor type maps shows up on no search page | Hide unmapped filter rows from search |
| Read a field off the most recent past listing that names it | Take the value from the most recent listing |

**TR3 A second half restating the code.** Cut it, or put it in brackets. It arrives as a `, so`,
`, since`, `, going on` or bare `-ing` clause hung on the end.

| Wrong | Right |
|---|---|
| The minimum balance the dashboard asks for. Nothing checks it before a run | Minimum balance from the dashboard (no pre-run check) |
| Nearest in time wins, and the key breaks a tie so two runs never disagree | Sort by time, then by key |
| Process one message and say what became of it | Process one message |

One comment in three hundred carries a `, so ...` clause. Keep one for a fact that the code cannot
show: `# This provider has no datetime search so default to the broad one`. The test is whether the
clause names something outside the file - a vendor limit, an API's shape, a business rule. A clause
saying why the line below is correct is a restatement, however true it is.

**TR4 An invented verb, or a described operation, where a flat one exists.** `walk` -> `iterate`,
`carry` -> `is`, `hand back` -> `return`, `stand up` -> `start`, `read off` -> `take`,
`reach` -> `access`, `land` -> `merge`.

The same fault arrives as a phrase describing an operation that one standard verb already names:
`put in front of` -> `prefix`, `take the whitespace off` -> `strip`, `turn into JSON` -> `serialize`,
`cut down to N characters` -> `truncate`, `make safe to put in a URL` -> `url-encode`.

Phrasal verbs stay where the phrase describes where something went, or what a service did, and
names no single operation: `comes back`, `turns up`, `goes to`, `turns away`, `holds up`.

Keep the standard technical word: `iterate`, `hash`, `cache`, `upsert`, `regex`, `deduplicate`,
`normalise`, `validate`, `sort`, `retry`, `foreign key`.

**TR5 A coined noun.** Use the name in the code, or the name that a stranger would use. Write
`account` for `rail`, `mocked` for `canned`. A word the project itself uses is not a coinage, whatever
it looks like from outside.

**TR6 A sentence rating the subject.** Delete it. `The hard part here is knowing what WSL can prove`
becomes `WSL can prove some changes and not others`.

**TR7 An aphorism.** Delete `A disagreement is a judgement`.

**TR8 `we`, `our` and `us`.** Name the thing that runs. `We compare a count` becomes
`The tests compare a count`.

## Markdown

`MD3`, `MD4`, `MD5`, `MD11`, `MD13` and `MD14` apply to comments too.

- **MD1** Paragraphs and bullets, one or two sentences each.
- **MD2** Backticks on every path, command, flag, identifier and literal value, and on a class,
  component or object name - `Input`, `Select`, `localStorage`, `false`.
- **MD3** Plain ASCII only: `->`, `-`, `...`, no em dash, no double hyphen, no glyphs. A spaced `-`
  joining two halves of a thought is fine.
- **MD4** No semicolons anywhere a person reads: prose, comments, log lines, help text, errors.
- **MD5** Describe the system as it stands. Cut `currently`, `previously`, dated notes and future
  plans, though a date inside a literal command stays.
- **MD6** Fix the wrong line. Don't add a section around it.
- **MD7** Name the section's contents in its heading, in sentence case - `## Configure the build
  cache`. A task heading opens on a bare verb, `Import components` rather than `Importing components`.
  A concept heading takes a noun phrase.
- **MD8** Link text names the target. Never `here`, `this document`, `above` or `below`.
- **MD9** Use a table for values compared across categories.
- **MD10** Above a fenced block, state what the command does. No `$` prompt inside it.
- **MD11** State the positive - `A knowledge base, not a journal` is the first half twice. A flat ban
  stays (`Never print()`), and so does naming the wrong turn where that turn is a fact
  (`Set background-color, not the shorthand, or the stripes vanish`).
- **MD12** No signpost opening a sentence - `In short`, `In other words`, `Essentially`. A closing
  sentence tying two facts together is fine. No three-part parallelism built for rhythm, though a
  genuine three-step pipeline is fine.
- **MD13** Active voice by default. Passive stays only where the paragraph names no actor:
  `Login via root is disabled`. Where it does, use it - `The search groups results into tiers`
  rather than `Results are grouped into tiers`.
- **MD14** Cut a word if the line means the same without it - `uses a dedicated index` becomes `uses
  an index`, and `the API's own cache` becomes `the API's cache`. Read the line without each modifier
  and each bracket. Whatever it still says without them goes, even a single word.
- **MD15** Relative paths for links to other files in the repository.
- **MD16** Placeholders in curly braces: `Authorization: Bearer {API_TOKEN}`.
- **MD17** Serial comma before the final item: `JSON, YAML, and TOML`.
- **MD18** A numbered list where the steps run in order.
- **MD19** Spelling and punctuation follow the repository, British or American. Never convert a file
  from one to the other.
- **MD20** Fix a faulty clause by cutting it before rewording it. Where the line still tells the reader
  what to do without the clause, the cut is the fix, a bracketed reason included - `Set PORT in .env
  only (the container reads nothing else)` becomes `Set PORT in .env only`.
- **MD21** For a newcomer, use plain words and name each term once. Explaining more is not
  friendlier.
