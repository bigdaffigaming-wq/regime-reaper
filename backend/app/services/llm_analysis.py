import json
from typing import Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Groq is primary — free, fast, excellent JSON output
# OpenAI is fallback if Groq key not set
try:
    from groq import AsyncGroq
    _groq = AsyncGroq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None
except ImportError:
    _groq = None

SYSTEM_PROMPT = """You are REGIME REAPER, an asset acquisition intelligence system.
You analyze vehicle listings for profitability. Respond with JSON only — no markdown, no explanation.
You cannot override hard rejection rules. Be direct, objective, profit-focused. Keep all text concise.
IMPORTANT: The rule engine already computed profit, score, repair cost, and title status. Do NOT repeat those in red_flags or green_flags. Only add qualitative observations the rule engine cannot detect — e.g. seller behavior, description red flags, market demand, hidden issues, negotiation leverage."""

ANALYSIS_SCHEMA = {
    "summary": "2-3 sentence deal assessment",
    "risk_notes": ["key risk factors"],
    "red_flags": ["specific problems found in description — not price/score/title"],
    "green_flags": ["qualitative positives from description — not price/score/title"],
    "inspection_questions": ["questions to ask at inspection based on description"],
    "negotiation_message": "opening text message to send seller",
    "recommended_strategy": "BUY / NEGOTIATE / MONITOR / SKIP and why",
    "description_intel": {
        "engine": "engine info if mentioned, else null",
        "modifications": ["list of mods/upgrades mentioned"],
        "issues_mentioned": ["any problems the seller admitted — leaks, noises, damage, etc."],
        "seller_signals": "private/broker/motivated/suspicious — note ATOBAN, dealers, 3rd parties",
        "key_facts": ["other important facts from description not captured elsewhere"]
    }
}


async def run_llm_analysis(
    listing_data: dict,
    deal_score: float,
    verdict: str,
    repair_estimate: float,
    expected_profit: float,
    red_flags: list,
    green_flags: list,
) -> Optional[dict]:

    prompt = f"""Analyze this vehicle listing for a vehicle flipper:

Title: {listing_data.get('title')}
Year/Make/Model: {listing_data.get('year')} {listing_data.get('make')} {listing_data.get('model')}
Price: ${listing_data.get('price')}
Mileage: {listing_data.get('mileage')}
Location: {listing_data.get('location')}
Title Status: {listing_data.get('title_status', 'clean')}
Description: {listing_data.get('description', 'N/A')}

Rule Engine Results:
Score: {deal_score}/100 | Verdict: {verdict}
Est. Repairs: ${repair_estimate} | Expected Profit: ${expected_profit}
Red Flags: {red_flags}
Green Flags: {green_flags}

Return JSON matching exactly:
{json.dumps(ANALYSIS_SCHEMA, indent=2)}"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    # Try Groq first
    if _groq:
        try:
            response = await _groq.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=800,
            )
            result = json.loads(response.choices[0].message.content)
            logger.info("LLM analysis completed via Groq")
            return result
        except Exception as e:
            logger.warning(f"Groq failed, trying fallback: {e}")

    logger.warning("Groq unavailable — skipping LLM analysis")
    return None
