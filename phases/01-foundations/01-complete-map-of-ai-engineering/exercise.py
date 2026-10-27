"""Exercise 1.1 - the router and the pipeline plan.

You are building stage 2 of the pipeline from the lesson: the part that decides
which capabilities a request actually needs. No model is involved. This is a
reasoning exercise about architecture, written in plain Python.

Everything above the TODO markers is given to you, including the phrase lists.
Do not change the given constants or the Plan dataclass; the tests rely on them.

Run the tests from the repository root:

    python -m pytest phases/01-foundations/01-complete-map-of-ai-engineering/ -v

They fail until you implement both functions. Read each failure message: it tells
you what behaviour is expected without telling you how to write it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# --------------------------------------------------------------------------- #
# Given constants. Do not edit.
# --------------------------------------------------------------------------- #

MAX_MESSAGE_LENGTH = 500

#: Phrases that mean the customer is asking about their OWN records.
#: These facts live in a database. They are looked up, never retrieved
#: semantically.
ACCOUNT_PHRASES: tuple[str, ...] = (
    "my payment",
    "my charge",
    "my card",
    "my invoice",
    "my subscription",
    "my refund",
)

#: Phrases that mean the customer is asking what something MEANS or what the
#: rules are. That knowledge lives in unstructured documents, so it is a
#: retrieval problem.
POLICY_PHRASES: tuple[str, ...] = (
    "policy",
    "how long",
    "what does",
    "what is",
    "why",
    "mean",
)

#: Phrases that request an ACTION rather than an answer.
ACTION_PHRASES: tuple[str, ...] = (
    "retry",
    "refund me",
    "cancel my",
    "update my card",
    "charge me",
)

#: Actions that move money or end a paid relationship. These need a human.
MONEY_ACTION_PHRASES: tuple[str, ...] = (
    "refund me",
    "cancel my",
    "charge me",
)

#: Questions common enough to answer from a written template filled in from the
#: database. These need NO model at all, which is the point of including them.
TEMPLATED_QUESTIONS: frozenset[str] = frozenset({
    "what is my current balance",
    "when is my next charge",
    "what card is on file",
})

#: The only stage names you may return, in the only order they may appear.
STAGE_ORDER: tuple[str, ...] = (
    "validate_input",
    "route",
    "lookup_payment_data",
    "retrieve_documents",
    "request_human_approval",
    "execute_tool",
    "assemble_context",
    "call_model",
    "validate_output",
    "log_trace",
)


@dataclass(frozen=True)
class Plan:
    """What one request needs. Produced by plan_request, consumed by pipeline_stages."""

    needs_llm: bool
    needs_data_lookup: bool
    needs_document_retrieval: bool
    needs_tool_action: bool
    needs_human_approval: bool
    reason: str


def normalise(message: str) -> str:
    """Lowercase, collapse whitespace and drop a trailing question mark.

    Given to you so that matching against TEMPLATED_QUESTIONS is unambiguous.
    """
    text = re.sub(r"\s+", " ", message.strip().lower())
    return text.rstrip("?").strip()


# --------------------------------------------------------------------------- #
# TODO 1 of 2
# --------------------------------------------------------------------------- #

def plan_request(message: str, *, user_owns_account: bool) -> Plan:
    """Decide which capabilities this request needs.

    Rules, in this order:

    1. Reject bad input. A message that is empty or only whitespace raises
       ValueError. A message longer than MAX_MESSAGE_LENGTH characters raises
       ValueError. (This is stage 1 of the pipeline, and it comes first because
       nothing downstream should ever see input you have not checked.)

    2. Authorisation. If the request needs the customer's own records and
       user_owns_account is False, raise PermissionError. Raise it BEFORE
       returning any plan. A request that needs no customer data must still
       succeed when user_owns_account is False, because nothing private is
       involved.

    3. Templated questions short-circuit. If normalise(message) is in
       TEMPLATED_QUESTIONS, the plan is: a data lookup, no retrieval, no tool,
       no approval, and NO model. A written template filled in from the
       database is more accurate, faster and free.

    4. Otherwise:
       - needs_data_lookup is True if any ACCOUNT_PHRASES appears in the
         lowercased message.
       - needs_document_retrieval is True if any POLICY_PHRASES appears.
       - needs_tool_action is True if any ACTION_PHRASES appears.
       - needs_human_approval is True only when there is a tool action AND any
         MONEY_ACTION_PHRASES appears. An approval gate with no action to gate
         is meaningless.
       - needs_llm is True.

    5. reason must be a non-empty human-readable string saying why. You will
       read this in a trace at three in the morning one day; write it for that
       reader, not for the tests.

    Args:
        message: what the customer typed.
        user_owns_account: whether the authenticated caller owns the account
            this request would read. In a real system this comes from a
            verified session, never from the message itself.

    Returns:
        A Plan.

    Raises:
        ValueError: the message is empty, whitespace only, or too long.
        PermissionError: the request needs account data the caller does not own.
    """
    # TODO: implement this function.
    raise NotImplementedError("plan_request is not implemented yet")


# --------------------------------------------------------------------------- #
# TODO 2 of 2
# --------------------------------------------------------------------------- #

def pipeline_stages(plan: Plan) -> list[str]:
    """Turn a Plan into the ordered list of stages that will run.

    Use only the names in STAGE_ORDER, and keep them in that relative order.

    - "validate_input" and "route" always run, in that order, first.
    - "lookup_payment_data" runs when the plan needs a data lookup.
    - "retrieve_documents" runs when the plan needs document retrieval.
    - "request_human_approval" runs when the plan needs human approval, and it
      must come BEFORE "execute_tool". An approval that happens after the action
      is not an approval.
    - "execute_tool" runs when the plan needs a tool action.
    - "assemble_context" and "call_model" run only when the plan needs a model,
      in that order.
    - "validate_output" and "log_trace" always run, in that order, last.

    Returns:
        The stage names, in execution order, with no duplicates.
    """
    # TODO: implement this function.
    raise NotImplementedError("pipeline_stages is not implemented yet")


if __name__ == "__main__":
    # A quick manual check. Once both functions work, this prints a plan and the
    # stages it implies. Compare it against the diagram in lesson.md section 5.3.
    plan = plan_request("Why did my payment fail?", user_owns_account=True)
    print(plan)
    print(" -> ".join(pipeline_stages(plan)))
