# Working in this repository

This is a personal learning repository with one learner and one mentor. These are
the rules that keep it honest.

## The single source of truth

`roadmap/curriculum.json` is canonical and hand-editable. The Mermaid diagram, the
interactive HTML roadmap, the README's embedded overview and the status report are
all **generated from it**. Never edit a generated file:

- `roadmap/roadmap.mmd`
- `roadmap/roadmap-overview.mmd`
- `roadmap/roadmap.html`
- the block between the generated-overview markers in `README.md`

After any change to the JSON:

```bash
python scripts/build_roadmap.py
python -m pytest
```

The build writes nothing and exits nonzero if validation fails, so a broken edit
cannot reach the outputs.

## Editing the curriculum

Adding a topic means adding an object to a phase's `topics` array with every
field the existing topics have. The validator will tell you precisely what is
missing. Things that will be rejected:

- a duplicate topic id, slug or lesson id
- a prerequisite that does not exist, or that points forward in the curriculum
- a dependency cycle (the error names the cycle)
- an `order` field that does not match the position in the array
- a file path that is absolute, contains `..`, uses backslashes, or sits outside
  the phase directory
- `scaffolded: true` when the six files are not on disk
- a status other than `not_started` on a topic that is not scaffolded
- review intervals that differ from the repository policy
- `status: "done"` without complete evidence

Renumbering a phase means renumbering every topic id and every reference to it.
Prefer appending to the end of a phase.

## Status and evidence

Status is a claim; evidence is proof. The fields are separate on purpose, and a
test fails if a topic is `done` without its evidence filled in.

| Status | Means |
|---|---|
| `not_started` | nothing has happened |
| `in_progress` | the lesson has been taught, assessment incomplete |
| `needs_revision` | assessed and a gap was found; counts as incomplete |
| `done` | all four mastery conditions met, with evidence recorded |

`evidence.exercise.passed` is set only from a `pytest` run that actually happened,
and `evidence.exercise.command` records the command that produced it. Phase status
is derived, never hand-edited.

## Lesson files

Each topic directory contains exactly six files:

| File | Rule |
|---|---|
| `lesson.md` | The canonical lesson. The chat explanation must agree with it |
| `demo.py` | Runnable with the documented command, declared dependencies only, no secrets, predictable output where practical |
| `exercise.py` | TODOs and an incomplete implementation. **The solution never appears here** |
| `test_exercise.py` | Meaningful behaviour, edge cases and expected errors. Failure messages state the expected behaviour without giving away the implementation |
| `quiz.md` | Questions only |
| `quiz_answers.md` | Answers and grading guidance. Not revealed before an attempt |

Keep a lesson small enough for one sitting. If a topic needs more, split it into
several topics rather than writing one enormous document.

Demos must distinguish an educational toy from production code, explicitly, in the
module docstring.

## Trackers

`tracker/progress.md` and `tracker/mistakes.md` are written by hand after a real
assessment. Nothing is recorded that did not happen:

- no invented quiz scores
- no invented test results
- no invented misconceptions
- no "completed" topic without evidence

An empty mistake log is a true statement about a learner who has not been assessed
yet, and that is the correct content for it.

## Flashcards

`flashcards/cards.csv` has the columns `front,back,topic,last_reviewed,next_review`
and is written with proper CSV quoting. One concept per card. `topic` must be a
real topic id. Cards come from lessons and from actual recorded misconceptions,
not from guesses about what might be hard.

## Tests

`python -m pytest` verifies the repository and must always be green. It collects
`tests/` only, because lesson exercise tests are meant to fail until the learner
implements them.

Tests assert behaviour. A test that only checks that a file exists is not accepted;
if existence matters, it is checked as part of a behaviour, such as the validator
rejecting a `scaffolded` topic with missing files.

When fixing a bug in the tooling, add the test that would have caught it first.

## Dependencies

The tooling uses the standard library only. `pytest` is the single declared
dependency, because `python -m pytest` is the verification command. A new
dependency needs a stated reason: what it does, why the standard library is not
enough, and what it costs. Phase-specific packages belong in that phase's own
requirements file, so Phase 1 never installs a machine learning stack.

## Git

This directory is **not yet a Git repository**. Nothing is initialised or
committed without the learner's explicit instruction.

Once it is initialised:

- Small, meaningful commits after completed milestones.
- Before suggesting a commit: check `git status`, review the diff, run the tests,
  check for generated files and secrets, then summarise and recommend a message.
- Never commit credentials, API keys, private documents or `.env` files.
- Never amend, reset, force-push or discard work without explicit permission.

Message style:

```
chore(roadmap): add approved curriculum schema
feat(roadmap): generate Mermaid and HTML visualisations
test(roadmap): validate dependencies and output parity
feat(lesson-01): add introductory lesson and exercise
lesson(01-foundations): complete AI engineering overview
```

## Prose style

Hyphens instead of em dashes. Plain English over jargon. Explain the concept before
the framework. Say what a number does not prove.

## Attribution

Topic structure based on roadmap.sh/ai-engineer. Only the structure is reproduced,
in an original educational format. No roadmap artwork, styling or descriptive text
is copied. Keep it that way, and keep the credit line in the generated HTML footer
and in `roadmap/sources.md` accurate.
