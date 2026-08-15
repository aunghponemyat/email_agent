from email_agent.llm_client import LLMClient
from email_agent.models import Classification

CLASSIFY_SYSTEM_PROMPT = """You are triaging an email inbox for a busy professional.
Classify each email into exactly one category:

- needs_reply: requires a personal, substantive response from the user
- fyi: informational only, no action or reply needed
- newsletter: bulk/marketing/subscription content
- action_item: requires the user to DO something (not just reply) — e.g. sign a form, pay an invoice, review a document
- spam: irrelevant or unwanted

Also return a confidence score from 0.0 to 1.0 (how sure you are) and a
one-sentence reasoning for your own auditing purposes. Be honest about low
confidence rather than guessing — items below 0.6 confidence should be
flagged for human review, not acted on."""

CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "enum": ["needs_reply", "fyi", "newsletter", "action_item", "spam"],
        },
        "confidence": {"type": "number"},
        "reasoning": {"type": "string"},
    },
    "required": ["category", "confidence", "reasoning"],
}


def classify_email(llm_client: LLMClient, sender: str, subject: str, body: str) -> Classification:
    user_prompt = f"From: {sender}\nSubject: {subject}\nBody:\n{body[:2000]}"
    result = llm_client.structured_call(
        CLASSIFY_SYSTEM_PROMPT, user_prompt, CLASSIFICATION_SCHEMA
    )
    return Classification(**result)
