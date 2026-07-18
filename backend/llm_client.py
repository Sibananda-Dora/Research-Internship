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
        if not key:
            print("WARNING: GROQ_API_KEY not set — LLM features will be disabled (keyword fallback only)")
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

def _translate_attention_to_weeks(attention_weights):
    if not attention_weights:
        return ""
    aw = attention_weights
    if len(aw) == 84:
        weeks = {}
        for d, val in enumerate(aw):
            wk = d // 7
            weeks[wk] = weeks.get(wk, 0) + val
        ranked = sorted(weeks.items(), key=lambda x: x[1], reverse=True)
        top = [f"W{w+1}" for w, _ in ranked[:4]]
        return f"The model focused most on {' → '.join(top)}, suggesting these growth stages are critical."
    return ""

def _telemetry_summary(telemetry):
    if not telemetry:
        return ""
    parts = []
    if "T2M" in telemetry:
        t = telemetry["T2M"]
        parts.append(f"Temperature: {t[0]:.1f}°C (early) → {max(t):.1f}°C (peak) → {t[-1]:.1f}°C (late)")
    if "PRECTOTCORR" in telemetry:
        p = telemetry["PRECTOTCORR"]
        total = sum(p)
        wet_weeks = sum(1 for v in p if v > 50)
        parts.append(f"Total rainfall: {total:.0f}mm over the season")
        if wet_weeks:
            parts.append(f"{wet_weeks} heavy-rain weeks (exceeding 50mm)")
    if "RH2M" in telemetry:
        h = telemetry["RH2M"]
        avg_h = sum(h) / len(h)
        parts.append(f"Average humidity: {avg_h:.0f}%")
    return " | ".join(parts)

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
{{"district": "DistrictName" or null, "season": "Kharif" or "Rabi" or null, "year": [year number] or null, "query_type": "failure_risk"}}
If the query mentions a specific year, use that year number directly. Otherwise null."""

    raw = _call(system, user_text, temperature=0.1, max_tokens=256)

    # Parse JSON from LLM response
    parsed = None
    if raw:
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, KeyError):
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                try:
                    parsed = json.loads(m.group())
                except json.JSONDecodeError:
                    pass

    if not parsed:
        parsed = {"district": None, "season": None, "year": None, "query_type": "full_diagnosis"}

    # Normalize district name
    if parsed.get("district"):
        matches = [d for d in DISTRICTS if d.lower() == parsed["district"].lower()]
        parsed["district"] = matches[0] if matches else None

    # Ensure valid query_type
    if parsed.get("query_type") not in QUERY_TYPES:
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

def format_advisory(structured: dict, attention_weights: list = None, telemetry: dict = None) -> str:
    """Format structured model output into plain-language advisory.
    
    Args:
        structured: Prediction result dict with district/season/year/yield/probability/triggers
        attention_weights: LSTM attention weights (84 daily values) for temporal context
        telemetry: Weekly telemetry dict with T2M/PRECTOTCORR/RH2M/GWETROOT lists
    """
    lines = []
    if structured.get("district") and structured.get("season") and structured.get("year"):
        lines.append(f"District: {structured['district']}, Season: {structured['season']}, Year: {structured['year']}")
    if structured.get("predicted_yield") is not None:
        lines.append(f"Predicted Yield: {structured['predicted_yield']} Q/Acre")
    if structured.get("failure_probability") is not None:
        lines.append(f"Failure Risk: {structured['failure_probability']:.0%}")
    if structured.get("active_triggers"):
        lines.append(f"Active Triggers: {', '.join(structured['active_triggers'])}")

    # Add temporal attention context
    attn_text = _translate_attention_to_weeks(attention_weights)
    if attn_text:
        lines.append(f"Temporal Focus: {attn_text}")

    # Add telemetry context
    telemetry_text = _telemetry_summary(telemetry)
    if telemetry_text:
        lines.append(f"Weather Summary: {telemetry_text}")

    prompt = "\n".join(lines) if lines else json.dumps(structured, indent=2)

    system = """You are an agricultural advisory assistant for Odisha rice farmers. Given structured model output, write 2-3 concise sentences explaining the prediction and actionable advice.

Rules:
- Use plain English, no technical jargon
- Mention the specific district, season, and year
- If triggers are present (Drought, Flooding, Thermal Sterility, Pest Risk), explain when and why, grounding it in the actual weather data provided
- Reference the temporal focus if given (e.g., "The model suggests the reproductive phase in Weeks 7-9 is most critical")
- Suggest 1 practical action if risk is high
- Keep it under 4 sentences total
- Do NOT mention model names, probabilities, or technical metrics

Output only the advisory text, no preamble."""

    advisory = _call(system, prompt, temperature=0.3, max_tokens=512)

    # Fallback if Groq is unavailable
    if not advisory:
        fallback = []
        d = structured.get("district", "the district")
        s = structured.get("season", "season")
        y = structured.get("year", "")
        yld = structured.get("predicted_yield")
        fail = structured.get("failure_probability", 0)
        triggers = structured.get("active_triggers", [])

        if yld is not None:
            fallback.append(f"In {d} for {s} {y}, the predicted yield is {yld} Q/Acre.")
        if triggers:
            fallback.append(f"Alerts: {', '.join(triggers)}. {'Consider taking preventive action.' if fail and fail > 0.5 else 'Monitor conditions closely.'}")
        elif fail and fail > 0.5:
            fallback.append(f"Risk of crop failure is elevated for {d}. Consider reviewing irrigation and pest management.")
        else:
            fallback.append(f"Conditions look favorable for {d} {s} {y}. Continue standard management practices.")
        advisory = " ".join(fallback)

    return advisory
