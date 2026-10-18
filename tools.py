from langchain_core.tools import tool
from typing import Optional

@tool
def create_jira_ticket(summary: str, priority: str) -> str:
    """
    Creates a new technical ticket in JIRA for software bugs and system issues.
    """
    return f"[MOCK JIRA API] Created Issue Ticket successfully -> Summary: '{summary}' | Priority: {priority}"

@tool
def process_customer_refund(customer_id: str) -> str:
    """
    Triggers an automated financial refund workflow for a specific customer ID.
    """
    if not customer_id:
        return "[MOCK BILLING API] Failed: Customer ID is required to process refunds."
    
    return f"[MOCK BILLING API] Refund request initiated for Customer ID: {customer_id}."

@tool
def escalate_to_human_agent(summary: str, customer_id: Optional[str] = None) -> str:
    """
    Routes critical or unresolved issues directly to a human support manager's queue.
    """
    cid = customer_id if customer_id else "UNKNOWN_USER"
    return f"[MOCK SUPPORT QUEUE] Escalated to senior support agent -> User: {cid} | Issue: '{summary}'"