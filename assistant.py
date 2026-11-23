"""FitDesk enquiry assistant: core logic."""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

ESCALATION = "I'll check with the owner and come back to you."
DATA_PATH = Path(__file__).parent / "data" / "studio_data.json"
LOG_PATH = Path(__file__).parent / "status_log.json"
MODEL_NAME = "gemini-3.5-flash-lite"
TIMEOUT_MS = 60000

PROMPT = """You classify customer enquiries for a fitness studio.
Return JSON only, with these fields:
- intent: one of "price", "availability", "both", "other"
- details: one short sentence summarising what the customer asked
- requires_human_approval: always true
- packages: the packages the customer asks about, using "single", "5" or "12".
  For any other package size, use the number as text, for example "20".
  Use an empty list if no package is named.
- asks_saturday: true if the customer asks about Saturday availability
Do not answer the question. Do not include any prices or availability.

Customer message: """


class AIUnavailableError(Exception):
    """Gemini failed or timed out."""


class InvalidAIOutputError(Exception):
    """Gemini returned something that does not match the model."""


class EnquiryResult(BaseModel):
    intent: str
    details: str
    requires_human_approval: bool
    packages: List[str]
    asks_saturday: bool


def call_gemini(message: str) -> str:
    """Send the message to Gemini and return the raw JSON text."""
    from google import genai
    from google.genai import types

    load_dotenv()
    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY"),
        http_options=types.HttpOptions(timeout=TIMEOUT_MS),
    )
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", MODEL_NAME),
        contents=PROMPT + message,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=EnquiryResult,
        ),
    )
    return response.text


def classify_message(message: str, call_model=call_gemini) -> EnquiryResult:
    """Get structured JSON from the AI and validate it."""
    try:
        raw = call_model(message)
    except Exception as exc:
        raise AIUnavailableError(str(exc)) from exc
    if not raw:
        raise InvalidAIOutputError("empty response")
    try:
        return EnquiryResult.model_validate_json(raw)
    except ValidationError as exc:
        raise InvalidAIOutputError(str(exc)) from exc


def load_data(path=DATA_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_reply(result: EnquiryResult, data: dict) -> str:
    """Draft a reply using ONLY facts from the data file."""
    lines = []
    missing = False
    wants_slots = result.asks_saturday or result.intent in ("availability", "both")
    wants_price = bool(result.packages) or result.intent in ("price", "both")

    if wants_price:
        if result.packages:
            for key in result.packages:
                pkg = data["packages"].get(key.strip().lower())
                if pkg:
                    lines.append(f"{pkg['label']}: R{pkg['price']:,}")
                else:
                    missing = True
        else:
            for pkg in data["packages"].values():
                lines.append(f"{pkg['label']}: R{pkg['price']:,}")

    if wants_slots:
        slots = ", ".join(
            f"{time} ({status})" for time, status in data["saturday_slots"].items()
        )
        lines.append(f"Saturday slots: {slots}")

    if not lines:
        return ESCALATION
    if missing:
        lines.append(ESCALATION)
    return "\n".join(lines)


def ask_approval(prompt_fn=input) -> bool:
    """Ask staff until they type y or n. Never default to y."""
    while True:
        answer = prompt_fn("Send? (y/n): ").strip().lower()
        if answer in ("y", "n"):
            return answer == "y"
        print("Please type y or n.")


def log_status(status, message, draft, log_path=LOG_PATH):
    path = Path(log_path)
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        entries = []
    entries.append(
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "message": message,
            "draft": draft,
            "status": status,
        }
    )
    path.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def process_enquiry(message, data, call_model=call_gemini,
                    approve=ask_approval, log_path=LOG_PATH):
    """Run one enquiry end to end. Returns (status, draft)."""
    try:
        result = classify_message(message, call_model)
    except AIUnavailableError:
        print("The AI service is unavailable. No draft was made.")
        log_status("error_ai_unavailable", message, "", log_path)
        return "error_ai_unavailable", ""
    except InvalidAIOutputError:
        print("The AI returned invalid output. No draft was made.")
        log_status("error_invalid_ai_output", message, "", log_path)
        return "error_invalid_ai_output", ""

    draft = build_reply(result, data)
    print("\nDraft reply:\n" + draft + "\n")
    status = "sent" if approve() else "rejected"
    log_status(status, message, draft, log_path)
    return status, draft