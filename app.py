"""
app.py — Introvert Husky Instagram Comic Generator
Story → Script (LLM) → Panels (Fireworks AI) → Instagram-ready images

Luna the ash-grey Siberian Husky is the FIXED main character.
Art style is locked to Minimalist & Doodle-Like.
Output is square (1024×1024) for Instagram.

Run:
    export FIREWORKS_API_KEY=fw_xxxx
    streamlit run app.py
"""

import os
import shutil
import zipfile
import io as _io

import streamlit as st

from luna_character import (
    LUNA_NAME,
    LUNA_BODY,
    LUNA_FACE,
    LUNA_NEGATIVE_EXTRA,
    MINIMALIST_STYLE,
    INSTAGRAM_WIDTH,
    INSTAGRAM_HEIGHT,
    LUNA_SYSTEM_PROMPT,
)
from fireworks_models import (
    SERVERLESS_LLM_MODELS,
    SERVERLESS_IMAGE_MODELS,
    DEFAULT_LLM_MODEL,
    DEFAULT_IMAGE_MODEL,
    IMAGE_COST_PER_PANEL,
)
from script_generator import generate_script
from image_generator import generate_image, check_fireworks
from text_overlay import add_speech_bubble, add_caption_box, get_caption_box_height
from layout import create_comic_page

os.makedirs("outputs", exist_ok=True)

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🐺 Introvert Husky — Luna Comic Generator",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🐺 Introvert Husky — Luna Comic Generator")
st.caption("Create Instagram-ready minimalist comics starring Luna the deadpan ash-grey Husky")

# ── API Key check ─────────────────────────────────────────────────────────────
if not os.environ.get("FIREWORKS_API_KEY"):
    st.warning(
        "⚠️  **FIREWORKS_API_KEY not set.**\n\n"
        "Get your free key at [fireworks.ai](https://fireworks.ai) and run:\n"
        "```bash\nexport FIREWORKS_API_KEY=fw_xxxx\nstreamlit run app.py\n```\n\n"
        "Or enter it below (not saved to disk):",
        icon="🔑",
    )
    api_key_input = st.text_input("Fireworks API Key", type="password", placeholder="fw_xxxx...")
    if api_key_input:
        os.environ["FIREWORKS_API_KEY"] = api_key_input
        st.success("API key set for this session. Reload the page to refresh the model list.")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")

    num_panels = st.slider("Number of Panels", 1, 12, 4,
                            help="Instagram carousels work best with 4–10 panels.")

    # ── Luna character card — read-only ───────────────────────────────────────
    st.subheader("🐾 Main Character: Luna")
    with st.expander("Luna's Character Sheet (locked)", expanded=False):
        st.markdown("""
**Name:** Luna  
**Breed:** Ash-grey & white Siberian Husky  
**Personality:** Deadpan introvert, minimal energy  

**Appearance:**
- Ash-grey head & back · White chest & belly
- Large round dark eyes · Small black nose
- Pointed grey ears with white inner
- Fluffy tail · Four short paws
- Permanent neutral / deadpan expression

**Art Style:** Minimalist & Doodle-Like (locked)  
**Format:** 1024 × 1024 px (Instagram square)  

> Luna's look is locked so she looks the same in every panel.  
> Other characters (other dogs, cats, humans) can change freely.
        """)

    # ── Supporting character (optional) ──────────────────────────────────────
    st.subheader("Supporting Character (optional)")
    supporting_char = st.text_input(
        "Other character in this comic",
        placeholder="e.g. Biscuit the golden retriever, a grumpy cat, Luna's owner...",
        help="This character will appear alongside Luna. Luna's look is always fixed.",
    )

    # ── LLM model ─────────────────────────────────────────────────────────────
    st.subheader("🔥 Fireworks AI Models")

    image_model = st.selectbox(
        "Image Model",
        options=SERVERLESS_IMAGE_MODELS,
        index=SERVERLESS_IMAGE_MODELS.index(DEFAULT_IMAGE_MODEL),
        help="flux-1-schnell-fp8: fastest & cheapest | flux-1-dev-fp8: higher quality ~2× cost",
    )

    llm_model = st.selectbox(
        "Script LLM",
        options=SERVERLESS_LLM_MODELS,
        index=SERVERLESS_LLM_MODELS.index(DEFAULT_LLM_MODEL),
        help="Llama 3.3 70B gives the best comic scripts. Use 8B for faster/cheaper.",
    )

    steps = st.slider("Inference Steps", 1, 50, 4,
                       help="4 is ideal for Flux-schnell. Use 20–30 for SDXL.")

    # ── Speech Bubbles ────────────────────────────────────────────────────────
    st.subheader("Speech Bubbles")
    bubble_font_size   = st.slider("Bubble Font Size", 10, 36, 20)
    alternate_position = st.checkbox("Alternate bubble position (top/bottom)", True)
    show_captions      = st.checkbox("Show narrator captions", True)
    summary_captions   = st.checkbox("Use full story summary as captions", True)
    bubble_w_pct       = st.slider("Bubble Width (%)", 20, 95, 36)
    bubble_opacity     = st.slider("Bubble Opacity", 0, 255, 26)
    bubble_w_frac      = bubble_w_pct / 100.0

    st.divider()

    est = IMAGE_COST_PER_PANEL.get(image_model, 0.001) * num_panels
    st.metric("💰 Est. image cost", f"~${est:.4f}")

    if check_fireworks():
        st.success("✅ Fireworks API key set")
    else:
        st.error("❌ No API key — set FIREWORKS_API_KEY")

