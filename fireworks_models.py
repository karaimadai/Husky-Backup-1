"""
fireworks_models.py — Single source of truth for ALL Fireworks model IDs.

Both app.py and script_generator.py import from here.
Model list is fetched live from the Fireworks API at startup so it never
goes stale. Falls back to a curated list if the API call fails.
"""

import os
import requests

# ── Verified fallback LLM models ──────────────────────────────────────────────
# These are confirmed serverless as of May 2026.
# The live fetch below will replace this list if the API responds.
_FALLBACK_LLM_MODELS = [
    "accounts/fireworks/models/llama4-maverick-instruct-basic",  # Llama 4 Maverick — best quality
    "accounts/fireworks/models/llama4-scout-instruct-basic",     # Llama 4 Scout — faster
    "accounts/fireworks/models/llama-v3p1-8b-instruct",         # Llama 3.1 8B — cheapest
]

# ── Image models (these don't change often) ───────────────────────────────────
SERVERLESS_IMAGE_MODELS = [
    "flux-1-schnell-fp8",               # fastest & cheapest
    "flux-1-dev-fp8",                   # higher quality ~2× cost
    "stable-diffusion-xl-1024-v1-0",    # SDXL fallback (supports negative prompts)
]
DEFAULT_IMAGE_MODEL = SERVERLESS_IMAGE_MODELS[0]

# ── Cost estimates (USD per image) ────────────────────────────────────────────
IMAGE_COST_PER_PANEL = {
    "flux-1-schnell-fp8":            0.0002,
    "flux-1-dev-fp8":                0.0009,
    "stable-diffusion-xl-1024-v1-0": 0.0007,
}

# ── Live model fetch ──────────────────────────────────────────────────────────
def _fetch_live_llm_models() -> list:
    """
    Fetch the current serverless LLM list from Fireworks API.
    Returns fallback list if API call fails or key not set.
    """
    api_key = os.environ.get("FIREWORKS_API_KEY", "").strip()
    if not api_key:
        return _FALLBACK_LLM_MODELS

    try:
        resp = requests.get(
            "https://api.fireworks.ai/inference/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=8,
        )
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            # Keep only text/chat LLM models — exclude image, audio, embedding models
            _exclude = {
                "image", "whisper", "embedding", "reranker",
                "stable-diffusion", "flux", "playground", "SSD",
                "vision", "vl", "audio",
            }
            llms = [
                m["id"] for m in data
                if m.get("id", "").startswith("accounts/fireworks/models/")
                and not any(x in m.get("id", "").lower() for x in _exclude)
            ]
            if llms:
                # Put preferred models first if they exist in the live list
                _preferred = [
                    "accounts/fireworks/models/llama4-maverick-instruct-basic",
                    "accounts/fireworks/models/llama4-scout-instruct-basic",
                    "accounts/fireworks/models/llama-v3p3-70b-instruct",
                    "accounts/fireworks/models/llama-v3p1-8b-instruct",
                ]
                ordered = [m for m in _preferred if m in llms]
                rest    = [m for m in sorted(llms) if m not in ordered]
                return ordered + rest
    except Exception:
        pass

    return _FALLBACK_LLM_MODELS


# Fetch once at import time (cached for the session)
SERVERLESS_LLM_MODELS = _fetch_live_llm_models()
DEFAULT_LLM_MODEL     = SERVERLESS_LLM_MODELS[0]
