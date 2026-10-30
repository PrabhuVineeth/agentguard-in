"""Implementation of the 5 Indian-context mock tools for AgentGuard-IN."""

import re
import uuid
from typing import Any, Callable, Dict, List, Optional
from agentguard.tools.base import ToolDefinition, ToolParameter
from agentguard.tools.environment import MockEnvironmentState, MockTrainBooking


def send_payment(
    env: MockEnvironmentState,
    account: str,
    amount: float,
    note: str = "",
    sender_account: str = "user@okhdfcbank",
) -> Dict[str, Any]:
    """Execute a simulated UPI payment between mock accounts."""
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        result = {"status": "FAILED", "error": f"Invalid amount: {amount}"}
        env.record_call("send_payment", {"account": account, "amount": amount, "note": note}, result, False)
        return result

    if amount <= 0:
        result = {"status": "FAILED", "error": "Payment amount must be positive"}
        env.record_call("send_payment", {"account": account, "amount": amount, "note": note}, result, False)
        return result

    if sender_account not in env.accounts:
        result = {"status": "FAILED", "error": f"Sender account '{sender_account}' does not exist"}
        env.record_call("send_payment", {"account": account, "amount": amount, "note": note}, result, False)
        return result

    sender = env.accounts[sender_account]
    if sender.balance < amount:
        result = {
            "status": "FAILED",
            "error": f"Insufficient funds: available {sender.balance}, requested {amount}",
        }
        env.record_call("send_payment", {"account": account, "amount": amount, "note": note}, result, False)
        return result

    # If recipient account doesn't exist yet in mock state, register it to track transfers
    if account not in env.accounts:
        from agentguard.tools.environment import MockAccount
        env.accounts[account] = MockAccount(account_id=account, owner_name="External Payee", balance=0.0)

    recipient = env.accounts[account]
    tx_id = f"UPI{env.step_counter + 1:06d}{len(env.audit_log):02d}"

    # Deduct and credit
    sender.balance -= amount
    recipient.balance += amount

    tx_record = {
        "tx_id": tx_id,
        "from": sender_account,
        "to": account,
        "amount": amount,
        "note": note,
    }
    sender.transactions.append(tx_record)
    recipient.transactions.append(tx_record)

    result = {
        "status": "SUCCESS",
        "tx_id": tx_id,
        "amount": amount,
        "recipient": account,
        "sender_remaining_balance": sender.balance,
        "note": note,
    }
    env.record_call("send_payment", {"account": account, "amount": amount, "note": note}, result, True)
    return result


def read_email(env: MockEnvironmentState, id: str) -> Dict[str, Any]:
    """Read an email from the simulated inbox by ID."""
    if id not in env.emails:
        result = {"status": "ERROR", "error": f"Email with ID '{id}' not found"}
        env.record_call("read_email", {"id": id}, result, False)
        return result

    email = env.emails[id]
    email.is_read = True
    result = {
        "status": "SUCCESS",
        "email_id": email.email_id,
        "sender": email.sender,
        "recipient": email.recipient,
        "subject": email.subject,
        "body": email.body,
        "date": email.date,
    }
    env.record_call("read_email", {"id": id}, result, True)
    return result


def send_email(env: MockEnvironmentState, to: str, body: str, subject: str = "Assistant Follow-up") -> Dict[str, Any]:
    """Send an email to a recipient and record in the mock sent box."""
    if not to or "@" not in to:
        result = {"status": "ERROR", "error": f"Invalid recipient email: '{to}'"}
        env.record_call("send_email", {"to": to, "body": body, "subject": subject}, result, False)
        return result

    msg_id = f"SENT_{len(env.sent_emails) + 1:04d}"
    record = {
        "message_id": msg_id,
        "to": to,
        "subject": subject,
        "body": body,
        "timestamp_step": env.step_counter + 1,
    }
    env.sent_emails.append(record)

    result = {
        "status": "SUCCESS",
        "message_id": msg_id,
        "to": to,
        "subject": subject,
    }
    env.record_call("send_email", {"to": to, "body": body, "subject": subject}, result, True)
    return result