# ── Main: Story input ─────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    story = st.text_area(
        "Luna's Story / Scenario",
        value="",
        placeholder=(
            "Luna discovers the cafe she loves is now crowded every day. "
            "She tries three different escape plans but keeps running into people. "
            "Eventually she finds a hidden corner behind a bookshelf and finally has peace."
        ),
        height=140,
        help=(
            "Describe what happens to Luna. Keep it slice-of-life and relatable. "
            "Luna is always the main character — other characters can appear too."
        ),
    )
    comic_title = st.text_input("Instagram Post Title (optional)", "")

with col2:
    st.info("""
**Tips for good Luna comics:**
- Focus on everyday introvert situations
- Short dry dialogue works best
- Luna rarely smiles or reacts dramatically
- Other characters can be energetic — Luna is not
- Leave dialogue blank for silent deadpan panels
    """)

    if supporting_char:
        st.info(f"🐾 Supporting character: **{supporting_char}**")

    st.caption(f"🎨 Art style: **Minimalist & Doodle-Like** (locked)  \n🖼️ Output: **1024 × 1024 px** (Instagram square)")

# ── Generate ──────────────────────────────────────────────────────────────────
if st.button("🎨 Generate Luna Comic", type="primary", disabled=not story):
    if not check_fireworks():
        st.error("Fireworks API key is required.")
        st.stop()

    import image_generator as ig
    import script_generator as sg

    # Ensure image generator uses Luna's locked style
    ig.COMIC_STYLE       = MINIMALIST_STYLE
    ig.FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY", "")
    # Note: sg.FIREWORKS_API_KEY is NOT needed — script_generator.py
    # reads os.environ["FIREWORKS_API_KEY"] directly at call time.

    # Build story context including supporting character if given
    story_context = story
    if supporting_char:
        story_context = (
            f"{story}\n\n"
            f"Supporting character in this story: {supporting_char}"
        )

    progress = st.progress(0)
    status   = st.empty()

    # ── Step 1: Script ────────────────────────────────────────────────────────
    status.write("**Step 1 / 3** — Writing Luna's comic script...")
    try:
        panels = generate_script(
            story_context,
            num_panels=num_panels,
            model=llm_model,
            summary_captions=summary_captions,
            supporting_char=supporting_char,
        )
        progress.progress(15)
    except Exception as e:
        st.error(f"Script generation failed: {e}")
        st.stop()

    # Ensure all panel characters mention Luna, and supporting char where relevant
    for p in panels:
        if "luna" not in p.get("characters", "").lower():
            p["characters"] = "Luna the grey husky, " + p.get("characters", "")
        # If a supporting character was specified but missing from characters field, add them
        if supporting_char and supporting_char.lower() not in p.get("characters", "").lower():
            if supporting_char.lower() in p.get("scene", "").lower():
                p["characters"] = p.get("characters", "") + f", {supporting_char}"

    with st.expander("📋 Generated Script", expanded=False):
        for p in panels:
            st.markdown(f"""
**Panel {p.get('panel', '?')}**
- Scene: {p.get('scene', '')}
- Characters: {p.get('characters', '')}
- Dialogue: *\"{p.get('dialogue', '')}\"*
- Emotion: {p.get('emotion', '')}
- Caption: {p.get('caption', '') or '(none)'}
""")

    # ── Step 2: Images ────────────────────────────────────────────────────────
    status.write("**Step 2 / 3** — Generating panel images for Luna...")
    raw_paths     = []
    preview_paths = []
    panel_cols    = st.columns(min(len(panels), 5))

    for i, panel in enumerate(panels):
        progress.progress(15 + int((i / len(panels)) * 65))
        status.write(
            f"**Step 2 / 3** — Panel {i + 1} / {len(panels)}: "
            f"*{panel.get('scene', '')[:60]}...*"
        )

        try:
            img_path = generate_image(
                panel, i,
                char_name=LUNA_NAME,
                char_body=LUNA_BODY,
                char_face=LUNA_FACE,
                model=image_model,
                width=INSTAGRAM_WIDTH,
                height=INSTAGRAM_HEIGHT,
                steps=steps,
                num_panels=len(panels),
                extra_negative=LUNA_NEGATIVE_EXTRA,
            )
            raw_paths.append(img_path)
        except Exception as e:
            st.warning(f"Panel {i + 1} image failed: {e}")
            continue

        # Add speech bubble for preview
        dialogue  = panel.get("dialogue", "").strip()
        caption   = panel.get("caption",  "").strip()
        position  = ("top" if i % 2 == 0 else "bottom") if alternate_position else "top"
        speaker   = "left" if i % 2 == 0 else "right"
        work_path = img_path
        caption_h = 0

        if show_captions and caption:
            cap_path = f"outputs/cap_{i}.png"
            add_caption_box(work_path, caption, cap_path, font_size=18)
            work_path = cap_path
            caption_h = get_caption_box_height(img_path, font_size=18)

        preview_path = f"outputs/preview_{i}.png"
        if dialogue:
            top_offset = caption_h if position == "top" else 0
            add_speech_bubble(
                work_path, dialogue, preview_path,
                font_size=bubble_font_size,
                position=position,
                speaker=speaker,
                top_offset=top_offset,
                use_comic_sans=True,   # always comic-sans for doodle style
                bubble_w_frac=bubble_w_frac,
                bubble_alpha=bubble_opacity,
            )
        else:
            shutil.copy(work_path, preview_path)

        preview_paths.append(preview_path)

        col_idx = i % len(panel_cols)
        with panel_cols[col_idx]:
            label = dialogue[:30] + "..." if len(dialogue) > 30 else dialogue
            st.image(preview_path, caption=f"Panel {i + 1}: {label}", use_column_width=True)

    if not raw_paths:
        st.error("No panels were generated. Check your API key and try again.")
        st.stop()

    # ── Step 3: Assemble ──────────────────────────────────────────────────────
    status.write("**Step 3 / 3** — Assembling Instagram comic page...")
    progress.progress(90)

    try:
        page_title = comic_title or "Introvert Husky"
        comic_path = create_comic_page(
            raw_paths,
            output="outputs/final_comic.png",
            title=page_title,
            panel_data=panels,
            bubble_cfg={
                "alternate_position": alternate_position,
                "show_captions":      show_captions,
                "comic_sans":         True,
                "bubble_w_frac":      bubble_w_frac,
                "bubble_alpha":       bubble_opacity,
            },
        )
        progress.progress(100)
        status.empty()

        st.success(f"✅ Luna's comic is ready! {len(raw_paths)} panels assembled.")
        st.image(comic_path, use_column_width=True)

        dl_col1, dl_col2 = st.columns(2)

        with dl_col1:
            with open(comic_path, "rb") as f:
                st.download_button(
                    "⬇️ Download Assembled Comic (PNG)", f,
                    file_name="luna_comic.png", mime="image/png",
                    use_container_width=True,
                )

        with dl_col2:
            zip_buf = _io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for idx, fp in enumerate(preview_paths):
                    zf.write(fp, arcname=f"luna_panel_{idx + 1:02d}.png")
            zip_buf.seek(0)
            title_slug = (comic_title or "luna").lower().replace(" ", "_")
            st.download_button(
                f"⬇️ Download All {len(preview_paths)} Panels (ZIP)",
                zip_buf,
                file_name=f"{title_slug}_panels.zip",
                mime="application/zip",
                use_container_width=True,
            )

        actual_cost = IMAGE_COST_PER_PANEL.get(image_model, 0.001) * len(raw_paths)
        st.caption(f"💸 Estimated cost for this comic: ~${actual_cost:.4f}")

    except Exception as e:
        st.error(f"Page assembly failed: {e}")
        raise
