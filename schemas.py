from enum import Enum
from typing import List , Optional
from pydantic import BaseModel , Field

class PriorityLevel(str,Enum):
    LOW = "LOW",
    MEDIUM ="MEDIUM",
    HIGH = "HIGH",
    CRITICAL = "CRITICAL"
    
class ActionCategory(str,Enum):
    BUG_REPORT = "BUG_REPORT"
    FEATURE_REQUEST = "FEATURE_REQUEST"
    BILLING_ISSUE = "BILLING_ISSUE"
    GENERAL_INQUIRY = "GENERAL_INQUIRY"
    
class ProcessedTicket(BaseModel):
    category: ActionCategory = Field(
        description="The primary intent category extracted from the message."
    )
    priority: PriorityLevel = Field(
        description="Assessed priority level based on user urgency or severity."
    )
    summary: str = Field(
        description="A 1-sentence concise summary of the issue."
    )
    customer_id: Optional[str] = Field(
        default=None,
        description="Extracted customer ID if mentioned (e.g., CUST_102), otherwise None."
    )
    requires_human_escalation: bool = Field(
        description="True if priority is CRITICAL or requires manual intervention, else False."
    )