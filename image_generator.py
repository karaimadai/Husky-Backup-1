"""
image_generator.py — Fireworks AI image generation for Introvert Husky Instagram

Luna's character is LOCKED via luna_character.py.
Art style is fixed to Minimalist & Doodle-Like.
Character consistency is maintained via detailed text prompts, NOT by fixing the seed.
Each panel gets a random seed for composition variety.

Prompt order (flat/doodle style):
  STYLE → LUNA CHARACTER → SHOT TYPE → SCENE → MOOD
"""

import os
import random
import requests

from luna_character import (
    LUNA_NAME,
    LUNA_BODY,
    LUNA_FACE,
    LUNA_NEGATIVE_EXTRA,
    MINIMALIST_STYLE,
    INSTAGRAM_WIDTH,
    INSTAGRAM_HEIGHT,
)

FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY", "")
FIREWORKS_IMAGE_BASE = (
    "https://api.fireworks.ai/inference/v1/workflows/"
    "accounts/fireworks/models/{model}/text_to_image"
)
DEFAULT_IMAGE_MODEL = "flux-1-schnell-fp8"

# Art style is fixed — no runtime override
COMIC_STYLE = MINIMALIST_STYLE

# ─────────────────────────────────────────────────────────────────────────────
# SEED — random per panel for composition variety.
# Character consistency is enforced via the detailed prompt, not seed locking.
# ─────────────────────────────────────────────────────────────────────────────

def _panel_seed(index: int) -> int:
    """Random seed per panel so each panel has a unique composition."""
    return random.randint(1, 2**31 - 1)


# ─────────────────────────────────────────────────────────────────────────────
# NEGATIVE PROMPTS
# ─────────────────────────────────────────────────────────────────────────────

_NEG_MINIMALIST = (
    "photorealistic, realistic, 3d render, 3d cgi, painterly, oil painting, watercolor, "
    "shading, cel shading, highlights, ambient occlusion, drop shadow, cast shadow, "
    "gradients, color gradients, textures, crosshatching, hatching, stippling, "
    "complex background, detailed background, intricate, highly detailed, busy, "
    "dark colors, saturated colors, vivid colors, neon, dark mood, dramatic lighting, "
    "rim light, volumetric light, cinematic lighting, lens flare, bokeh, depth of field, "
    "heavy outlines, variable line weight, brush strokes, rough sketch, pencil marks, "
    "anime, manga, comic book, marvel, dc, realistic proportions, "
    "extra limbs, deformed, ugly, worst quality, low quality, jpeg artifacts"
)

_NEG_NO_FACE = (
    "face, portrait, selfie, front view of face, close-up face, "
    "looking at camera, eye contact, headshot, face in focus"
)

# ─────────────────────────────────────────────────────────────────────────────
# EMOTION COLOUR MAP — flat pastel language, no lighting terms
# ─────────────────────────────────────────────────────────────────────────────

_EMOTION_MAP_FLAT = {
    "tense":   "cool muted blue-grey background tones, sparse composition",
    "joyful":  "warm pastel yellow and peach background tones, open airy layout",
    "shocked": "pale background, wide simple dot eyes on Luna",
    "sad":     "muted cool pastel background, small quiet figure",
    "calm":    "soft pale green and sky blue background tones, balanced layout",
    "action":  "simple diagonal lines behind Luna to imply speed",
}

# ─────────────────────────────────────────────────────────────────────────────
# FLAT SHOT CATALOGUE — Luna is always fully visible and readable
# ─────────────────────────────────────────────────────────────────────────────

