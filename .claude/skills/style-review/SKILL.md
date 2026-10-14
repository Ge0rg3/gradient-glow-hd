---
name: style-review
description: Review changes against the AGENTS.md style rules and the prose_rules.md writing rules with parallel read-only agents, then apply the fixes. Use it for "style review", "check the comments", "does this follow AGENTS".
---

# Style review

Read the changes (`git diff HEAD`) and understand them. Fix code outside the diff where it plainly
breaks a rule.

A person asking for the review means all the changes. An agent asking mid-job means that job's changes.

Two files hold the rules.

- [prose_rules.md](prose_rules.md), beside this file, covers every word a person reads: comments,
  docstrings, and the prose in `README.md` and `AGENTS.md`.
- [AGENTS.md](../../../AGENTS.md) covers the code. Every rule takes an id apart from the
  "Documentation policy" and "Workflow rules" sections.

`AGENTS.md` wins on a line of prose where the two disagree, because it is the project's own. A
sub-project's own `AGENTS.md` wins for the files it covers. Both prose agents read both files, so they
can apply that order themselves.

## Sub-agents

Spawn these as read-only `general-purpose` agents in parallel, then apply what they find yourself.
Each starts with no context. Give it the changed file list, the rules files to read, and the sections
and rule ids it owns.

- **prose-in-comments** - every comment and docstring, in any language. Reads prose_rules.md and
  `AGENTS.md`. Owns `CM`, `DS`, `TR1`-`TR8`, every CP rule as it applies to a comment or a docstring,
  the comment-shaped AI-tells `AI1`-`AI11` and `AI17`, and `MD3`, `MD4`, `MD5`, `MD11`, `MD13` and
  `MD14`, which prose_rules.md applies to comments too.
- **prose-in-markdown** - the prose in every changed `*.md`. Reads prose_rules.md and `AGENTS.md`.
  Owns `MD`, `TR1`-`TR8`, every CP rule as it applies to a markdown line, and the Style block inside
  "Documentation policy". `TR1`-`TR5` reach a markdown sentence only where it describes what runs.
- **docs-sync** - whether the READMEs and `AGENTS.md` still describe what the code does, and whether
  each line earns its place. Owns "Documentation policy" apart from its Style block and its "Check
  what you wrote" list, both of which are prose mechanics. It judges what a doc says, and how a doc
  reads belongs to prose-in-markdown. Its census covers every line of each doc section the diff
  touches. Give it the brief under "What to tell docs-sync".
- **naming** - owns "Naming" (`NM`), across Python, JavaScript, CSS classes, templates and the keys
  of the model file.
- **python** - owns "Python" (`PY`). On `PY8` it owns the requirement that every function has a
  one-line docstring. What the docstring says is prose-in-comments, under `DS`.
- **frontend** - the gallery page's script, template and stylesheet, and the Plasma script under
  `extras/plasma/`. Owns "JavaScript" (`JS`) and "CSS" (`CS`).
- **structure-and-ai-tells** - everything outside a comment, plus `AT1` wherever it appears, comments
  and docs included. Owns "Files and modules" (`FM`), "AI-tells > Unnecessary code" (`AI12`-`AI16`)
  and "Coauthorship and attribution" (`AT`).

Add one more, named after its section, for any other id-carrying section the diff touches. Split an
agent in two when its share of the diff is too big for one pass.

### What to tell every agent

Give each one a scratch path for its census, then this:

> Write a census to `<path>` before your first finding. One row for every comment, every docstring,
> every block comment and every declared name in the files you own:
>
> `ROW | path:line | the text itself | lines and words | PASS, or the rule ids it breaks`
>
> Count the lines and the words before you judge the row - `2L 28w`. A row past `1L` or past `15w`
> cannot be a PASS.
>
> Then give me the findings drawn from the rows that were not PASS. Each one carries `path:line`, the
> rule id, what is wrong, and the replacement line.

The census is what makes the review complete. Telling an agent to "check every line carefully" scores
the same as telling it nothing.

Markdown has no declarations, so prose-in-markdown and docs-sync get a different census unit: one row
per heading, per paragraph, per bullet and per table cell.

### What to tell docs-sync

Give it this word for word. Five wordings ran side by side on the same guide: the old role text cut
none of 20 lines that restated code and made six of them longer, and this one cut 17 while keeping
the lines about other systems.

