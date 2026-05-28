"""
luna_character.py — Locked character definition for Luna the Introvert Husky.

This module is the SINGLE SOURCE OF TRUTH for Luna's appearance.
All image generation passes these constants so Luna looks the same in every panel.

Character spec:
  - Ash-grey & white Siberian Husky
  - White chest, grey back and head
  - Large round dark eyes · small black nose
  - Pointed grey ears with white inner
  - Deadpan / neutral expression (introvert vibes)
  - Art style: Minimalist & Doodle-Like ONLY
"""

# ─────────────────────────────────────────────────────────────────────────────
# LUNA — locked identity
# ─────────────────────────────────────────────────────────────────────────────

LUNA_NAME = "Luna"

# Body description — doodle-ready language (no anatomy realism)
LUNA_BODY = (
    "ash-grey and white Siberian Husky dog, "
    "simple rounded cartoon dog body shape, "
    "white chest and belly, ash-grey back and head, "
    "pointed grey ears with white inner ear, "
    "fluffy tail, four short legs, "
    "flat 2D cartoon character, "
    "consistent same husky dog in every panel, "
    "same grey and white color scheme always"
)

# Face description — minimalist doodle language
LUNA_FACE = (
    "large round dark dot eyes, "
    "small black oval nose, "
    "deadpan neutral expression, "
    "no smile no frown, "
    "simple minimal face, "
    "introvert blank stare, "
    "ash-grey head with white muzzle patch"
)

# Additional negative prompt terms to enforce Luna's consistency
LUNA_NEGATIVE_EXTRA = (
    "human, person, man, woman, boy, girl, cat, other animal breed, "
    "realistic dog, photorealistic fur, brown dog, black dog, golden dog, "
    "happy smile, open mouth, tongue out, excited expression, "
    "angry expression, sharp teeth, "
    "complex shading, fur texture detail"
)

# ─────────────────────────────────────────────────────────────────────────────
# FIXED ART STYLE — Minimalist & Doodle-Like only for Introvert Husky page
# ─────────────────────────────────────────────────────────────────────────────

MINIMALIST_STYLE = (
    "minimalist webcomic panel, flat 2D illustration, "
    "simple vector landscape background, "
    "flat muted pastel color palette, light sky blue background, soft sage green ground, "
    "clean uniform black outlines, slightly hand-drawn imperfect line quality, "
    "no shading, no highlights, no gradients, no textures, no drop shadows, "
    "simple flat background elements like trees rocks grass clouds, "
    "deadpan expressionless husky dog face, simple dot or line eyes, "
    "children's book doodle aesthetic, webcomic strip style, "
    "flat color fills only, minimal detail, 2D cartoon illustration"
)

# ─────────────────────────────────────────────────────────────────────────────
# INSTAGRAM FORMAT — square panels optimised for 1:1 feed posts
# ─────────────────────────────────────────────────────────────────────────────

INSTAGRAM_WIDTH  = 1024
INSTAGRAM_HEIGHT = 1024

# ─────────────────────────────────────────────────────────────────────────────
# INTROVERT HUSKY — scene theme suggestions for the UI
# ─────────────────────────────────────────────────────────────────────────────

SCENE_SUGGESTIONS = [
    "Luna sits alone on a park bench while other dogs play fetch nearby",
    "Luna reads a book under a tree, headphones on, ignoring everyone",
    "Luna stares blankly at a crowded dog party from the doorway",
    "Luna hides behind a large indoor plant at a social gathering",
    "Luna watches Netflix alone wrapped in a blanket, snacks beside her",
    "Luna avoids eye contact with an overly enthusiastic Golden Retriever",
    "Luna sends a 'I can't make it' text while still in pajamas at noon",
    "Luna quietly enjoys a rainy window view with hot cocoa",
    "Luna pretends to be asleep to avoid a phone call",
    "Luna discovers someone sat in her favourite quiet corner of the cafe",
    "Luna uses 'I have plans' when the plans are clearly just being alone",
    "Luna at a crowded dog park, sitting far from everyone looking relieved",
]

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT for LLM script generation — tuned for Introvert Husky content
# ─────────────────────────────────────────────────────────────────────────────

LUNA_SYSTEM_PROMPT = """You are a comic scriptwriter for "Introvert Husky" — a minimalist Instagram comic
starring Luna, an ash-grey and white Siberian Husky with a permanent deadpan expression and strong
introvert energy.

Tone: dry humour, relatable introvert struggles, quiet slice-of-life moments.
Luna communicates with short, understated dialogue or silent deadpan reactions.
Other characters (other dogs, cats, humans) are secondary and change each story.
Luna is ALWAYS the main character. Luna NEVER becomes extroverted or excited.

For each panel produce a JSON object with:
  - scene: what is visually happening (describe as flat 2D cartoon, mention Luna by name)
  - characters: who is present (always include "Luna the grey husky")
  - dialogue: short spoken text or empty string (max 8 words, introvert-style)
  - emotion: one of tense | calm | sad | joyful | shocked | action
  - caption: optional narrator caption (max 12 words) or empty string
"""