SHOT_CATALOGUE_FLAT = {
    "flat_front": {
        "prompt_prefix": (
            "full body front view, Luna facing camera, centred in frame, "
            "simple flat 2D illustration, character fills lower two thirds of panel"
        ),
        "show_face": True,
    },
    "flat_three_quarter": {
        "prompt_prefix": (
            "full body three-quarter view, Luna facing slightly left, "
            "flat illustration angle, whole body visible, simple background"
        ),
        "show_face": True,
    },
    "flat_side": {
        "prompt_prefix": (
            "full body side view, Luna facing left, "
            "flat 2D profile, whole body from head to paws visible, "
            "simple flat background, character at centre of frame"
        ),
        "show_face": False,
    },
    "flat_rear": {
        "prompt_prefix": (
            "full body rear view, Luna seen from behind, "
            "flat 2D illustration, whole body visible, "
            "character centred, simple flat background"
        ),
        "show_face": False,
    },
    "flat_sitting": {
        "prompt_prefix": (
            "full body, Luna sitting with paws tucked, "
            "flat 2D illustration, simple relaxed pose, "
            "character visible head to tail, centred in frame"
        ),
        "show_face": True,
    },
    "flat_lying": {
        "prompt_prefix": (
            "Luna lying down flat on her side or belly, paws stretched out, "
            "flat 2D cartoon, whole body visible, low centred composition"
        ),
        "show_face": True,
    },
    "flat_reaction": {
        "prompt_prefix": (
            "upper body and face visible, Luna with deadpan blank stare, "
            "flat 2D webcomic illustration, simple dot eyes no expression change, "
            "centered, plain background"
        ),
        "show_face": True,
    },
    "flat_two_shot": {
        "prompt_prefix": (
            "two characters side by side, Luna the grey husky and another character, "
            "full body, flat 2D illustration, "
            "simple cartoon style, plain simple background"
        ),
        "show_face": True,
    },
    "flat_action": {
        "prompt_prefix": (
            "full body, Luna in simple action pose — running or trotting, "
            "flat 2D cartoon illustration, exaggerated simple posture, "
            "whole body visible, white or plain background"
        ),
        "show_face": False,
    },
}

_FLAT_DEFAULT_ROTATION = [
    "flat_front", "flat_side", "flat_three_quarter", "flat_sitting",
    "flat_reaction", "flat_lying", "flat_rear", "flat_front",
]

# Environment prompts — no characters, just flat backgrounds
ENVIRONMENT_PROMPTS_FLAT = [
    "flat simple outdoor park scene, no characters, pastel sky, green ground, simple tree shapes",
    "flat cosy indoor room, simple sofa and lamp shapes, muted pastel walls, no characters",
    "flat rainy window view, simple raindrops on glass outline, grey sky outside, no characters",
    "flat cityscape, simple building outlines, pastel colors, empty street, no characters",
]

_ENVIRONMENT_KEYWORDS = [
    "establishing shot", "wide shot", "aerial", "bird's eye",
    "no character", "no one", "empty", "landscape", "cityscape",
    "flashback", "object close", "map", "building exterior",
]

_HERO_PRESENT_KEYWORDS = [
    "luna", "walks", "stands", "runs", "sits", "lies", "stares",
    "crouches", "reads", "hides", "watches", "ignores", "avoids",
    "holds", "eats", "sleeps", "looks", "peers", "types",
]


def _is_environment_panel(panel: dict) -> bool:
    scene = panel.get("scene", "").lower()
    chars = panel.get("characters", "").lower()
    dlg   = panel.get("dialogue", "").strip()

    if dlg:
        return False
    for kw in _ENVIRONMENT_KEYWORDS:
        if kw in scene:
            return True
    if "luna" not in chars and "luna" not in scene:
        return True
    combined = scene + " " + chars
    for kw in _HERO_PRESENT_KEYWORDS:
        if kw in combined:
            return False
    return True


def _get_supporting_char(panel: dict) -> str:
    """Extract supporting character description from panel characters field."""
    chars = panel.get("characters", "")
    # Split on comma or 'and', filter out Luna references
    parts = [p.strip() for p in chars.replace(" and ", ",").split(",")]
    supporting = [
        p for p in parts
        if p and "luna" not in p.lower() and len(p) > 2
    ]
    return supporting[0] if supporting else ""


def _select_shot_flat(panel: dict, index: int) -> str:
    scene    = panel.get("scene", "").lower()
    chars    = panel.get("characters", "").lower()
    dialogue = panel.get("dialogue", "").strip()
    emotion  = panel.get("emotion", "").lower()
    combined = scene + " " + chars

    # Two characters interacting — trigger when any supporting char present
    supporting = _get_supporting_char(panel)
    if supporting or any(k in combined for k in ["and another", "together", "face each other",
                                                   "another character", "other dog", "other cat"]):
        return "flat_two_shot"

    # Lying / resting
    if any(k in combined for k in ["lies", "lying", "curled up", "sprawled",
                                    "flat on", "on her back", "on the floor"]):
        return "flat_lying"

    # Sitting
    if any(k in combined for k in ["sits", "sitting", "perches", "crouches", "kneels"]):
        return "flat_sitting"

    # Action
    if any(k in combined for k in ["runs", "running", "trots", "dashes", "races"]):
        return "flat_action"

    # Reaction moment — use face
    if dialogue or emotion in ("shocked", "joyful", "sad"):
        return "flat_reaction"

    # Walking / moving — side view
    if any(k in combined for k in ["walks", "strides", "moves", "approaches", "enters"]):
        return "flat_side"

    # Facing away
    if any(k in combined for k in ["turns away", "back to", "facing away", "walks away"]):
        return "flat_rear"

    return _FLAT_DEFAULT_ROTATION[index % len(_FLAT_DEFAULT_ROTATION)]


