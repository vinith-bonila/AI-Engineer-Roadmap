# Where this curriculum came from

Topic structure based on roadmap.sh/ai-engineer.

This file records exactly what was fetched, when, and how the official roadmap maps
onto the thirteen phases in `curriculum.json`. It exists so that any claim in this
repository about "the official roadmap" can be checked rather than taken on trust.

---

## What was fetched

| Source | Result |
|---|---|
| `https://roadmap.sh/ai-engineer` | **Topic data not available.** The page renders its graph client side. Only the shell was returned: title, intro, FAQ headings, navigation, footer. |
| `https://roadmap.sh/ai-engineer.json` | **The authoritative structure.** 148,737 bytes. 280 nodes: 22 `topic`, 168 `subtopic`, 37 `label`, plus layout nodes. 41 edges. `updatedAt: 2026-10-16T13:43:41.288Z`. Fetched 2026-10-27. |
| `https://roadmap.sh/api/v1-official-roadmap/ai-engineer` | Identical payload to the above. |
| `kamranahmedse/developer-roadmap` on GitHub | Redirects (HTTP 301) to `nilbuild/developer-roadmap`. The old `src/data/roadmaps/ai-engineer/` path no longer exists. |
| `nilbuild/developer-roadmap`, `roadmaps/ai-engineer/content/` | 199 markdown files named `<slug>@<nodeId>.md`. Confirms topic names and node ids. Contains **no** structure file: the graph layout is not in the public repository. |

### Stated limitation

The official roadmap encodes reading order as canvas position rather than as an
ordered list. The sequence below was reconstructed from node `y` and `x` positions
plus the 41 edges. Three edges are drawn upward on the canvas (`MCP -> AI Agents`,
`Development Tools -> Multimodal AI`, `Regression Testing -> Other AI Applications`);
for those, vertical position was used, which agrees with the section labels. The
rendered page was not inspected visually.

---

## The official prerequisites

The roadmap declares its own prerequisites as link nodes: **one of** the Frontend,
Backend or Full-Stack roadmaps. It therefore assumes software engineering
foundations and does not teach Python, Git, the shell, HTTP, SQL or testing.

Phase 1 of this curriculum supplies that prerequisite. It is not a duplication of
the official roadmap; it is the thing the official roadmap points elsewhere for.

The roadmap also links out to sibling roadmaps: Prompt Engineering, AI Agents,
Inference Engineering, Vibe Coding, Claude Code and Forward Deployed Engineer.

---

## Official spine, in canvas order, mapped to phases

| # | Official topic | Covered by |
|---|---|---|
| 1 | Introduction (what an AI engineer is, roles, impact on product development, AI engineer versus ML engineer) | Phase 1 topic 1, revisited in Phase 13 |
| 2 | How LLMs Work (common terminology, core LLM elements, sampling parameters) | Phase 4 |
| 3 | Prompt Engineering (prompt anatomy, prompting techniques, model interaction) | Phase 4 |
| 4 | Context Engineering (context layer, sources, security, evaluation, techniques, tooling) | **Phase 5** |
| 5 | Type of Models (pre-trained, closed versus open source, self-hosted) | Phase 4 |
| 6 | Hugging Face, Ollama, LM Studio, OpenRouter, APIs and SDKs, closed and open model families | Phase 4 |
| 7 | Choosing the Right Model | Phase 4 |
| 8 | What are Embeddings, Embedding Models, Vector Databases, embedding use cases | Phase 6 |
| 9 | What are RAGs (implementing RAG, ways of implementing RAG) | Phase 7 |
| 10 | AI Agents (tools and function calling, ReAct, multi-agents, building AI agents) | Phase 8 |
| 11 | Model Context Protocol (host, client, server, data layer, transport layer, developing with MCP) | Phase 8 |
| 12 | AI Safety and Ethics (prompt injection, privacy, bias, moderation, adversarial testing) | Phase 12, with injection pulled forward into Phases 7 and 8 |
| 13 | LLM Observability (tracing, cost and latency, production monitoring, tooling) | Phase 12, with agent tracing pulled forward into Phase 8 |
| 14 | LLM Evaluations (deterministic, model-based, human, metrics, tooling) | Phase 12, with a minimal harness built in Phase 4 |
| 15 | Regression Testing | Phase 12 |
| 16 | Multimodal AI (image, video, audio, speech, implementing multimodal AI) | Phase 9 |
| 17 | Development Tools (AI-assisted coding tools) | Phase 13 |

---

## Deliberate deviations from the official order

1. **Model platforms and model selection were moved earlier**, into Phase 4, ahead
   of Context Engineering. The official order is Context Engineering, then Type of
   Models, then Choosing the Right Model. Reason: you cannot practise prompting or
   context engineering before you can call a model. This is the only significant
   reordering inside the overlapping region.
2. **AI Safety is split rather than taught as one block after MCP.** Prompt
   injection through retrieved documents is taught in Phase 7, and tool
   permissions, budgets and traces in Phase 8, because Phase 8 builds an agent
   that touches payment data. The rigorous treatment stays in Phase 12.
3. **A minimal evaluation harness is built in Phase 4**, long before the official
   evaluation section. Reason: every later phase makes a measured claim, and a
   claim without a baseline is not a claim.
4. **Development Tools stay last**, matching the official order, so that agentic
   coding tools arrive after the fundamentals are evidenced rather than before.

---

## Added beyond the official roadmap

The official roadmap frames the role around using pre-trained models, so it
contains no mathematics, no deep learning, no fine-tuning depth, no backend or
deployment engineering and no career material. Those are additions, marked in
`curriculum.json` with `"source": "user"` or `"source": "recommended"`:

- Phase 1, Programming and Software Foundations (the official prerequisite)
- Phase 2, Mathematics and Machine Learning Fundamentals
- Phase 3, Deep Learning Essentials, scoped to reading a model card and explaining a transformer
- Phase 10, Fine-Tuning and Model Optimization (official coverage is two subtopics)
- Phase 11, Backend Engineering and Deployment (official coverage defers to the Backend roadmap)
- Phase 13, Portfolio and Career

Counts by source are reported by `python scripts/build_roadmap.py` and can be
recomputed from `curriculum.json` at any time.

---

## Copyright note

Only the topic structure is reproduced, in an original educational format. No
roadmap artwork, styling, layout or descriptive text was copied. Lesson text,
diagrams, demos, exercises and quizzes in this repository are original.
