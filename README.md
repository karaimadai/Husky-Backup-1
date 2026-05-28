# AI Comic Generator — with Style Transfer

**Story → Script → Images → Speech Bubbles → Comic Page**

Powered by **Fireworks AI** (cheap image gen + LLM) and **Claude Vision** (style analysis).

---

## What's New: Style Transfer

You can now give the generator a **reference image** (or Instagram link) and it will clone that art style across every generated panel.

### How it works

```
Reference Image / IG URL
        │
        ▼
  Claude Vision API
  (style_analyzer.py)
        │
        ▼
  StyleProfile
  ├── style_prompt   → injected into Fireworks positive prompt
  ├── negative_prompt→ injected into Fireworks negative prompt
  ├── color_palette  → shown in UI
  └── linework       → shown in UI
        │
        ▼
  Fireworks AI (FLUX / SDXL)
  → Panels styled to match reference
```

### Cost breakdown

| Step | API | Cost |
|------|-----|------|
| Script (LLM) | Fireworks llama-v3p3-70b | ~$0.001 |
| Style analysis | Claude claude-sonnet-4-20250514 Vision | ~$0.003 per analysis |
| Images (4 panels) | Fireworks flux-1-schnell-fp8 | ~$0.0008 |
| **Total for 4-panel comic** | | **~$0.005** |

Style analysis is a one-time cost — analyzed once, applied to all panels.

---

## Setup

```bash
# 1. Clone / unzip the project
cd comic_generator

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set API keys
export FIREWORKS_API_KEY=fw_xxxx

# Claude API key — needed for Style Transfer only
# The app uses the standard Anthropic API endpoint (no key needed in claude.ai)
# For standalone use:
export ANTHROPIC_API_KEY=sk-ant-xxxx

# 4. Run
streamlit run app.py
```

---

## File Structure

```
comic_generator/
├── app.py              ← Main Streamlit app (Story + Style Transfer tabs)
├── style_analyzer.py   ← NEW: Claude Vision style extraction
├── image_generator.py  ← Fireworks image API (updated: extra_negative param)
├── script_generator.py ← Fireworks LLM → comic panel JSON
├── text_overlay.py     ← Speech bubbles + caption boxes (Pillow)
├── layout.py           ← Assembles panels into a comic page
├── requirements.txt
└── outputs/            ← Generated files saved here
```

---

## Style Transfer Tips

**What images work best:**
- Single comic panels with clear, consistent linework
- Manga / webtoon pages with distinct color signatures
- Illustration art from Instagram, Pixiv, ArtStation

**Instagram links:**
- Use post links: `https://www.instagram.com/p/POSTCODE/`
- Or reel links: `https://www.instagram.com/reel/REELCODE/`
- Public posts only

**Refining the style:**
- Use the hint box to focus Claude: *"emphasize the inking style"*, *"focus on color grading"*
- Use **Analyze + Preview Panel** to test before generating all panels
- The style prompt is just text — you can view and edit it in the UI

---

## How the Prompt Architecture Works

```
Panel prompt = [SHOT TYPE] + [COMIC_STYLE or STYLE_TRANSFER] + [CHARACTER] + [SCENE] + [EMOTION]
```

- **SHOT TYPE** is always first — it's the dominant instruction (rear_walk, side_profile, front_portrait, etc.)
- **COMIC_STYLE** is replaced by `StyleProfile.style_prompt` when Style Transfer is active
- **Negative prompt** merges the base negative + shot-specific negative + `StyleProfile.negative_prompt`

This means style transfer only affects **color, linework, and rendering** — the shot framing, character, and scene remain under your control.