> An agent reads the code it is about to change, so a doc line earns its place only with a fact that
> file cannot give it:
>
> - a system the code talks to - another repo, an outside service or API, a browser or crawler - and
>   what that system does. This stays even when a code comment repeats it.
> - a rule that spans files, so no single file shows it.
> - how to run, deploy or debug something.
> - where something lives. Keep one pointer per place, and where two lines point at the same place,
>   cut one and keep the other.
>
> Everything else restates the code: a function's steps, its parameters, a config value, and the
> reason one line of code is written the way it is. A reason like that belongs in a comment on that
> line, so cut it from the doc even when no comment carries it yet.
>
> End each census row with the fact the line carries that the file it names cannot give an agent, or
> `CODE` when it has none. A `CODE` row is a finding: cut it, or replace it with a pointer to the file.
> A row that mixes both is a finding too: trim it to the fact.

Give prose-in-comments and python one line more, because a census of what exists can never find a
comment that should be there and isn't:

> An absence is a row too. Write one for line 1 of every file you own, and one for every bare literal,
> compiled pattern and sleep with no comment above it, and one for every non-trivial function with no
> comment above it and every stage of a long function with no label. Mark those `MISSING`, cite `CM9`,
> `CM14`, `CP15`, `CP16` or `PY8`, and give the line you would add.

Add this, because precedent is the commonest excuse for leaving a fault unreported:

> A matching pattern elsewhere is not a defence. Where existing code breaks a rule, both are findings -
> the new one and the one it copied.

And this for the two prose agents:

> File one finding per faulty line, under the closest rule, and carry a repeated fault as one finding
> naming its instances. Your replacement line has to pass every rule, not only the one you cited.
> Where prose_rules.md and `AGENTS.md` disagree, follow `AGENTS.md` and say so in the finding.

Give prose-in-markdown and docs-sync this too, because a true line that reads well can still repeat
the code:

> In an agent guide - an `AGENTS.md` or another guide written for agents - a line that says what the
> code or its comments already say, or what another doc already says, is a finding even when it is true
> and reads well. Its fix is a cut or a link, never a rewrite. A line stays when it gives what the code
> cannot: a reason the instruction can't do without, a trap, a link across files, or a fact from
> outside the code. A README telling the people who run a tool how it behaves is not an agent guide, so
> this rule skips it.

Then the bar, because the census asks for a verdict on every row and a verdict is easy to give:

> Write each replacement from the code, not from the line you are replacing. Read what the statements
> under it do and write the label you would have written on a blank file. A minimal edit inherits the
> length and the articles of the line it came from: last run the replacements came out at a median of
> seven words where the author writes three, and 71% of them kept an article he would have dropped.
>
> A short, plain, accurate comment with none of the `TR` faults is a PASS. Being able to write a shorter
> label is not a finding. `# Setup new dict`, `# Store results`, `# Get 3 most relevant` and
> `# Find the module name of the caller` are all PASS, the last two at seven and eight words.
> In a comment, length alone is not a finding below ten words, and an article on its own never is.
> File a finding only where you can name the
> fault: an inanimate subject with a human verb, a relative clause with `that` dropped, a second half
> restating the code, an invented verb, a coinage, a trailing comment saying its own line back, a
> `Label:` prefix, a semicolon, a decorative separator, a full stop on a one-liner, a comment past
> fifteen words, a second comment line where the reason would fit in brackets, two sentences where
> one would do, a missing comment, or in markdown a word, bracket or clause the line means the same
> without (`MD14`). In a comment, one word longer than you would have written is none of those.

The three faults that cost the most last time, measured on 35 lines the author wrote himself:

- the echo rule read as a ban on labelling a short step. A label on its own line is right over one
  statement (`CP20`).
- an article deleted for its own sake. `# Restore the original logger's name` is a PASS.
- a domain word read as a coinage. Where the project uses a word, that word is not a coinage.
- `CM1` fired on a seven or eight word label. His own labels run past six about one time in six.

