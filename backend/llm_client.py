"""Groq-based LLM client for intent parsing and advisory formatting."""
import os
import json
import re
import time
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq, RateLimitError, APIError

load_dotenv(Path(__file__).parent / ".env")
MODEL = "llama-3.3-70b-versatile"
_MAX_RETRIES = 3
_INITIAL_BACKOFF = 1.0

DISTRICTS = [
    "Angul","Balangir","Balasore","Bargarh","Bhadrak","Boudh","Cuttack","Deogarh",
    "Dhenkanal","Gajapati","Ganjam","Jagatsinghpur","Jajpur","Jharsuguda","Kalahandi",
    "Kandhamal","Kendrapara","Keonjhar","Khurda","Koraput","Malkangiri","Mayurbhanj",
    "Nabarangpur","Nayagarh","Nuapada","Puri","Rayagada","Sambalpur","Sonepur","Sundargarh"
]

QUERY_TYPES = ["yield_forecast", "failure_risk", "temporal_analysis", "what_if", "full_diagnosis"]

_client = None

def _get_client() -> Groq:
    global _client
    if _client is None:
        key = os.environ.get("GROQ_API_KEY", "").strip().strip("\"'")
        _client = Groq(api_key=key)
    return _client

def _call(system: str, user: str, temperature: float = 0.1, max_tokens: int = 512) -> str:
    last_exc = None
    for attempt in range(_MAX_RETRIES):
        try:
            resp = _get_client().chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content.strip()
        except (RateLimitError, APIError) as e:
            last_exc = e
            if attempt < _MAX_RETRIES - 1:
                wait = _INITIAL_BACKOFF * (2 ** attempt)
                time.sleep(wait)
        except Exception as e:
            last_exc = e
            break
    return ""

def parse_intent(user_text: str) -> dict:
    """Parse user query into structured routing parameters."""
    system = f"""You are a query parser for a crop advisory system. Extract structured fields from the user's query.

Available districts: {', '.join(DISTRICTS)}
Seasons: Kharif (monsoon, Jun-Sep), Rabi (winter, Nov-Jan)
Valid query_type values (choose EXACTLY one):
- "yield_forecast" — user asks about yield amount, production, harvest quantity
- "failure_risk" — user asks about crop failure, risk, flood, drought, stress, danger
- "temporal_analysis" — user asks about weather patterns, trends, timing, weekly analysis
- "what_if" — user asks about scenarios, simulations, "what if", hypothetical changes
- "full_diagnosis" — comprehensive analysis or unclear intent

Respond ONLY with valid JSON (no markdown, no extra text, no explanation):
{{"district": "DistrictName" or null, "season": "Kharif" or "Rabi" or null, "year": 2024 or null, "query_type": "failure_risk"}}
Use null for any field not mentioned. If the query mentions a year, use it; otherwise null."""

    # Also do simple keyword matching as fallback
    raw = _call(system, user_text, temperature=0.1, max_tokens=256)
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, KeyError):
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            try:
                parsed = json.loads(m.group())
            except json.JSONDecodeError:
                parsed = {"district": None, "season": None, "year": None, "query_type": "full_diagnosis"}
        else:
            parsed = {"district": None, "season": None, "year": None, "query_type": "full_diagnosis"}

    if parsed.get("district"):
        matches = [d for d in DISTRICTS if d.lower() == parsed["district"].lower()]
        parsed["district"] = matches[0] if matches else None
    if parsed.get("query_type") not in QUERY_TYPES:
        # Keyword fallback
        text_lower = user_text.lower()
        if any(w in text_lower for w in ["flood", "drought", "fail", "risk", "stress", "danger"]):
            parsed["query_type"] = "failure_risk"
        elif any(w in text_lower for w in ["yield", "forecast", "harvest", "production", "how much"]):
            parsed["query_type"] = "yield_forecast"
        elif any(w in text_lower for w in ["trend", "pattern", "week", "temporal", "timing"]):
            parsed["query_type"] = "temporal_analysis"
        elif any(w in text_lower for w in ["what if", "simulate", "scenario", "change"]):
            parsed["query_type"] = "what_if"
        else:
            parsed["query_type"] = "full_diagnosis"
    return parsed

def format_advisory(structured: dict) -> str:
    """Format structured model output into plain-language advisory."""
    lines = []
    if structured.get("district") and structured.get("season") and structured.get("year"):
        lines.append(f"District: {structured['district']}, Season: {structured['season']}, Year: {structured['year']}")
    if structured.get("predicted_yield") is not None:
        lines.append(f"Predicted Yield: {structured['predicted_yield']} Q/Acre")
    if structured.get("failure_probability") is not None:
        lines.append(f"Failure Risk: {structured['failure_probability']:.0%}")
    if structured.get("active_triggers"):
        lines.append(f"Active Triggers: {', '.join(structured['active_triggers'])}")
    if structured.get("yield_source"):
        lines.append(f"Yield Source: {structured['yield_source']}")

    prompt = "\n".join(lines) if lines else json.dumps(structured, indent=2)

    system = """You are an agricultural advisory assistant for Odisha rice farmers. Given structured model output, write 2-3 concise sentences explaining the prediction and actionable advice.

Rules:
- Use plain English, no technical jargon
- Mention the specific district, season, and year
- If triggers are present (Drought, Flooding, Thermal Sterility, Pest Risk), explain when and why
- Suggest 1 practical action if risk is high
- Keep it under 4 sentences total
- Do NOT mention model names, probabilities, or technical metrics

Output only the advisory text, no preamble."""

    return _call(system, prompt, temperature=0.3, max_tokens=512)
