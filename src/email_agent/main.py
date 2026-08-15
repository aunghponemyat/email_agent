from email_agent.classifier import classify_email
from email_agent.db import Database, now_iso
from email_agent.gmail_client import GmailClient
from email_agent.llm_client import get_default_client
from email_agent.models import EmailRecord
from email_agent.configs import Settings, get_settings

settings: Settings = get_settings()

def main():
    max_emails = int(settings.max_emails_per_run)
    
    print("Connecting to Gmail...")
    gmail = GmailClient(
        credentials_path=settings.gmail_credentials_path,
        token_path=settings.gmail_token_path
    )
    
    print("Connecting to LLM (Gemini free tier)...")
    llm = get_default_client()
    
    db = Database()
    
    print(f"Fetching up to {max_emails} uread emails...")
    emails = gmail.fetch_unread(max_results=max_emails)
    print(f"Found {len(emails)} unread emails.")
    
    new_count = 0
    # classification = None
    for email in emails:
        if db.already_processed(email.gmail_id):
            continue
        
        try:
            classification = classify_email(
                llm, sender=email.sender, subject=email.subject, body=email.body
            )
        except KeyboardInterrupt:
            print("Processing cancelled..!")
            break
        except Exception as e:
            print(f"   [ERROR] Failed to classify '{email.subject[:50]}': {e}")
            continue

        record = EmailRecord(
            gmail_id=email.gmail_id,
            sender=email.sender,
            subject=email.subject,
            snippet=email.snippet,
            category=classification.category,
            confidence=classification.confidence,
            reasoning=classification.reasoning,
            model_used="gemini-2.5-flash",
            processed_at=now_iso(),
        )
        db.save(record)
        new_count += 1
        
        flag = "LOW CONFIDENCE" if classification.confidence < 0.6 else ""
        print(f"   [{classification.category.value:12s}] ({classification.confidence:.2f}) {email.subject[:60]}{flag}")

    print(f"\nProcessed {new_count} new emails this run.")
    print("Category breakdown so far:", db.stats())
    db.close()


if __name__ == "__main__":
    main()