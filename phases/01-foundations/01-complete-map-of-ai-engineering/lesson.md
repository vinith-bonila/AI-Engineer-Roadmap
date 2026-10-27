# 1.1 The Complete Map of AI Engineering

| | |
|---|---|
| **Phase** | 1. Programming and Software Foundations |
| **Topic ID** | `p01-t01` |
| **Lesson ID** | `p01-t01-lesson` |
| **Prerequisites** | None |
| **Estimated lesson time** | 45 minutes |
| **Exercise time** | 45 to 60 minutes |
| **Source** | Topic present in the official roadmap (Introduction section) |

---

## 1. Learning objectives

By the end of this lesson you should be able to:

1. Explain how AI, machine learning, deep learning, generative AI, LLMs, RAG and agents relate to each other.
2. Trace one user request through an AI application from input to output.
3. Decide when an application does **not** need RAG or agents.
4. Describe what an AI engineer does differently from an ML engineer.

---

## 2. Simple definition

**AI engineering is the practice of building reliable software products on top of models that someone else has already trained.** You are not inventing the model. You are deciding what reaches it, what it is allowed to do, and how you know whether it worked.

---

## 3. A real-world analogy

Think of a very capable new hire on their first day.

They are articulate, widely read, fast, and they will answer any question you put to them. But they have never seen your company's data, they have no login credentials, they cannot look anything up, they do not know today's date, and they will never say "I don't know" unless you tell them that is allowed.

Your job is not to make them smarter. Your job is to:

- hand them the right document before they answer (**retrieval**),
- give them a phone and a specific list of people they may call (**tools**),
- require a manager's signature before they move money (**approval**),
- check their work before it reaches the customer (**validation**),
- and keep a record of what they did so you can find out what went wrong (**observability**).

That list is the job. The model is the new hire. Everything else is engineering.

---

## 4. Why AI engineers need this map

Without the map, three expensive mistakes are nearly guaranteed:

1. **Reaching for the wrong tool.** Adding RAG to a problem that was a database query. Adding an agent to a problem that was a three-step script.
2. **Blaming the wrong layer.** The answer was wrong, so the prompt gets rewritten twenty times, when the actual cause was that retrieval never returned the right document.
3. **Claiming things you cannot show.** "We improved accuracy" is not a claim until you can say accuracy of what, measured on which cases, against which baseline.

You already have four projects. You have built retrieval, agents, and voice. The purpose of this lesson is to give you precise names for the parts you built, so that for the rest of this curriculum we can both say exactly which layer we are talking about.

---

## 5. Step-by-step explanation

### 5.1 The nesting of terms

These terms are often used as if they were alternatives. They are not. Most of them contain each other.

```
+-------------------------------------------------------------+
| ARTIFICIAL INTELLIGENCE                                     |
|  Any system that performs tasks we associate with           |
|  intelligence. Includes hand-written rules.                 |
|                                                             |
|  +-------------------------------------------------------+  |
|  | MACHINE LEARNING                                      |  |
|  |  Behaviour learned from data instead of written as     |  |
|  |  rules. Regression, decision trees, clustering.        |  |
|  |                                                       |  |
|  |  +-------------------------------------------------+  |  |
|  |  | DEEP LEARNING                                   |  |  |
|  |  |  ML using many-layered neural networks.         |  |  |
|  |  |                                                 |  |  |
|  |  |  +-------------------------------------------+  |  |  |
|  |  |  | GENERATIVE AI                             |  |  |  |
|  |  |  |  Models that produce new content.         |  |  |  |
|  |  |  |                                           |  |  |  |
|  |  |  |  +-------------------------------------+  |  |  |  |
|  |  |  |  | LARGE LANGUAGE MODELS               |  |  |  |  |
|  |  |  |  |  Generative models over text that   |  |  |  |  |
|  |  |  |  |  predict the next token.            |  |  |  |  |
|  |  |  |  +-------------------------------------+  |  |  |  |
|  |  |  +-------------------------------------------+  |  |  |
|  |  +-------------------------------------------------+  |  |
|  +-------------------------------------------------------+  |
+-------------------------------------------------------------+

Outside the nesting, because they are not model types:

  RAG     = an architecture. Retrieve relevant text, then put it in
            the prompt, then generate. It is plumbing around an LLM.

  AGENTS  = a control flow. The model is called in a loop and is
            allowed to choose actions. It is a program shape, not
            a kind of model.
```

The single most useful thing on that diagram is the bottom note. **RAG and agents are not models.** They are things *you* build. Nobody ships you a RAG. You assemble one out of a retriever, a prompt, a model call and some validation. That is why they are an engineering discipline rather than a research one, and that is why they are your job.

