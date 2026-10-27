# Mistake log

Every misconception that shows up in an assessment is recorded here, with the
correct understanding and a targeted question to re-test it later. Flashcards are
generated from real entries in this file, not from guesses about what might be
hard.

**No entry is ever invented.** If nothing was got wrong, this file stays empty.
An empty mistake log is a true statement about a learner who has not been
assessed yet, and a useful one.

---

## Open misconceptions

None recorded. No assessment has taken place yet.

## Resolved misconceptions

None recorded.

---

## Entry template

```
### YYYY-MM-DD - <topic id> <topic title>

- **Incorrect belief or answer:** what was actually said or written
- **Correct understanding:** the accurate version, in plain words
- **Why it happened:** if known. "Unknown" is an acceptable and honest answer
- **Corrective question:** a question that will fail if the misconception survives
- **Status:** open | resolved on YYYY-MM-DD
- **Critical:** yes | no   (critical means it would cause real design errors later)
```

### Severity

- **Critical.** Would cause wrong architecture decisions in a later phase. Blocks
  `done` for the topic regardless of the quiz score. Examples: believing RAG is a
  model; believing a prompt can enforce authorization.
- **Ordinary.** Worth re-testing but not blocking. Example: mixing up top-k and
  top-p.

### Review interaction

A misconception resets the topic's spaced-repetition interval to 1 day when it is
recorded, and the corrective question is asked at the next review. It is marked
resolved only after the corrective question is answered correctly on a later date,
not in the same session in which the correct answer was just explained.
