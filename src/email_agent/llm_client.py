import json
import re
import time
from abc import ABC, abstractmethod

from google import genai
from google.genai import errors, types
from email_agent.configs import Settings, get_settings

settings: Settings = get_settings()

class LLMClient(ABC):
    @abstractmethod
    def structured_call(self, system_prompt: str, user_prompt: str, schema: dict) -> dict:
        """Send a prompt, get back a dict that matches the given JSON schema."""
        ...


class GeminiClient(LLMClient):
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        min_interval_seconds: float = 13.0,
        max_retries: int = 4,
    ):
        api_key = settings.gemini_api_key
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not set. Get a free key at "
                "https://aistudio.google.com/app/apikey and put it in .env"
            )
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.min_interval_seconds = min_interval_seconds
        self.max_retries = max_retries
        self._last_call_at: float | None = None

    def _pace(self) -> None:
        """Sleep just enough to respect min_interval_seconds between calls."""
        if self._last_call_at is not None:
            elapsed = time.monotonic() - self._last_call_at
            remaining = self.min_interval_seconds - elapsed
            if remaining > 0:
                time.sleep(remaining)
        self._last_call_at = time.monotonic()

    def structured_call(self, system_prompt: str, user_prompt: str, schema: dict) -> dict:
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            self._pace()
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        response_schema=schema,
                        temperature=0.2,
                    ),
                )
                return json.loads(str(response.text))

            except errors.APIError as e:
                last_error = e
                if getattr(e, "code", None) != 429:
                    raise  # not a rate-limit error — don't retry, surface it

                if attempt == self.max_retries:
                    break  # out of retries, fall through to raise below

                delay = self._extract_retry_delay(e) or (2 ** attempt)
                print(
                    f"    [rate limited] retrying in {delay:.1f}s "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                time.sleep(delay)

        raise last_error # type: ignore

    @staticmethod
    def _extract_retry_delay(error: Exception) -> float | None:
        """Pull the server-suggested retry delay out of a 429 error, if present."""
        match = re.search(r"retryDelay['\"]?:\s*['\"]?(\d+(?:\.\d+)?)s", str(error))
        if match:
            return float(match.group(1))
        return None

def get_default_client() -> LLMClient:
    """Single place to control which model backs the whole app."""
    return GeminiClient()