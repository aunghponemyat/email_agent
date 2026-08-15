import base64
import os
from dataclasses import dataclass
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

@dataclass
class EmailMessage:
    gmail_id: str
    sender: str
    subject: str
    snippet: str
    body: str
    
class GmailClient:
    def __init__(self, credentials_path: str, token_path: str):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = self._authenticate()
        
    def _authenticate(self):
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Missing {self.credentials_path}. Download it from "
                        "Google Cloud Console > APIs & Services > Credentials "
                        "(see README for the full setup)."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0, open_browser=False)
            with open(self.token_path, "w") as f:
                f.write(creds.to_json()) 
        return build("gmail", "v1", credentials=creds)
    
    def fetch_unread(self, max_results: int = 10) -> list[EmailMessage]:
        results = (
            self.service.users()
            .messages()
            .list(userId="me", labelIds=["UNREAD"], maxResults=max_results)
            .execute()
        )
        message_stubs = results.get("messages", [])
        print(results)
        
        emails = []
        for stub in message_stubs:
            msg = (
                self.service.users()
                .messages()
                .get(userId="me", id=stub["id"], format="full")
                .execute()
            )
            emails.append(self._parse_message(msg))
        return emails
    
    def _parse_message(self, msg: dict) -> EmailMessage:
        headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
        body = self._extract_body(msg["payload"])
        return EmailMessage(
            gmail_id=msg["id"],
            sender=headers.get("From", "unknown"),
            subject=headers.get("Subject", "(no subject)"),
            snippet=msg.get("snippet", ""),
            body=body,
        )

    def _extract_body(self, payload: dict) -> str:
        if payload.get("mimeType") == "text/plain" and "data" in payload.get("body", {}):
            return self._decode(payload["body"]["data"])

        for part in payload.get("parts", []):
            body = self._extract_body(part)
            if body:
                return body
        return ""

    @staticmethod
    def _decode(data: str) -> str:
        return base64.urlsafe_b64decode(data.encode("ASCII")).decode("utf-8", errors="replace")