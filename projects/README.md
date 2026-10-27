# Projects

This directory holds **notes, evaluation sets, benchmark results and write-ups**
for each project. It deliberately does **not** hold the project code.

## Why the code stays where it is

DocMind, VINI AI, the Payment Recovery Agent and AutoBI already exist in their own
locations. Copying or moving them here would create a second copy that drifts from
the real one, and every measurement taken against a stale copy would be worthless.

So each project keeps its own repository or folder, and this directory holds only
what belongs to the learning process: the baseline numbers, the evaluation data,
the error analysis and the final metrics-first write-up.

## Recording where a project lives

Project paths are **not yet recorded anywhere**, because they have not been
supplied. When a project's phase arrives, set its `path` or `external_url` in
`roadmap/curriculum.json`:

```json
{
  "id": "docmind",
  "name": "DocMind",
  "path": "../../path/to/docmind",
  "external_url": "https://github.com/you/docmind"
}
```

The validator accepts `null` for both, warns if a `path` does not exist, and
rejects an `external_url` that is not an http or https URL. Until a path is set,
nothing in this repository claims to know what is inside any of these projects.

## Layout, once a project phase starts

```
projects/<project-id>/
├── README.md        metrics first: what was measured, under what conditions,
│                    and what the numbers do not prove
├── baseline.md      the measurement taken BEFORE any change
├── architecture.md  the diagram and the trade-offs chosen
├── evals/           evaluation cases and expected outputs
└── results/         raw run output, with the exact command that produced it
```

## Rules

1. **Baseline before change.** A measurement taken after the work is not a baseline,
   and an improvement without one is not an improvement.
2. **Simulated is labelled simulated.** The Payment Recovery Agent is evaluated
   against mock providers and simulated cases. Those results never get described as
   real payment outcomes.
3. **No live credentials, ever.** No real payment keys, no production data, no
   customer documents. Mock providers and sandbox environments only.
4. **Reproducible or it does not count.** Every result records the command,
   the data version and the environment.
5. **State the limits.** Every write-up says what the measurement does not cover.

## Project to phase mapping

| Project | Phase | Status |
|---|---|---|
| DocMind | 7 | path not yet recorded |
| Payment Recovery Agent | 8 and 12 | path not yet recorded |
| VINI AI | 9 | path not yet recorded |
| AutoBI | 11 | path not yet recorded |
| Bounded research or coding agent | 8 | not started; new project |