### 5.2 What an AI engineer actually does at a company

The official roadmap is blunt about this: an AI engineer uses pre-trained models and existing AI tools rather than building models from scratch. In practice the weekly work looks like this:

| Activity | Roughly how much of the job |
|---|---|
| Deciding what information reaches the model, and in what order | a lot |
| Writing the glue: APIs, data access, validation, error handling | a lot |
| Building evaluation sets and measuring changes | more than people expect |
| Investigating why one specific answer was wrong | a lot |
| Prompt wording | less than people expect |
| Training or fine-tuning a model | occasionally, and only with evidence |

Contrast with an ML engineer, who owns datasets, training pipelines, model architecture and offline model metrics. The boundary is not rigid, and at a small company one person does both. But the centre of gravity differs: an **ML engineer makes a model**; an **AI engineer makes a product that depends on a model**.

### 5.3 How an AI application works, input to output

Here is the shape almost every serious LLM application has. Not every stage is present in every system, which is exactly the point.

```
  user input
      |
      v
 [1] VALIDATE INPUT  ------------- reject empty, oversized, abusive input
      |
      v
 [2] ROUTE / PLAN  --------------- what does this request actually need?
      |                            (this is where you decide whether you
      |                             need RAG, a tool, or neither)
      |
      +--> [3a] STRUCTURED DATA LOOKUP ---- SQL, API: facts about THIS user
      |
      +--> [3b] DOCUMENT RETRIEVAL -------- embeddings + search: policy text
      |                                     (this branch is "the R in RAG")
      |
      +--> [3c] TOOL CALL ---------------- an action: retry, email, refund
      |              |
      |              v
      |         [4] PERMISSION + APPROVAL -- may this user do this?
      |                                      does a human must sign off?
      v
 [5] ASSEMBLE CONTEXT  ----------- instructions + user question + retrieved
      |                            facts + retrieved documents, within a
      |                            token budget
      v
 [6] CALL THE MODEL  ------------- the only stage that involves an LLM
      |
      v
 [7] VALIDATE OUTPUT  ------------ is it valid JSON? is every claim
      |                            supported by the retrieved text?
      v
 [8] LOG THE TRACE  -------------- inputs, retrievals, tokens, cost,
      |                            latency, decision, outcome
      v
   response to user
```

Notice how little of that diagram is the model. Stage 6 is one box. Stages 1, 2, 4, 5, 7 and 8 are ordinary software engineering, and they are where reliability comes from.

---

## 6. Practical use case: "Why did my payment fail?"

One running example for the whole lesson. A customer of a subscription business opens support chat and types:

> Why did my payment fail?

Walk the stages.

**[1] Validate input.** Non-empty, short enough, a real question. Pass.

**[2] Route.** This question has two halves, and separating them is the whole skill:

- "my payment" is a **fact about this specific customer**. No amount of model cleverness can produce it. It must come from the payments database. This is a lookup, not retrieval.
- "why did it fail" needs the **meaning of the decline code**, which lives in a provider's documentation. That is a document retrieval problem.

**[3a] Structured data lookup.** Query the payments table for the latest charge on this account. It returns, say: amount 499.00 INR, status `failed`, decline code `insufficient_funds`, card ending 4242, attempted 2 days ago, two retries since.

**[3b] Document retrieval.** Search the help corpus for `insufficient_funds`. It returns a paragraph: what the code means, that the bank declined it rather than the merchant, and that a retry typically succeeds after the customer adds funds.

**[4] Permission.** Before any of this reaches the model, check that the authenticated caller owns that account. This check lives in your code, against your session. It is **not** an instruction in the prompt. A prompt instruction is a request; an authorization check is a gate.

**[5] Assemble context.** Build one request: a system instruction ("answer only from the provided facts; if the facts do not answer the question, say so"), the customer's question, the payment record, and the retrieved paragraph with its source id.

**[6] Call the model.** It writes two sentences of plain English that a stressed customer can read, grounded in the facts you supplied.

**[7] Validate output.** Does the answer cite a source that was actually retrieved? Does it mention a decline code that was actually in the record? Does it avoid promising a refund you did not authorise?

**[8] Log the trace.** Which documents were retrieved, how many tokens, what it cost, how long it took, and what the customer did next.

### Does this need an agent?

No. There is one decision and a fixed sequence of steps. A plain function with branches is more reliable, cheaper, easier to test and easier to explain. An agent becomes justified when the number of steps genuinely cannot be known in advance.

