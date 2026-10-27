# Quiz 1.1 - Answers and grading guidance

**Do not read this before submitting your attempt.**

Marking principle: award points for understanding, not for matching wording. A
correct idea in different words is full marks. A memorised phrase with the wrong
idea behind it is zero.

Critical errors are flagged. Any critical error means the topic is **not** marked
`done`, even at 80 percent or above, because it will cause real design mistakes
in Phases 6 to 8.

---

## Question 1 (20 points)

**Answer.** Broadest to narrowest:

1. artificial intelligence
2. machine learning
3. deep learning
4. large language models

**RAG does not belong in the nesting.** It is not a type of model or a subfield;
it is an architecture you build around a model: retrieve relevant text, assemble
it into the prompt, then generate.

**Grading.**
- 12 points for the correct ordering of the four nested terms.
- 8 points for identifying RAG as the outlier **and** saying what it actually is.
- Partial: 4 of those 8 if they name RAG but only say "it is not a model" without
  saying what it is.
- Note: generative AI sits between deep learning and LLMs. Not asked, but credit
  it if mentioned correctly.

**Critical error:** calling RAG a model, or describing it as something you buy or
download rather than something you assemble.

---

## Question 2 (20 points)

**Answer.** Order status is a structured, per-customer fact. It lives in a
database and should be fetched with an authenticated query or API call, which is
faster, cheaper and exactly accurate. Semantic retrieval over order records would
be slower, more expensive, and would sometimes return the wrong customer's
nearest-matching record, which is both a correctness bug and a privacy incident.
RAG is the right tool for the unstructured half of the problem: shipping policy,
returns rules, help articles.

**Grading.**
- 10 points for identifying it as a lookup, not a retrieval problem.
- 5 points for naming a concrete cost of doing it with RAG (accuracy, latency,
  cost, or cross-customer leakage).
- 5 points for saying what RAG would legitimately be used for in the same system.

**Critical error:** believing embeddings are an appropriate way to retrieve
exact per-customer records. This is the mistake the rest of Phase 6 and 7 depend
on not making.

---

## Question 3 (20 points)

**Answer.** The authorization check stops being enforced and becomes a request.
The data is fetched before the model is ever involved, so by the time the
instruction could apply, the other customer's record is already in the context
window. Anything that can influence the model's input can then influence whether
the instruction is followed: the customer's own wording, or text inside a
retrieved document.

The category is **prompt injection** (specifically indirect prompt injection when
the instruction arrives inside retrieved content). The general principle: a prompt
is a strong suggestion, not a security boundary. Authorization must be enforced in
code, against a verified session, before the data is read.

**Grading.**
- 8 points for recognising that the data is already fetched and exposed.
- 7 points for stating that a prompt cannot enforce a rule.
- 5 points for naming prompt injection.
- Full marks are available without the exact term if the mechanism is described
  correctly, for example "a document could tell the model to ignore that rule".

**Critical error:** arguing that a sufficiently firm or well-worded system prompt
makes this safe.

---

## Question 4 (20 points)

**Answer.** Needed: validate input, document retrieval, assemble context, call the
model, validate output, log the trace. The handbook is unstructured knowledge that
is the same for everyone, so this is the one case where RAG is clearly the right
architecture.

Can be left out: the structured data lookup (there are no per-employee facts), the
tool call and the approval gate (there are no actions). Routing is optional, since
every request takes the same path, though a trivial router is cheap and worth
keeping.

No agent. There is a single fixed sequence of steps with no decisions whose number
is unknown in advance, so a straight-line function is more reliable, cheaper and
easier to test.

**Grading.**
- 8 points for the correct set of needed stages.
- 6 points for correctly excluding lookup, tool and approval.
- 6 points for "no agent" with a justification based on fixed, known steps.
- Accept and credit either answer on routing if the reasoning is sound.
- Credit as a bonus observation, not required: access control still matters if
  parts of the handbook are restricted.

---

## Question 5 (20 points)

**Answer.** A reasonable order, any sensible variation accepted:

1. **Was the right document retrieved at all, and at what rank?** Check the
   retrieved ids in the trace. If the correct source is absent, this is an
   ingestion or retrieval problem and nothing downstream matters.
2. **Did it survive context assembly?** It can be retrieved and then truncated by
   the token budget, or buried in the middle of a long context.
3. **Did the model receive it and ignore it, or contradict it?** Only now is this
   a generation or grounding problem. Also check whether output validation should
   have caught an uncited claim.

**What not to do first: rewrite the prompt.** It is the most tempting and least
informative move. It changes behaviour without identifying the cause, so a lucky
improvement hides the real bug, and you cannot tell whether you fixed anything or
reshuffled the failure. Diagnose the stage first, then change exactly one thing,
then re-measure on a case set that includes this failure.

**Grading.**
- 12 points for three checks that proceed through the pipeline in order rather
  than jumping to the model.
- 5 points for naming prompt rewriting as the thing not to do first.
- 3 points for the reason: it changes behaviour without isolating the cause.
- Bonus credit, not required: adding the failing case to an evaluation set so the
  fix can be shown to work and shown not to break anything else.

**Critical error:** starting with the prompt, or treating "the model is bad at
this" as a diagnosis.

---

## Overall assessment

| Total | Reading |
|---|---|
| 90 to 100, no critical error | Mastered. Mark `done` once the exercise also passes. |
| 80 to 89, no critical error | Pass. Note the weak area and schedule a review in 1 day. |
| 60 to 79 | `needs_revision`. Re-read the weak sections, then re-answer those questions. |
| Below 60, or any critical error | `needs_revision`. Record the misconception in `tracker/mistakes.md` with a targeted corrective question. |

Remember the other half of the gate: the exercise tests must pass, and the
learner must be able to explain the lookup-versus-retrieval distinction out loud,
without notes. A perfect quiz score with no explanation is not mastery.