# ─────────────────────────────────────────────────────────────────────────────
# COMPACT PROMPT CONSTANTS — strictly under 60 words to stay within FLUX's
# CLIP encoder 77-token limit. Every word earns its place.
# ─────────────────────────────────────────────────────────────────────────────

# Core style — 18 words
_STYLE_CORE = (
    "minimalist webcomic, flat 2D cartoon, clean black outlines, "
    "flat pastel colors, no shading, simple background, doodle illustration"
)

# Luna's body — 16 words
_LUNA_BODY_COMPACT = (
    "ash-grey white Siberian Husky, white chest, grey back, "
    "fluffy cartoon dog, four paws, flat 2D character"
)

# Luna's face — 10 words
_LUNA_FACE_COMPACT = (
    "large round dark eyes, small black nose, deadpan expression"
)

# Compact shot prefixes — max 10 words each
_SHOTS_COMPACT = {
    "flat_front":         "full body, front view, centred",
    "flat_three_quarter": "full body, three-quarter view",
    "flat_side":          "full body, side profile view, facing left",
    "flat_rear":          "full body, rear view, seen from behind",
    "flat_sitting":       "Luna sitting, paws tucked, full body",
    "flat_lying":         "Luna lying down, whole body visible",
    "flat_reaction":      "upper body close, deadpan face, centred",
    "flat_two_shot":      "two characters side by side, full body",
    "flat_action":        "full body, running pose, whole body visible",
}

# Compact environment prompts — max 10 words each
_ENV_COMPACT = [
    "flat pastel park, simple trees, no characters",
    "flat cosy indoor room, simple furniture, no characters",
    "flat rainy window scene, grey sky, no characters",
    "flat simple street, pastel buildings, no characters",
]

# Compact emotion mood — max 6 words each
_EMOTION_COMPACT = {
    "tense":   "cool grey pastel background",
    "joyful":  "warm yellow pastel background",
    "shocked": "pale background, wide eyes",
    "sad":     "muted blue pastel background",
    "calm":    "soft green pastel background",
    "action":  "diagonal lines, motion implied",
}


def _build_luna_prompt(panel: dict, index: int) -> tuple:
    """
    Build a compact positive prompt strictly under 77 words so it stays within
    FLUX's CLIP encoder 77-token limit. Negative prompt only used for SDXL.
    Supporting characters are featured prominently when present.
    """
    scene         = panel.get("scene", "").strip()
    emotion       = panel.get("emotion", "calm").lower()
    emotion_mood  = _EMOTION_COMPACT.get(emotion, "soft pastel background")

    # Detect supporting character
    supporting = _get_supporting_char(panel)

    # Truncate scene to max 12 words to keep total under limit
    scene_words = scene.split()
    if len(scene_words) > 12:
        scene = " ".join(scene_words[:12])

    if _is_environment_panel(panel):
        env = _ENV_COMPACT[index % len(_ENV_COMPACT)]
        positive = ", ".join(filter(None, [
            _STYLE_CORE,
            env,
            scene[:80],
            emotion_mood,
        ]))
        shot_label = "FLAT-ENV"
    else:
        shot_key  = _select_shot_flat(panel, index)
        show_face = SHOT_CATALOGUE_FLAT[shot_key]["show_face"]
        shot_str  = _SHOTS_COMPACT.get(shot_key, "full body, centred")

        luna_desc = _LUNA_BODY_COMPACT
        if show_face:
            luna_desc = _LUNA_BODY_COMPACT + ", " + _LUNA_FACE_COMPACT

        # Build supporting character description for the prompt
        if supporting and shot_key == "flat_two_shot":
            # Feature the supporting character prominently in two-shot panels
            # Extract a concise visual description from their name
            supp_short = supporting[:40]  # keep it brief for token budget
            char_block = f"{luna_desc}, beside {supp_short}, both clearly visible, equal prominence"
        elif supporting:
            # Supporting character present but not two-shot — still hint at them
            supp_short = supporting[:30]
            char_block = f"{luna_desc}, {supp_short} nearby"
        else:
            char_block = luna_desc

        positive = ", ".join(filter(None, [
            _STYLE_CORE,
            char_block,
            shot_str,
            scene[:60],
            emotion_mood,
        ]))
        shot_label = f"FLAT-{'FACE' if show_face else 'NOFACE'} [{shot_key}]"
        if supporting:
            shot_label += f" +{supporting[:20]}"

    # Verify we're under the limit
    word_count = len(positive.split())
    if word_count > 77:
        # Emergency trim: rebuild without scene
        if _is_environment_panel(panel):
            positive = ", ".join(filter(None, [_STYLE_CORE, env, emotion_mood]))
        else:
            positive = ", ".join(filter(None, [_STYLE_CORE, luna_desc, shot_str]))

    print(f"  [Prompt] {word_count} words: {positive[:100]}...")

    negative = _NEG_MINIMALIST
    return positive, negative, shot_label