### Does this need RAG?

Half of it does. The decline-code explanation genuinely benefits from retrieval. The payment facts do not: that is a database query, and routing it through embeddings would be slower, more expensive and less accurate.

### Does the summary even need an LLM?

Honest answer: for the top ten decline codes, a written template filled in from the database would be more accurate, instant and free. The LLM earns its place on the long tail of unusual questions. **"Where can I delete the LLM?" is a senior question, not a cynical one.**

---

## 7. The demo

Run it:

```bash
python phases/01-foundations/01-complete-map-of-ai-engineering/demo.py
```

It simulates the whole pipeline above with no network, no API key and no dependencies. The "model" is a deterministic stub, so the output is identical every run. That is on purpose: the lesson is the shape of the system, not the cleverness of the model.

### Key lines explained

```python
PAYMENTS: dict[str, dict[str, object]] = {...}
HELP_ARTICLES: list[dict[str, str]] = [...]
```
Two fake data sources. `PAYMENTS` stands in for your production database: per-customer facts. `HELP_ARTICLES` stands in for the document corpus you would embed and search. Keeping them as separate structures in the demo is deliberate, because confusing these two is the most common architecture mistake in RAG systems.

```python
def route(question: str) -> Route:
```
The planner from stage 2. It decides which downstream capabilities are needed. Note it is ordinary Python with no model call. Routing with cheap deterministic logic where you can is a real production pattern, not a simplification for teaching.

```python
if not session.owns_account(account_id):
    raise PermissionError(...)
```
The authorization gate from stage 4, in code, before retrieval. If this lived in the prompt it would be a suggestion that an injected document could talk the model out of.

```python
def retrieve(query: str, k: int = 1) -> list[Hit]:
    scored = [(keyword_overlap(query, a["text"]), a) for a in HELP_ARTICLES]
```
A deliberately primitive retriever: word overlap, not embeddings. You will replace it with real dense retrieval in Phase 6. The point here is that retrieval is *scoring and ranking*, and that the interface (query in, ranked hits out) is the same whether the scorer is three lines or a vector database.

```python
def validate_answer(answer: str, allowed_sources: set[str], record: dict) -> list[str]:
```
Stage 7. It returns a list of problems rather than raising, because in production you want to log every violation, not just the first.

```python
trace = {"stages": stages, "retrieved": [...], "latency_ms": ..., "cost_usd": ...}
```
Stage 8. Note that cost and latency are recorded per request from the very first day. Retrofitting this later is painful, and without it you cannot make a single honest performance claim.

---

## 8. Memory trick

**"The model is one box out of eight."**

When something goes wrong, say the stages out loud in order and ask which one failed:

> **V**alidate, **R**oute, **L**ookup, **R**etrieve, **A**ssemble, **M**odel, **V**erify, **L**og

Mnemonic: **V**ery **R**arely **L**ucky, **R**eally **A**lways **M**easure **V**ery **L**oudly.

The habit it builds matters more than the words: before touching the prompt, name the stage.

---

## 9. Common misconceptions and mistakes

| Misconception | What is actually true |
|---|---|
| "RAG is a kind of model." | RAG is an architecture you build around a model. Retrieve, assemble, generate. |
| "An agent is a smarter LLM." | An agent is a control loop in which a model may choose actions. The model is unchanged; the program shape is different. Autonomy is traded for reliability. |
| "More context is always better." | Longer context costs more, is slower, and relevant information gets lost in the middle. Precision beats volume. |
| "If the answer is wrong, fix the prompt." | Usually the retrieval failed, or the data was never fetched. Diagnose the stage first. |
| "Generative AI is all of AI now." | A huge amount of production machine learning is still classification, ranking and forecasting. Embeddings alone solve many problems with no LLM at all. |
| "The model can enforce rules I write in the prompt." | A prompt is a strong suggestion. Permissions, budgets and limits must be enforced in code. |
| "I built a RAG system, so I understand embeddings." | Shipping something is not the same as being able to explain why it works and predict how it breaks. This curriculum separates the two deliberately. |
| "An AI engineer needs to train models." | The official roadmap explicitly frames the role around using pre-trained models. Fine-tuning is one tool, used with evidence, not the default. |

---

## 10. Interview questions

**Q1. A customer support team wants an assistant that answers questions about a customer's own orders. Do you need RAG?**

