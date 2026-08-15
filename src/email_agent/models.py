from pydantic import BaseModel, Field
from enum import Enum

class Category(str, Enum):
    NEEDS_REPLY = "needs_reply"
    FYI = "fyi"
    NEWSLETTER = "newsletter"
    ACTION_ITEM = "action_item"
    SPAM = "spam"
    
class Classification(BaseModel):
    category: Category
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    
class EmailRecord(BaseModel):
    gmail_id: str
    sender: str
    subject: str
    snippet: str
    category: Category
    confidence: float
    reasoning: str
    model_used: str
    processed_at: str