The fault that costs the most in the other direction is `TR3`. A trailing `, so`, `, since`,
`, going on` or `-ing` clause is a restatement unless it names something outside the file - a vendor
limit, an API's shape, a business rule. `# Test whether a file is an image, going on the extension
since the bytes are never read` is a finding. Six of those went unreported last time.

The fault after that is length, and it is the one a census passes most often. Count before you read:
a comment past fifteen words, a comment running to two lines, or two sentences in one comment are
each a finding on sight. Measured over a repository written and then reviewed under these rules, one
comment block in five ran to two lines against the author's one in forty, and the median came out at
ten words against his three. Not one of them was reported.

Don't hand a sub-agent a list of words to hunt for. A word list measured worse than saying nothing, and
it condemned three correct lines.

## Applying the fixes

Rewrite what fails into the shortest correct form.

- Write the new line from the code, not from the old line. Cover the faulty comment, read the
  statements under it, and write the label you would have written on a blank file. Editing the old
  line in place is what leaves a fixed comment twice as long as one written from scratch.
- A finding on one word inside a long comment is a finding on the whole comment. Where the line runs
  past fifteen words or over two lines, the replacement is the label written from the code, not the
  old line with one word swapped.
- Keep every fact. Each number keeps the noun it counted, and a clause carrying a reason stays where
  the instruction needs it.
- In a doc, keep only the facts the code can't give. Where docs-sync cuts or trims a line, apply that
  before any prose rewrite of it. A reworded line that should have gone looks fixed and stays.
- Before cutting a line as a duplicate, check that its twin survives. Each copy gets marked as the
  repeat of the other, so both go unless you keep one.
- Fix the line you were given. Don't reflow the paragraph around it or restyle the file. A comment
  is one line, so the whole comment is the line you were given, both halves of a two-line one
  included.
- Cutting counts as a fix. The shortest correct version is often deletion.
- Try the cut before the rewrite. Where a line still says what to do without the faulty clause, cut
  the clause.

Check the replacement against the same numbers a fresh comment is held to: three words is the middle,
fifteen is the ceiling, one line covers all but one comment in forty, and an article is rare. A
replacement that needs a second line has not been cut far enough.

A missing comment is a real finding, and it is also where reviews do the most damage. When you add one,
write a two-to-six word label in ordinary vocabulary. Never reach for an interesting verb to fill a
line a rule asked for. The last three times a review invented a comment, the verb came from the rule
that asked for it.

## Check your own fixes

Nothing else reviews them. The sub-agents read the tree as it stood before you edited.

Run this over the files you edited before you read a word of them. It prints every comment that runs
to a second line and every comment past fifteen words:

```bash
awk 'FNR==1{p=""} /^[ \t]*#/ && !/^#!/ {if (p ~ /^[ \t]*#/) print FILENAME":"FNR" second line"; if (NF>16) print FILENAME":"FNR" "NF-1" words"} {p=$0}' <changed files>
```

Every line it prints is unfixed, whatever the finding said. Cover the old comment, read the
statements under it, and write the label you would have written on a blank file. A word swapped
inside a long comment leaves it long - the last review reported four two-line comments for one word
each, fixed that word, and left all four at their original length.

Then re-read every line you changed:

1. Is the subject something that runs?
2. Does every noun appear in the code below, or in the product?
3. For a doc line, open the code it names. Is the line true, and does it say something that code
   doesn't?
4. Cut until the next cut would lose a fact. Most labels are two to six words, fifteen is the
   ceiling for any comment with its `CM9` reason counted in (`CM1`), and one line carries both
   (`CM2`). A docstring runs to eight where it fits (`DS`).

Then grep your own edits for the list in `AGENTS.md` under "Check what you wrote": non-ASCII
characters, semicolons in prose, `Label:` prefixes, "X, not Y" mirroring, a trailing `, which` or
`, so` clause on a docstring, and `is`, `are`, `was` or `were` in front of a past participle.

Fix what fails, and count those fixes in the report.

## Output

Once every fix has landed, close with a report in this shape. Every file and line it names is a
markdown link the reader can open:

```markdown
## Style review

Reviewed 6 changed files against AGENTS.md and prose_rules.md. 6 findings - 5 fixed, 1 skipped.

### Prose in comments - 2 fixed
- [src/field.py:88](src/field.py#L88) - AI7 - docstring hung a ", so ..." clause off the end, cut back to the label
- [src/config.py:24](src/config.py#L24) - CM9 - `EVAL_CHUNK = 400_000` had no reason above it, added one

### Prose in markdown - 1 fixed
- [README.md:12](README.md#L12) - MD5 - "as of June" note in the setup section, rewrote it as what the system does now

### Naming - 1 fixed, 1 skipped
- [src/static/gallery.js:31](src/static/gallery.js#L31) - NM5 - renamed `data` to `shadeNames`
- [src/palettes.py:12](src/palettes.py#L12) - NM2 - `check` doesn't read as a yes/no question, skipped: it is public API and [render.py](src/render.py) calls it

### Beyond the diff - 1 fixed
- [src/fit.py:5](src/fit.py#L5) - AI1 - decorative `# ----` separator in untouched code, deleted

Docs and structure came back clean.
```

The link text is the path from the repo root with the line on the end. The target is that same path
anchored `#L88`, or `#L88-L94` over a range.

Link the file alone, with no anchor, where a finding has no one line - a file that should exist and
doesn't, or a whole module. Link any other file the sentence mentions, the way the line above links
`render.py`.

Cite the line as the file stands once your fixes are in. You edit before you write the report, so a
number taken from a census has usually moved - re-grep each line you cite.

With no findings at all, the totals line is the whole report. The closing line names any agent you
didn't spawn, and why.