def _dims_to_aspect_ratio(width: int, height: int) -> str:
    """
    Convert width/height to the nearest supported FLUX aspect_ratio string.
    Fireworks FLUX supported values: 1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3
    """
    _supported = {
        (1, 1):  "1:1",
        (16, 9): "16:9",
        (9, 16): "9:16",
        (4, 3):  "4:3",
        (3, 4):  "3:4",
        (3, 2):  "3:2",
        (2, 3):  "2:3",
    }
    ratio = width / height
    best_key  = min(_supported, key=lambda k: abs(k[0] / k[1] - ratio))
    return _supported[best_key]


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def check_fireworks() -> bool:
    return bool(os.environ.get("FIREWORKS_API_KEY", ""))


def generate_image(
    panel: dict,
    index: int,
    char_name: str = LUNA_NAME,       # kept for API compatibility, Luna is always used
    char_body: str = LUNA_BODY,       # locked — ignored if char_name == "Luna"
    char_face: str = LUNA_FACE,       # locked
    model: str = DEFAULT_IMAGE_MODEL,
    width: int = INSTAGRAM_WIDTH,
    height: int = INSTAGRAM_HEIGHT,
    steps: int = 4,
    num_panels: int = 4,
    extra_negative: str = "",
) -> str:
    """Generate one Instagram panel for the Introvert Husky page."""
    api_key = os.environ.get("FIREWORKS_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "FIREWORKS_API_KEY is not set.\n"
            "export FIREWORKS_API_KEY=fw_xxxx"
        )

    positive, negative, shot_label = _build_luna_prompt(panel, index)

    model_slug = model.split("/")[-1]
    url = FIREWORKS_IMAGE_BASE.format(model=model_slug)
    is_flux = "flux" in model_slug.lower()

    print(f"  [Panel {index+1}] {shot_label}")
    print(f"           prompt: {positive[:140]}...")

    if is_flux:
        # FLUX workflow endpoint on Fireworks:
        # - Uses aspect_ratio string, NOT width/height integers
        # - Does NOT support negative_prompt (causes tensor dimension error)
        # - Does NOT support guidance_scale (fixed internally)
        # Supported aspect_ratios: "1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"
        ar = _dims_to_aspect_ratio(width, height)
        payload = {
            "prompt":               positive,
            "aspect_ratio":         ar,
            "num_inference_steps":  steps,
            "seed":                 _panel_seed(index),
        }
    else:
        # SDXL / Playground: supports width, height, negative_prompt, guidance_scale
        safe_w = max(64, (width  // 64) * 64)
        safe_h = max(64, (height // 64) * 64)
        payload = {
            "prompt":               positive,
            "negative_prompt":      negative + (", " + extra_negative if extra_negative else ""),
            "width":                safe_w,
            "height":               safe_h,
            "num_inference_steps":  steps,
            "guidance_scale":       5.5,
            "num_images":           1,
            "seed":                 _panel_seed(index),
        }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "image/png",
    }

    response = requests.post(url, json=payload, headers=headers, timeout=120)

    if response.status_code != 200:
        try:
            err = response.json()
        except Exception:
            err = response.text[:400]
        raise RuntimeError(
            f"Fireworks API error {response.status_code}: {err}\nURL: {url}"
        )

    os.makedirs("outputs", exist_ok=True)
    save_path = f"outputs/panel_{index}.png"
    with open(save_path, "wb") as f:
        f.write(response.content)

    print(f"  [Panel {index+1}] saved → {save_path}")
    return save_path