def book_ticket(
    env: MockEnvironmentState,
    train_id: str,
    passenger: str,
    date: str,
) -> Dict[str, Any]:
    """Book a simulated railway ticket on IRCTC-style inventory."""
    if train_id not in env.trains:
        result = {"status": "ERROR", "error": f"Train number '{train_id}' not found in IRCTC schedule"}
        env.record_call("book_ticket", {"train_id": train_id, "passenger": passenger, "date": date}, result, False)
        return result

    train = env.trains[train_id]
    if train.available_seats <= 0:
        result = {"status": "FAILED", "error": f"No berths available on train {train_id} for date {date}"}
        env.record_call("book_ticket", {"train_id": train_id, "passenger": passenger, "date": date}, result, False)
        return result

    pnr = f"PNR{train_id[-3:]}{len(train.bookings) + 101:04d}"
    booking = MockTrainBooking(
        pnr=pnr,
        train_id=train_id,
        train_name=train.train_name,
        passenger_name=passenger,
        date=date,
        status="CONFIRMED",
    )
    train.bookings.append(booking)
    train.available_seats -= 1

    result = {
        "status": "SUCCESS",
        "pnr": pnr,
        "train_id": train_id,
        "train_name": train.train_name,
        "passenger": passenger,
        "date": date,
        "fare": train.fare,
        "remaining_seats": train.available_seats,
    }
    env.record_call("book_ticket", {"train_id": train_id, "passenger": passenger, "date": date}, result, True)
    return result


def read_document(env: MockEnvironmentState, doc_id: str) -> Dict[str, Any]:
    """Read a simulated government portal guideline, citizen document, or invoice."""
    if doc_id not in env.documents:
        result = {"status": "ERROR", "error": f"Document with ID '{doc_id}' not found in registry"}
        env.record_call("read_document", {"doc_id": doc_id}, result, False)
        return result

    doc = env.documents[doc_id]
    result = {
        "status": "SUCCESS",
        "doc_id": doc.doc_id,
        "title": doc.title,
        "doc_type": doc.doc_type,
        "content": doc.content,
        "metadata": doc.metadata,
    }
    env.record_call("read_document", {"doc_id": doc_id}, result, True)
    return result


class MockToolRegistry:
    """Registry providing tool metadata and safe invocation dispatch."""

    DEFINITIONS: Dict[str, ToolDefinition] = {
        "send_payment": ToolDefinition(
            name="send_payment",
            description="Send an Indian UPI payment to a verified VPA/UPI ID (e.g., vendor@okaxis) with amount in INR and note.",
            parameters=[
                ToolParameter(name="account", type="string", description="Recipient UPI VPA address (e.g. landlord@icici)"),
                ToolParameter(name="amount", type="number", description="Payment amount in INR (positive number)"),
                ToolParameter(name="note", type="string", description="Transaction description/note", required=False),
            ],
        ),
        "read_email": ToolDefinition(
            name="read_email",
            description="Fetch and read the content of an email from the inbox using its email ID (e.g., EML_001).",
            parameters=[
                ToolParameter(name="id", type="string", description="The identifier of the email to read (e.g. EML_001)"),
            ],
        ),
        "send_email": ToolDefinition(
            name="send_email",
            description="Compose and dispatch an email to a specified email address.",
            parameters=[
                ToolParameter(name="to", type="string", description="Recipient email address"),
                ToolParameter(name="body", type="string", description="Content/body of the email message"),
                ToolParameter(name="subject", type="string", description="Subject line of the email", required=False),
            ],
        ),
        "book_ticket": ToolDefinition(
            name="book_ticket",
            description="Book an Indian Railways (IRCTC) train ticket using train number, passenger name, and travel date.",
            parameters=[
                ToolParameter(name="train_id", type="string", description="5-digit train number (e.g., 12951)"),
                ToolParameter(name="passenger", type="string", description="Full name of the passenger"),
                ToolParameter(name="date", type="string", description="Date of journey in YYYY-MM-DD format"),
            ],
        ),
        "read_document": ToolDefinition(
            name="read_document",
            description="Read a document from the official citizen welfare/utility portal using document ID.",
            parameters=[
                ToolParameter(name="doc_id", type="string", description="Document identifier (e.g. DOC_SCHOLARSHIP_01)"),
            ],
        ),
    }

    _HANDLERS: Dict[str, Callable] = {
        "send_payment": send_payment,
        "read_email": read_email,
        "send_email": send_email,
        "book_ticket": book_ticket,
        "read_document": read_document,
    }

    @classmethod
    def get_definitions(cls, tools_allowed: Optional[List[str]] = None) -> List[ToolDefinition]:
        if tools_allowed is None:
            return list(cls.DEFINITIONS.values())
        return [cls.DEFINITIONS[t] for t in tools_allowed if t in cls.DEFINITIONS]

    @classmethod
    def get_openai_tools(cls, tools_allowed: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        return [t.to_openai_schema() for t in cls.get_definitions(tools_allowed)]

    @classmethod
    def execute(cls, tool_name: str, args: Dict[str, Any], env: MockEnvironmentState) -> Dict[str, Any]:
        if tool_name not in cls._HANDLERS:
            err = {"status": "ERROR", "error": f"Unknown tool '{tool_name}'"}
            env.record_call(tool_name, args, err, False)
            return err
        return cls._HANDLERS[tool_name](env=env, **args)
