"""Tests for exercise 1.1.

Run from the repository root:

    python -m pytest phases/01-foundations/01-complete-map-of-ai-engineering/ -v

These check behaviour, not implementation. Every failure message states the
expected behaviour so that you can work out the fix yourself.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from exercise import (  # noqa: E402
    MAX_MESSAGE_LENGTH,
    STAGE_ORDER,
    TEMPLATED_QUESTIONS,
    Plan,
    pipeline_stages,
    plan_request,
)


# --------------------------------------------------------------------------- #
# Stage 1: input validation happens before anything else
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("bad", ["", "   ", "\n\t "])
def test_empty_message_is_rejected(bad):
    with pytest.raises(ValueError):
        plan_request(bad, user_owns_account=True)


def test_overlong_message_is_rejected():
    too_long = "a" * (MAX_MESSAGE_LENGTH + 1)
    with pytest.raises(ValueError):
        plan_request(too_long, user_owns_account=True)


def test_message_at_the_limit_is_accepted():
    at_limit = "x" * MAX_MESSAGE_LENGTH
    plan = plan_request(at_limit, user_owns_account=True)
    assert isinstance(plan, Plan), "a message exactly at the limit is valid input"


# --------------------------------------------------------------------------- #
# Stage 2: routing
# --------------------------------------------------------------------------- #

def test_own_payment_question_needs_lookup_and_retrieval():
    plan = plan_request("Why did my payment fail?", user_owns_account=True)
    assert plan.needs_data_lookup is True, (
        "'my payment' is a fact about one customer, so it needs a database lookup"
    )
    assert plan.needs_document_retrieval is True, (
        "'why' asks what something means, which lives in documents, so retrieval"
    )
    assert plan.needs_tool_action is False, "the customer asked a question, not for an action"
    assert plan.needs_human_approval is False, "no action means nothing to approve"
    assert plan.needs_llm is True


def test_policy_question_needs_retrieval_only():
    plan = plan_request("What does your refund policy say?", user_owns_account=True)
    assert plan.needs_document_retrieval is True
    assert plan.needs_data_lookup is False, (
        "a policy question is the same for every customer, so no account data is read"
    )
    assert plan.needs_tool_action is False


def test_money_action_needs_approval():
    plan = plan_request("Please refund me for my subscription charge",
                        user_owns_account=True)
    assert plan.needs_tool_action is True
    assert plan.needs_human_approval is True, (
        "a refund moves money, so a human has to approve it"
    )
    assert plan.needs_data_lookup is True, "'my subscription' reads this customer's records"


def test_non_money_action_does_not_need_approval():
    plan = plan_request("Please retry my payment", user_owns_account=True)
    assert plan.needs_tool_action is True
    assert plan.needs_human_approval is False, (
        "a retry of an already-authorised charge does not move new money"
    )


def test_small_talk_needs_nothing_but_the_model():
    plan = plan_request("Hello, are you a real person", user_owns_account=True)
    assert plan.needs_data_lookup is False
    assert plan.needs_document_retrieval is False
    assert plan.needs_tool_action is False
    assert plan.needs_human_approval is False


def test_approval_is_never_set_without_an_action():
    for message in ["Why did my payment fail?", "What does your refund policy say?",
                    "Hello there"]:
        plan = plan_request(message, user_owns_account=True)
        if plan.needs_human_approval:
            assert plan.needs_tool_action, (
                f"{message!r}: approval was requested with no action to approve"
            )


def test_reason_is_a_non_empty_string():
    plan = plan_request("Why did my payment fail?", user_owns_account=True)
    assert isinstance(plan.reason, str) and plan.reason.strip(), (
        "reason is what you will read in a trace later; it must say something"
    )


# --------------------------------------------------------------------------- #
# Rule 3: templated questions need no model
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("question", sorted(TEMPLATED_QUESTIONS))
def test_templated_questions_skip_the_model(question):
    plan = plan_request(question, user_owns_account=True)
    assert plan.needs_llm is False, (
        f"{question!r} is in TEMPLATED_QUESTIONS, so a filled-in template answers it"
    )
    assert plan.needs_data_lookup is True, "the template still needs the customer's data"
    assert plan.needs_document_retrieval is False
    assert plan.needs_tool_action is False
    assert plan.needs_human_approval is False


def test_templated_match_ignores_case_whitespace_and_question_mark():
    plan = plan_request("  What Card Is On File?  ", user_owns_account=True)
    assert plan.needs_llm is False, (
        "normalise() exists so that casing, padding and a trailing '?' do not "
        "stop a templated question from matching"
    )


def test_a_question_outside_the_template_set_does_use_the_model():
    plan = plan_request("what card did I use in March", user_owns_account=True)
    assert plan.needs_llm is True


# --------------------------------------------------------------------------- #
# Rule 2: authorisation, in code, before any plan is returned
# --------------------------------------------------------------------------- #

def test_account_question_without_ownership_raises_permission_error():
    with pytest.raises(PermissionError):
        plan_request("Why did my payment fail?", user_owns_account=False)


def test_templated_question_without_ownership_raises_permission_error():
    with pytest.raises(PermissionError):
        plan_request("when is my next charge", user_owns_account=False)


def test_policy_question_without_ownership_is_allowed():
    plan = plan_request("What does your refund policy say?", user_owns_account=False)
    assert plan.needs_document_retrieval is True, (
        "nothing private is involved, so this must not be blocked"
    )


def test_validation_is_checked_before_authorisation():
    with pytest.raises(ValueError):
        plan_request("", user_owns_account=False)


# --------------------------------------------------------------------------- #
# pipeline_stages
# --------------------------------------------------------------------------- #

def _plan(**kwargs) -> Plan:
    base = dict(
        needs_llm=True,
        needs_data_lookup=False,
        needs_document_retrieval=False,
        needs_tool_action=False,
        needs_human_approval=False,
        reason="test",
    )
    base.update(kwargs)
    return Plan(**base)


def test_stages_always_start_and_end_the_same_way():
    stages = pipeline_stages(_plan())
    assert stages[:2] == ["validate_input", "route"]
    assert stages[-2:] == ["validate_output", "log_trace"]


def test_stages_use_only_known_names_in_order_and_without_duplicates():
    stages = pipeline_stages(_plan(
        needs_data_lookup=True, needs_document_retrieval=True,
        needs_tool_action=True, needs_human_approval=True,
    ))
    assert len(stages) == len(set(stages)), "no stage runs twice"
    for name in stages:
        assert name in STAGE_ORDER, f"{name!r} is not a stage name in STAGE_ORDER"
    positions = [STAGE_ORDER.index(name) for name in stages]
    assert positions == sorted(positions), (
        "stages must appear in the relative order given by STAGE_ORDER"
    )


def test_full_pipeline_for_the_lesson_example():
    plan = plan_request("Why did my payment fail?", user_owns_account=True)
    assert pipeline_stages(plan) == [
        "validate_input",
        "route",
        "lookup_payment_data",
        "retrieve_documents",
        "assemble_context",
        "call_model",
        "validate_output",
        "log_trace",
    ]


def test_templated_question_pipeline_has_no_model_stages():
    plan = plan_request("what card is on file", user_owns_account=True)
    stages = pipeline_stages(plan)
    assert "call_model" not in stages
    assert "assemble_context" not in stages, (
        "there is no context to assemble when no model is called"
    )
    assert stages == [
        "validate_input", "route", "lookup_payment_data",
        "validate_output", "log_trace",
    ]


def test_approval_comes_before_tool_execution():
    stages = pipeline_stages(_plan(needs_tool_action=True, needs_human_approval=True))
    assert "request_human_approval" in stages and "execute_tool" in stages
    assert stages.index("request_human_approval") < stages.index("execute_tool"), (
        "an approval that happens after the action is not an approval"
    )


def test_no_lookup_stage_when_no_lookup_is_needed():
    stages = pipeline_stages(_plan(needs_document_retrieval=True))
    assert "lookup_payment_data" not in stages
    assert "retrieve_documents" in stages


def test_no_approval_stage_when_no_approval_is_needed():
    stages = pipeline_stages(_plan(needs_tool_action=True))
    assert "execute_tool" in stages
    assert "request_human_approval" not in stages