Model answer: Mostly no. Order details are structured per-customer facts, so the right mechanism is an authenticated database or API query, which is faster, cheaper and exactly accurate. RAG earns its place only for the unstructured half: policies, help articles, shipping terms. I would build the data lookup first, measure how many real questions it already answers, and add retrieval for the remainder. I would also enforce the customer-to-order authorization check in code before anything reaches the model, because a prompt instruction is not an access control.

**Q2. What is the difference between an AI engineer and an ML engineer?**

Model answer: An ML engineer owns the model: data collection, training pipelines, architecture and offline model metrics. An AI engineer owns a product built on a model that already exists: what context reaches it, which tools it may use, how outputs are validated, how the system is evaluated, monitored, secured and costed. The skills overlap, and at a small company one person does both, but the deliverable differs. An ML engineer ships a model; an AI engineer ships a system whose reliability mostly comes from everything around the model.

**Q3. Your RAG assistant gives a confidently wrong answer. Walk me through your diagnosis.**

Model answer: I do not touch the prompt first. I pull the trace for that request and check the stages in order. Was the right document even in the corpus? Did retrieval return it, and at what rank? Did it survive assembly, or was it truncated by the token budget? Did the model receive it and ignore it? Did the output validator miss an uncited claim? Each of those is a different fix: ingestion, retrieval or reranking, context assembly, grounding instructions, or validation. Then I add the failing case to an evaluation set so that whatever I change, I can show it fixed this case and did not break the others.

---

## 11. Exercise

Specification is in [`exercise.py`](exercise.py). You will implement two functions:

1. `plan_request(message, user_owns_account)` - decide which capabilities a request needs, returning a `Plan`. This is stage 2 of the diagram.
2. `pipeline_stages(plan)` - turn a plan into the ordered list of stages that will run.

The keyword constants are given to you. The decision logic is yours. There is no LLM involved; this is a reasoning exercise about architecture, written in plain Python.

Run the tests:

```bash
python -m pytest phases/01-foundations/01-complete-map-of-ai-engineering/test_exercise.py -v
```

They will fail until you implement the functions. Read each failure message: it tells you the expected behaviour without giving you the implementation.

---

## 12. Recall quiz

Five questions in [`quiz.md`](quiz.md). Answer them in your own words before looking at anything else. Answers and grading guidance are in `quiz_answers.md`, which you should not open until you have submitted your attempt.

---

## 13. Summary

- AI contains ML contains deep learning contains generative AI contains LLMs.
- RAG and agents are **architectures you build**, not models you buy.
- An AI application is roughly eight stages, and the model is one of them.
- Per-customer facts come from a **lookup**; unstructured knowledge comes from **retrieval**. Confusing these two is the classic mistake.
- Agents are for genuinely unknown step counts. Otherwise write the workflow.
- Permissions, budgets and limits are enforced in code, never in a prompt.
- Cost, latency and a trace are recorded from day one, or no later claim is credible.

---

## 14. Flashcard candidates

| Front | Back |
|---|---|
| Is RAG a model or an architecture? | An architecture: retrieve, assemble context, generate. You build it. |
| What makes a system an agent rather than a workflow? | The model chooses actions in a loop; the number of steps is not known in advance. |
| Per-customer fact: lookup or retrieval? | Lookup, against an authenticated database or API. |
| The eight stages of an AI request | Validate, route, lookup, retrieve, assemble, model, verify, log |
| Where must an authorization check live? | In code, before the model call. Never in the prompt. |
| ML engineer versus AI engineer | ML engineer ships a model; AI engineer ships a system built on an existing model. |
| First question when an answer is wrong | Which stage failed? Check the trace before editing the prompt. |

---

## 15. Review schedule

This topic enters the spaced repetition queue on assessment, with intervals of 1, 3, 7, 14 and 30 days. A correct review advances the interval; an incorrect one resets it to 1 day. Your schedule lives in `tracker/review_schedule.json`.

---

## 16. Completion checklist

This topic is marked `done` only when **all** of the following are true. A tick without evidence does not count.

- [ ] I read the lesson and ran `demo.py` successfully.
- [ ] I implemented both functions in `exercise.py`.
- [ ] `python -m pytest phases/01-foundations/01-complete-map-of-ai-engineering/ -v` passes.
- [ ] I answered all five quiz questions and scored at least 80 percent.
- [ ] I explained, in my own words and without notes, the difference between a lookup and a retrieval.
- [ ] I correctly decided, for a system I was not shown, whether it needs RAG or an agent.
- [ ] Any misconception found during the assessment is recorded and resolved in `tracker/mistakes.md`.

---

*Topic structure based on roadmap.sh/ai-engineer. This lesson text, diagrams, demo and exercise are original.*
