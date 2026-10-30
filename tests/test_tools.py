"""Unit tests for the 5 Indian-context mock tools."""

import pytest
from agentguard.tools.environment import MockEnvironmentState
from agentguard.tools.mock_tools import (
    MockToolRegistry,
    book_ticket,
    read_document,
    read_email,
    send_email,
    send_payment,
)


@pytest.fixture
def fresh_env():
    return MockEnvironmentState(seed=42)


def test_send_payment_success(fresh_env):
    sender = "user@okhdfcbank"
    initial_balance = fresh_env.accounts[sender].balance
    res = send_payment(fresh_env, account="kirana_store@upi", amount=500.0, note="Groceries")

    assert res["status"] == "SUCCESS"
    assert res["amount"] == 500.0
    assert fresh_env.accounts[sender].balance == initial_balance - 500.0
    assert fresh_env.accounts["kirana_store@upi"].balance == 8400.0 + 500.0
    assert len(fresh_env.audit_log) == 1
    assert fresh_env.audit_log[0].tool_name == "send_payment"
    assert fresh_env.audit_log[0].success is True


def test_send_payment_insufficient_funds(fresh_env):
    res = send_payment(fresh_env, account="kirana_store@upi", amount=999999.0)
    assert res["status"] == "FAILED"
    assert "Insufficient funds" in res["error"]
    assert len(fresh_env.audit_log) == 1
    assert fresh_env.audit_log[0].success is False


def test_send_payment_invalid_amount(fresh_env):
    res = send_payment(fresh_env, account="kirana_store@upi", amount=-100.0)
    assert res["status"] == "FAILED"
    assert "positive" in res["error"]


def test_read_email(fresh_env):
    res = read_email(fresh_env, id="EML_001")
    assert res["status"] == "SUCCESS"
    assert res["email_id"] == "EML_001"
    assert "bescom" in res["body"].lower()
    assert fresh_env.emails["EML_001"].is_read is True

    # Unknown email
    res_err = read_email(fresh_env, id="NON_EXISTENT")
    assert res_err["status"] == "ERROR"


def test_send_email(fresh_env):
    res = send_email(fresh_env, to="student.desk@college.edu.in", body="Test verification", subject="Inquiry")
    assert res["status"] == "SUCCESS"
    assert len(fresh_env.sent_emails) == 1
    assert fresh_env.sent_emails[0]["to"] == "student.desk@college.edu.in"

    # Invalid recipient
    res_err = send_email(fresh_env, to="invalid_email_format", body="hello")
    assert res_err["status"] == "ERROR"


def test_book_ticket(fresh_env):
    initial_seats = fresh_env.trains["12951"].available_seats
    res = book_ticket(fresh_env, train_id="12951", passenger="Aarav Sharma", date="2026-11-05")
    assert res["status"] == "SUCCESS"
    assert res["passenger"] == "Aarav Sharma"
    assert "pnr" in res
    assert fresh_env.trains["12951"].available_seats == initial_seats - 1

    # Non-existent train
    res_err = book_ticket(fresh_env, train_id="99999", passenger="Aarav Sharma", date="2026-11-05")
    assert res_err["status"] == "ERROR"


def test_read_document(fresh_env):
    res = read_document(fresh_env, doc_id="DOC_SCHOLARSHIP_01")
    assert res["status"] == "SUCCESS"
    assert "scholarships.gov.in" in res["content"]

    res_err = read_document(fresh_env, doc_id="UNKNOWN_DOC")
    assert res_err["status"] == "ERROR"


def test_tool_registry_dispatch(fresh_env):
    res = MockToolRegistry.execute("read_email", {"id": "EML_002"}, fresh_env)
    assert res["status"] == "SUCCESS"
    assert "landlord_verma@icici" in res["body"]

    res_unknown = MockToolRegistry.execute("unknown_tool", {}, fresh_env)
    assert res_unknown["status"] == "ERROR"
