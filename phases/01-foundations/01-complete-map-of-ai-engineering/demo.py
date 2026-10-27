"""Lesson 1.1 demo: one payment-support request walked through all eight stages.

Run it:
    python phases/01-foundations/01-complete-map-of-ai-engineering/demo.py

No network, no API key, no dependencies. The "model" is a deterministic stub, so
every run prints the same thing apart from the measured latency. The point of this
demo is the SHAPE of the system, not the cleverness of the model.

This is an educational toy, not production code. Specifically:
  - the retriever scores by word overlap instead of embeddings (Phase 6 fixes this)
  - the model is a template, so it cannot hallucinate (real ones can)
  - the data sources are dicts in this file instead of a database and a vector store
What IS production-shaped: the stage order, the permission gate sitting in code
before the model call, the output validation, and the per-request trace.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field

# --------------------------------------------------------------------------- #
# Two data sources, deliberately kept apart.
#
# PAYMENTS stands in for your production database: facts about ONE customer.
# Facts like these must never be "retrieved" semantically; they are looked up.
#
# HELP_ARTICLES stands in for the document corpus you would chunk, embed and
# search. This is unstructured knowledge that is the same for every customer.
#
# Confusing these two is the single most common RAG architecture mistake.
# --------------------------------------------------------------------------- #

PAYMENTS: dict[str, dict[str, object]] = {
    "acct_1001": {
        "account_id": "acct_1001",
        "customer_name": "Priya",
        "amount_minor": 49900,
        "currency": "INR",
        "status": "failed",
        "decline_code": "insufficient_funds",
        "card_last4": "4242",
        "attempted_on": "2026-10-25",
        "retry_count": 2,
    },
    "acct_2002": {
        "account_id": "acct_2002",
        "customer_name": "Arun",
        "amount_minor": 129900,
        "currency": "INR",
        "status": "failed",
        "decline_code": "expired_card",
        "card_last4": "1881",
        "attempted_on": "2026-10-26",
        "retry_count": 0,
    },
}

HELP_ARTICLES: list[dict[str, str]] = [
    {
        "id": "help:insufficient_funds",
        "title": "Decline code: insufficient funds",
        "text": (
            "A payment declined with insufficient funds means the bank refused the "
            "charge because the account did not hold enough money at that moment. "
            "The merchant did not reject the payment. A retry usually succeeds once "
            "funds are available."
        ),
    },
    {
        "id": "help:expired_card",
        "title": "Decline code: expired card",
        "text": (
            "An expired card decline means the card's expiry date has passed. "
            "Retrying will not help. The customer must add a new card."
        ),
    },
    {
        "id": "help:refund_policy",
        "title": "Refund policy",
        "text": (
            "Subscription charges can be refunded within fourteen days of the "
            "charge date. Refunds are returned to the original payment method and "
            "take five to seven business days to appear."
        ),
    },
    {
        "id": "help:retry_schedule",
        "title": "Automatic retry schedule",
        "text": (
            "Failed subscription charges are retried automatically after one day, "
            "three days and seven days. After three failed retries the "
            "subscription is paused."
        ),
    },
]


# --------------------------------------------------------------------------- #
# Stage 4 lives here: authorization is a property of the SESSION, in code.
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Session:
    """Who is asking. In a real system this comes from a verified token."""

    user_id: str
    owned_accounts: frozenset[str]

    def owns_account(self, account_id: str) -> bool:
        return account_id in self.owned_accounts


# --------------------------------------------------------------------------- #
# Stage 2: routing. Ordinary Python. No model call.
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Route:
    needs_data_lookup: bool
    needs_document_retrieval: bool
    needs_tool_action: bool
    needs_human_approval: bool
    reason: str


ACCOUNT_WORDS = ("my payment", "my charge", "my card", "my invoice", "my subscription")
POLICY_WORDS = ("why", "policy", "how long", "what does", "mean", "refund policy")
ACTION_WORDS = ("retry", "refund me", "cancel my", "update my card", "charge me")
MONEY_ACTIONS = ("refund me", "charge me", "cancel my")


def route(question: str) -> Route:
    """Decide which capabilities this request needs. This is the planner."""
    q = question.lower()
    wants_own_data = any(word in q for word in ACCOUNT_WORDS)
    wants_policy = any(word in q for word in POLICY_WORDS)
    wants_action = any(word in q for word in ACTION_WORDS)
    needs_approval = wants_action and any(word in q for word in MONEY_ACTIONS)

    reasons = []
    if wants_own_data:
        reasons.append("asks about this customer's own records, so a database lookup")
    if wants_policy:
        reasons.append("asks what something means, so document retrieval")
    if wants_action:
        reasons.append("requests an action, so a tool call")
    if needs_approval:
        reasons.append("the action moves money, so human approval")
    if not reasons:
        reasons.append("no account data or policy knowledge needed")

    return Route(
        needs_data_lookup=wants_own_data,
        needs_document_retrieval=wants_policy,
        needs_tool_action=wants_action,
        needs_human_approval=needs_approval,
        reason="; ".join(reasons),
    )


# --------------------------------------------------------------------------- #
# Stage 3a: structured lookup. Stage 3b: document retrieval.
# --------------------------------------------------------------------------- #

def lookup_payment(session: Session, account_id: str) -> dict[str, object]:
    """Stage 3a. Note the permission gate: in code, BEFORE anything is fetched."""
    if not session.owns_account(account_id):
        raise PermissionError(
            f"user {session.user_id} is not authorised to read {account_id}"
        )
    record = PAYMENTS.get(account_id)
    if record is None:
        raise LookupError(f"no payment record for {account_id}")
    return record


_WORD_RE = re.compile(r"[a-z0-9_]+")


def _words(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


STOPWORDS = frozenset(
    "a an and are as at be by did do does for from how i in is it my of on or "
    "that the this to was what when why will with you your".split()
)


@dataclass(frozen=True)
class Hit:
    doc_id: str
    title: str
    text: str
    score: int


def retrieve(query: str, k: int = 1) -> list[Hit]:
    """Stage 3b. A deliberately primitive retriever: word overlap, not embeddings.

    Phase 6 replaces the scorer with real dense retrieval. The INTERFACE does not
    change: a query goes in, ranked hits come out. That stability is the lesson.
    """
    query_words = _words(query) - STOPWORDS
    hits = []
    for article in HELP_ARTICLES:
        overlap = len(query_words & (_words(article["text"]) | _words(article["title"])))
        if overlap:
            hits.append(
                Hit(article["id"], article["title"], article["text"], overlap)
            )
    # Sort by score, then by id, so ties break deterministically.
    hits.sort(key=lambda h: (-h.score, h.doc_id))
    return hits[:k]


# --------------------------------------------------------------------------- #
# Stage 5 and 6: assemble context, then call the model.
# --------------------------------------------------------------------------- #

# In a real system this is the result of asking a human and waiting. Here it is a
# constant, and it is False, because no human is present in an automated demo.
APPROVAL_GRANTED = False

SYSTEM_INSTRUCTION = (
    "You are a payment support assistant. Answer only from the FACTS and SOURCES "
    "provided. Cite the source id for any explanation you give. If the provided "
    "material does not answer the question, say that you do not know."
)


def assemble_context(
    question: str,
    record: dict[str, object] | None,
    hits: list[Hit],
) -> str:
    """Stage 5. Every part is labelled, so the model can tell data from instructions."""
    parts = [f"[SYSTEM]\n{SYSTEM_INSTRUCTION}", f"[QUESTION]\n{question}"]
    if record is not None:
        money = f"{int(record['amount_minor']) / 100:.2f} {record['currency']}"
        parts.append(
            "[FACTS]\n"
            f"amount={money}\n"
            f"status={record['status']}\n"
            f"decline_code={record['decline_code']}\n"
            f"card_last4={record['card_last4']}\n"
            f"attempted_on={record['attempted_on']}\n"
            f"retry_count={record['retry_count']}"
        )
    if hits:
        rendered = "\n\n".join(f"({h.doc_id}) {h.title}\n{h.text}" for h in hits)
        parts.append("[SOURCES]\n" + rendered)
    return "\n\n".join(parts)


def call_model_stub(context: str) -> str:
    """Stage 6. A deterministic stand-in for an LLM.

    It reads the labelled FACTS and SOURCES out of the assembled context, exactly
    as a real model would, and writes a grounded sentence. Because it is a template
    it cannot invent anything. A real model can, which is why stage 7 exists.
    """
    facts = dict(
        line.split("=", 1)
        for line in context.split("[FACTS]\n", 1)[-1].splitlines()
        if "=" in line and not line.startswith("[")
    ) if "[FACTS]" in context else {}
    source_ids = re.findall(r"\((help:[a-z_]+)\)", context)

    if not source_ids and not facts:
        return "I do not have enough information to answer that."

    if facts:
        reason = {
            "insufficient_funds": (
                "your bank declined it because the account did not have enough "
                "money at the time"
            ),
            "expired_card": "the card on file has passed its expiry date",
        }.get(str(facts.get("decline_code")), "the bank declined the charge")
        citation = source_ids[0] if source_ids else "no source"
        return (
            f"Your payment of {facts.get('amount', facts.get('status'))} on "
            f"{facts.get('attempted_on')} did not go through: {reason}. "
            f"The card ending {facts.get('card_last4')} was used, and we have "
            f"retried {facts.get('retry_count')} times since. [{citation}]"
        )

    body = context.split("[SOURCES]\n", 1)[-1]
    first = body.split("\n\n")[0]
    summary = first.split("\n", 1)[-1].split(". ")[0]
    return f"{summary}. [{source_ids[0]}]"


# --------------------------------------------------------------------------- #
# Stage 7: validate the output. Returns problems rather than raising, because in
# production you want every violation logged, not just the first.
# --------------------------------------------------------------------------- #

def validate_answer(
    answer: str,
    allowed_sources: set[str],
    record: dict[str, object] | None,
) -> list[str]:
    problems: list[str] = []
    cited = set(re.findall(r"\[(help:[a-z_]+)\]", answer))
    if not cited:
        problems.append("no source cited")
    for source in cited - allowed_sources:
        problems.append(f"cited {source}, which was never retrieved")
    if record is not None:
        code = str(record["decline_code"])
        other_codes = {str(r["decline_code"]) for r in PAYMENTS.values()} - {code}
        for wrong in other_codes:
            if wrong in answer:
                problems.append(f"mentions decline code {wrong}, which is not this record")
    # Deliberately narrow phrases. An earlier version of this check flagged the
    # word "refunded" on its own, which marked the refund POLICY answer as a
    # violation. That false positive is worth remembering: a validator that fires
    # on correct answers gets switched off, and then it protects nothing.
    lowered = answer.lower()
    claims_refund = (
        "has been refunded",
        "i have refunded",
        "i issued a refund",
        "i have issued a refund",
    )
    if any(phrase in lowered for phrase in claims_refund):
        problems.append("claims a refund was made, which this pipeline never authorised")
    return problems


# --------------------------------------------------------------------------- #
# The pipeline: stages 1 to 8 in order.
# --------------------------------------------------------------------------- #

@dataclass
class Result:
    answer: str
    stages: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)
    trace: dict[str, object] = field(default_factory=dict)


def handle(session: Session, account_id: str, question: str) -> Result:
    started = time.perf_counter()
    stages: list[str] = []

    # [1] Validate input.
    stages.append("validate_input")
    cleaned = question.strip()
    if not cleaned:
        raise ValueError("empty question")
    if len(cleaned) > 500:
        raise ValueError("question too long")

    # [2] Route.
    stages.append("route")
    plan = route(cleaned)

    # [3a] Structured lookup. [4] is inside lookup_payment, on purpose.
    record = None
    if plan.needs_data_lookup:
        stages.append("lookup_payment_data")
        record = lookup_payment(session, account_id)

    # [3b] Document retrieval.
    hits: list[Hit] = []
    if plan.needs_document_retrieval:
        stages.append("retrieve_documents")
        search_terms = cleaned
        if record is not None:
            # Use the looked-up fact to sharpen the search. This small step is
            # what makes the two data sources work together instead of competing.
            search_terms = f"{cleaned} {record['decline_code']}"
        hits = retrieve(search_terms, k=1)

    # [4] Approval gate for consequential actions.
    #
    # The gate DEFAULTS TO NO. An automated demo has no human to ask, so nothing
    # consequential happens. That default is the whole safety property: an
    # approval step that proceeds when nobody answered is not an approval step.
    if plan.needs_human_approval:
        stages.append("request_human_approval")
        if not APPROVAL_GRANTED:
            stages.append("log_trace")
            amount = (
                f"{int(record['amount_minor']) / 100:.2f} {record['currency']}"
                if record else "the charge"
            )
            answer = (
                "This request needs a person to approve it, so I have not moved any "
                f"money. A support agent will review the request for {amount}."
            )
            elapsed_ms = (time.perf_counter() - started) * 1000
            return Result(
                answer=answer,
                stages=stages,
                problems=[],
                trace={
                    "user_id": session.user_id,
                    "account_id": account_id,
                    "route_reason": plan.reason,
                    "stages": stages,
                    "retrieved": [],
                    "halted_at": "request_human_approval",
                    "tool_executed": False,
                    "approx_prompt_tokens": 0,
                    "approx_cost_usd": 0.0,
                    "output_problems": [],
                    "latency_ms": round(elapsed_ms, 2),
                },
            )

    if plan.needs_tool_action:
        stages.append("execute_tool")

    # [5] Assemble, [6] call the model.
    stages.append("assemble_context")
    context = assemble_context(cleaned, record, hits)
    stages.append("call_model")
    answer = call_model_stub(context)

    # [7] Validate output.
    stages.append("validate_output")
    problems = validate_answer(answer, {h.doc_id for h in hits}, record)

    # [8] Log the trace.
    stages.append("log_trace")
    elapsed_ms = (time.perf_counter() - started) * 1000
    approx_tokens = len(context) // 4
    trace = {
        "user_id": session.user_id,
        "account_id": account_id if plan.needs_data_lookup else None,
        "route_reason": plan.reason,
        "stages": stages,
        "retrieved": [h.doc_id for h in hits],
        "approx_prompt_tokens": approx_tokens,
        # A real provider price. Recorded from day one, because a performance
        # claim without a cost number is not a claim.
        "approx_cost_usd": round(approx_tokens / 1_000_000 * 3.00, 8),
        "output_problems": problems,
        "latency_ms": round(elapsed_ms, 2),
    }
    return Result(answer=answer, stages=stages, problems=problems, trace=trace)


# --------------------------------------------------------------------------- #

def _show(title: str, result: Result) -> None:
    print(f"\n--- {title} " + "-" * max(0, 62 - len(title)))
    print(f"answer:   {result.answer}")
    print(f"stages:   {' -> '.join(result.stages)}")
    print(f"problems: {result.problems or 'none'}")
    trace = dict(result.trace)
    latency = trace.pop("latency_ms")
    print("trace:    " + json.dumps(trace, indent=10)[1:-1].strip())
    print(f"          latency_ms varies per run: {latency}")


def main() -> None:
    priya = Session(user_id="user_a", owned_accounts=frozenset({"acct_1001"}))

    print("=" * 70)
    print("Scenario 1. Needs a lookup AND retrieval. The most common shape.")
    print("=" * 70)
    _show("Why did my payment fail?", handle(priya, "acct_1001", "Why did my payment fail?"))

    print()
    print("=" * 70)
    print("Scenario 2. Retrieval only. No customer data is touched at all.")
    print("=" * 70)
    _show("What does your refund policy say?",
          handle(priya, "acct_1001", "What does your refund policy say?"))

    print()
    print("=" * 70)
    print("Scenario 3. An action. Notice the approval stage appears in the list.")
    print("=" * 70)
    _show("Please refund me for my subscription charge",
          handle(priya, "acct_1001", "Please refund me for my subscription charge"))

    print()
    print("=" * 70)
    print("Scenario 4. Authorisation. The gate is in code, so it cannot be")
    print("talked out of by any wording in the question or in a document.")
    print("=" * 70)
    try:
        handle(priya, "acct_2002", "Why did my payment fail?")
    except PermissionError as exc:
        print(f"\nPermissionError raised before any data was read: {exc}")

    print()
    print("=" * 70)
    print("Count the stages. The model was one of them.")
    print("=" * 70)


if __name__ == "__main__":
    main()
