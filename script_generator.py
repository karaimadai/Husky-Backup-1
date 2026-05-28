"""
script_generator.py — Comic script generation via Fireworks AI LLM

Fixes vs previous version:
  1. Uses LUNA_SYSTEM_PROMPT from luna_character.py (was using generic prompt)
  2. Reads API key from os.environ at call time (not import time)
  3. Robust JSON extraction handles truncated/wrapped responses
  4. Model IDs imported from fireworks_models.py only
"""

import os
import json
import re
import requests

from fireworks_models import DEFAULT_LLM_MODEL

# Import Luna's personality-tuned system prompt
# This was defined in luna_character.py but never wired in — fixed here.
try:
    from luna_character import LUNA_SYSTEM_PROMPT
except ImportError:
    LUNA_SYSTEM_PROMPT = None   # fallback if used outside Luna project

FIREWORKS_CHAT_URL = "https://api.fireworks.ai/inference/v1/chat/completions"


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL: raw LLM call
# ─────────────────────────────────────────────────────────────────────────────

def _call_fireworks_llm(
    system: str,
    user: str,
    model: str = DEFAULT_LLM_MODEL,
    max_tokens: int = 2048,
    temperature: float = 0.7,
) -> str:
    """POST to Fireworks chat completions and return the text content."""
    api_key = os.environ.get("FIREWORKS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "FIREWORKS_API_KEY is not set.\n"
            "Get your key at https://fireworks.ai and run:\n"
            "  export FIREWORKS_API_KEY=fw_xxxx\n"
            "or enter it in the sidebar."
        )

    payload = {
        "model":       model,
        "max_tokens":  max_tokens,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
    }

    try:
        response = requests.post(
            FIREWORKS_CHAT_URL, json=payload, headers=headers, timeout=90
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("Fireworks API timed out. Try again or switch to the 8B model.")

    if response.status_code != 200:
        try:
            err = response.json()
        except Exception:
            err = response.text[:400]
        raise RuntimeError(
            f"Fireworks LLM error {response.status_code}: {err}\n"
            f"Model used: {model}\n\n"
            f"If you see 404, the model may be unavailable. "
            f"Try switching to a different Script LLM in the sidebar."
        )

    return response.json()["choices"][0]["message"]["content"].strip()


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL: JSON extraction — handles all LLM response formats
# ─────────────────────────────────────────────────────────────────────────────

def _extract_json_array(raw: str) -> list | None:
    """
    Robustly extract a JSON array from an LLM response that may:
    - Be wrapped in ```json ... ``` fences
    - Have preamble text before the array
    - Be truncated mid-response (common with long outputs)
    - Wrap the array in a dict key like {"panels": [...]}
    """
    # Strip markdown fences
    clean = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    clean = re.sub(r"\s*```$",          "", clean,        flags=re.MULTILINE).strip()

    # 1. Try parsing the whole thing
    try:
        parsed = json.loads(clean)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            for key in ("panels", "comic", "script", "result", "data"):
                if key in parsed and isinstance(parsed[key], list):
                    return parsed[key]
    except json.JSONDecodeError:
        pass

    # 2. Find the first [ ... ] block (handles preamble text)
    bracket_match = re.search(r"\[.*\]", clean, re.DOTALL)
    if bracket_match:
        try:
            parsed = json.loads(bracket_match.group())
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

    # 3. Handle truncated JSON — find all complete panel objects { ... }
    # This recovers panels even when the last one is cut off
    panel_matches = re.findall(
        r'\{\s*"panel"\s*:.*?"caption"\s*:\s*"[^"]*"\s*\}',
        clean, re.DOTALL
    )
    if panel_matches:
        try:
            panels = [json.loads(p) for p in panel_matches]
            if panels:
                return panels
        except json.JSONDecodeError:
            pass

    return None


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC: story summary captions
# ─────────────────────────────────────────────────────────────────────────────

def generate_story_summary(story: str, num_panels: int, model: str = DEFAULT_LLM_MODEL) -> list:
    """Return exactly num_panels narrator caption strings covering the full story."""
    system = (
        "You are a comic-book narrator. "
        "Summarise stories as punchy, sequential caption lines. "
        "Return ONLY a JSON array of strings — no markdown, no extra keys."
    )
    user = (
        f"Summarise this story as exactly {num_panels} short narrator captions.\n\n"
        f"Rules:\n"
        f"- Exactly {num_panels} items in the array.\n"
        f"- Each caption: 1-2 sentences, max 20 words.\n"
        f"- Cover the FULL story: beginning → middle → climax → resolution.\n"
        f"- Present tense, narrator voice.\n"
        f"- Return ONLY a JSON array of strings.\n\n"
        f"Story:\n{story}\n\nJSON array:"
    )

    raw   = _call_fireworks_llm(system, user, model=model, max_tokens=1024, temperature=0.5)
    clean = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()

    try:
        captions = json.loads(clean)
        if isinstance(captions, list) and captions:
            while len(captions) < num_panels:
                captions.append(captions[-1])
            return [str(c).strip() for c in captions[:num_panels]]
    except (json.JSONDecodeError, TypeError):
        pass

    match = re.search(r"\[.*?\]", clean, re.DOTALL)
    if match:
        try:
            captions = json.loads(match.group())
            if isinstance(captions, list):
                while len(captions) < num_panels:
                    captions.append(captions[-1])
                return [str(c).strip() for c in captions[:num_panels]]
        except (json.JSONDecodeError, TypeError):
            pass

    # Hard fallback: chop story into sentence chunks
    sentences  = [s.strip() for s in re.split(r"(?<=[.!?])\s+", story.strip()) if s.strip()]
    chunk_size = max(1, len(sentences) // num_panels)
    chunks = []
    for i in range(num_panels):
        start = i * chunk_size
        end   = start + chunk_size if i < num_panels - 1 else len(sentences)
        chunk = " ".join(sentences[start:end])
        chunks.append(chunk[:120] + ("..." if len(chunk) > 120 else ""))
    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC: main script generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_script(
    story: str,
    num_panels: int = 4,
    model: str = DEFAULT_LLM_MODEL,
    summary_captions: bool = True,
    supporting_char: str = "",
) -> list:
    """
    Convert a story into a list of comic panel dicts.

    Uses LUNA_SYSTEM_PROMPT if available (Luna project) so the LLM knows
    Luna's personality, tone, and introvert character. Falls back to a
    generic comic scriptwriter prompt otherwise.

    Each dict: {panel, scene, characters, dialogue, emotion, caption}
    """
    # ── System prompt: use Luna's personality prompt if available ─────────────
    if LUNA_SYSTEM_PROMPT:
        system = LUNA_SYSTEM_PROMPT
    else:
        system = (
            "You are a professional comic book scriptwriter. "
            "Convert stories into visual comic panel scripts. "
            "Return ONLY valid JSON — no markdown fences, no explanation. "
            "Every field is required. Keep dialogue short like real comics."
        )

    # ── Build supporting character rules ──────────────────────────────────────
    if supporting_char:
        char_rule_scene = (
            f"- The supporting character is: {supporting_char}. "
            f"They must appear visually in the scene description and characters field whenever they are part of the action. "
            f"Do NOT reduce them to a vague mention — name them and describe what they are doing."
        )
        char_rule_dialogue = (
            f"- {supporting_char} can have their own dialogue lines — they are a full participant, not background. "
            f"Give them equal visual weight to Luna in panels where they appear."
        )
        char_rule_chars = (
            f'    "characters": "Always list Luna the grey husky AND {supporting_char} by name in panels they share.",'
        )
    else:
        char_rule_scene    = "- scene must be VISUAL and SPECIFIC — describe what we see"
        char_rule_dialogue = ""
        char_rule_chars    = '    "characters": "Always include Luna the grey husky plus any others.",'

    # ── User prompt: structured JSON request ──────────────────────────────────
    user = (
        f"Convert this story into exactly {num_panels} comic panels for Luna the Introvert Husky.\n\n"
        f"Return ONLY a JSON array — no markdown, no preamble, no explanation:\n"
        f"[\n"
        f"  {{\n"
        f'    "panel": 1,\n'
        f'    "scene": "Visual description — flat 2D cartoon setting, name every character present and what they are doing- The scene/location must remain consistent across all panels unless a location change is explicitly part of the story.",\n'
        f"    {char_rule_chars}\n"
        f'    "dialogue": "Max 8 words, dry introvert humour or empty string.",\n'
        f'    "emotion": "One of: tense | joyful | shocked | sad | calm | action",\n'
        f'    "caption": "Narrator caption max 12 words, or empty string."\n'
        f"  }}\n"
        f"]\n\n"
        f"Rules:\n"
        f"- scene must be VISUAL and SPECIFIC — describe what we see\n"
        f"{char_rule_scene}\n"
        f"{char_rule_dialogue}\n"
        f"- dialogue is SHORT — Luna is an introvert, she under-reacts\n"
        f"- Luna never becomes excited or extroverted\n"
        f"- spread the story: beginning, middle, climax, resolution\n"
        f"- return EXACTLY {num_panels} panels\n\n"
        f"Story:\n{story}\n\n"
        f"JSON array ({num_panels} panels):"
    )

    raw    = _call_fireworks_llm(system, user, model=model, max_tokens=3000)
    parsed = _extract_json_array(raw)

    if parsed is None:
        raise ValueError(
            f"Could not parse JSON from the LLM response.\n"
            f"Model: {model}\n"
            f"Try switching to a different Script LLM in the sidebar.\n\n"
            f"Raw response (first 500 chars):\n{raw[:500]}"
        )

    panels = _validate_panels(parsed, num_panels)

    if not panels:
        raise ValueError(
            f"LLM returned {len(parsed)} items but none could be validated as panels.\n"
            f"Model: {model}\n"
            f"Raw response:\n{raw[:500]}"
        )

    # Pad to requested count if fewer panels returned
    while len(panels) < num_panels:
        last = dict(panels[-1])
        last["panel"]    = len(panels) + 1
        last["dialogue"] = ""
        last["caption"]  = ""
        panels.append(last)

    if summary_captions:
        try:
            summaries = generate_story_summary(story, num_panels, model=model)
            for i, panel in enumerate(panels):
                panel["caption"] = summaries[i]
        except Exception:
            pass   # keep whatever captions the LLM generated

    return panels


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL: validation
# ─────────────────────────────────────────────────────────────────────────────

def _validate_panels(panels: list, num_panels: int) -> list:
    """Ensure every panel dict has all required fields with sensible defaults."""
    defaults = {
        "panel":      0,
        "scene":      "Luna sits quietly in a simple room.",
        "characters": "Luna the grey husky",
        "dialogue":   "",
        "emotion":    "calm",
        "caption":    "",
    }
    valid = []
    for i, p in enumerate(panels[:num_panels]):
        if not isinstance(p, dict):
            continue
        cleaned = {}
        for field, default in defaults.items():
            val = p.get(field, default)
            if field == "dialogue" and isinstance(val, str):
                words = val.split()
                if len(words) > 12:
                    val = " ".join(words[:12]) + "..."
            cleaned[field] = val if val is not None else default
        if cleaned["panel"] == 0:
            cleaned["panel"] = i + 1
        valid.append(cleaned)
    return valid
