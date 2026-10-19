import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from schemas import ProcessedTicket, ActionCategory, PriorityLevel
from tools import create_jira_ticket, process_customer_refund, escalate_to_human_agent

load_dotenv()

llm = ChatOpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_NIM_API_KEY"),
    model="nvidia/nemotron-3-super-120b-a12b",
    temperature=0.0  # Forces deterministic decisions
)

structured_llm = llm.with_structured_output(ProcessedTicket)

prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are an automated Customer Support Intake Router.\n"
        "Analyze incoming raw customer messages and extract structured ticket attributes.\n"
        "Carefully identify category, priority level, customer IDs, and concise summary.\n"
        "If priority is CRITICAL or involves urgent financial refund issues, mark requires_human_escalation as True.\n\n"
        "Categories:\n"
        "- BUG_REPORT: something is broken, crashing, freezing or behaving wrongly.\n"
        "- FEATURE_REQUEST: the user wants something new or an improvement that does not exist yet.\n"
        "- BILLING_ISSUE: charges, refunds, invoices, subscriptions, payments.\n"
        "- GENERAL_INQUIRY: questions or anything that fits none of the above.\n\n"
        "Priority: CRITICAL = money lost, outage or user says critical/urgent; HIGH = core feature broken; "
        "MEDIUM = annoying but has a workaround; LOW = cosmetic, requests or simple questions.\n"
        "Only set customer_id if the message contains one. Never make one up."
    )),
    ("user", "{user_input}")
])

intake_chain = prompt | structured_llm

def route_and_execute_ticket(user_message: str):
    """
    1. Runs user message through the LCEL intake chain to extract structured schema.
    2. Inspects extracted attributes (category, priority, customer_id).
    3. Automatically routes parameters to backend tool functions.
    """
    print(f"\n--- Processing Incoming Message ---\n\"{user_message}\"")
    
    ticket: ProcessedTicket = intake_chain.invoke({"user_input": user_message})
    
    print("\n--- Extracted Pydantic Form Output ---")
    print(f"Category           : {ticket.category.value}")
    print(f"Priority           : {ticket.priority.value}")
    print(f"Summary            : {ticket.summary}")
    print(f"Customer ID        : {ticket.customer_id}")
    print(f"Human Escalation   : {ticket.requires_human_escalation}")

    tool_result = ""
    
    # don't rely on the model alone for escalation
    needs_human = (
        ticket.requires_human_escalation
        or ticket.priority == PriorityLevel.CRITICAL
        or (ticket.category == ActionCategory.BILLING_ISSUE and not ticket.customer_id)
    )

    if needs_human:
        tool_result = escalate_to_human_agent.invoke({
            "summary": ticket.summary,
            "customer_id": ticket.customer_id
        })
    elif ticket.category == ActionCategory.BUG_REPORT:
        tool_result = create_jira_ticket.invoke({
            "summary": ticket.summary,
            "priority": ticket.priority.value
        })
    elif ticket.category == ActionCategory.BILLING_ISSUE:
        tool_result = process_customer_refund.invoke({
            "customer_id": ticket.customer_id
        })
    else:
        tool_result = f"[GENERAL QUEUE] Logging ticket to support queue: '{ticket.summary}'."

    print(f"\n--- Backend Tool Result ---\n{tool_result}\n" + "="*50)
    return ticket, tool_result

if __name__ == "__main__":
    msg1 = "Hey, the payment screen freezes every time I click submit! User ID is CUST_882. Fix this bug immediately!"
    route_and_execute_ticket(msg1)

    msg2 = "CRITICAL: I was charged $500 twice on my account today! Need a refund right now!"
    route_and_execute_ticket(msg2)
    
    msg3 = "CRITICAL: The payment screen freezes every time I click submit! User ID is CUST_882."
    route_and_execute_ticket(msg3)

    msg4 = "The dark mode toggle button on the settings page has a small alignment typo. User ID: CUST_404."
    route_and_execute_ticket(msg4)
    
    msg5 = "Please refund my subscription charge from yesterday for customer CUST_991."
    route_and_execute_ticket(msg5)