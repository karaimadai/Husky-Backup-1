from PIL import Image, ImageDraw, ImageFont
import os

# ─────────────────────────────────────────────────────────────────────────────
# PAGE SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
PAGE_W = 1080
PAGE_H = 1560
GUTTER = 12
BORDER = 20
PANEL_BORDER_W = 4
TITLE_H = 44

BACKGROUND_COLOR   = (255, 255, 255)
GUTTER_COLOR       = (15, 15, 15)
PANEL_BORDER_COLOR = (0, 0, 0)
TITLE_BG_COLOR     = (10, 10, 10)
TITLE_TEXT_COLOR   = (255, 255, 255)

FONT_CANDIDATES = [
    "fonts/Bangers-Regular.ttf",
    "C:/Windows/Fonts/comic.ttf",
    "C:/Windows/Fonts/comicbd.ttf",
    "/Library/Fonts/Comic Sans MS.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
FONT_CANDIDATES_COMIC_SANS = [
    "C:/Windows/Fonts/comic.ttf",
    "C:/Windows/Fonts/comicbd.ttf",
    "/Library/Fonts/Comic Sans MS.ttf",
    "/usr/share/fonts/truetype/msttcorefonts/Comic_Sans_MS.ttf",
    "fonts/ComicSans.ttf",
] + FONT_CANDIDATES


def _load_font(size: int, comic_sans: bool = False) -> ImageFont.FreeTypeFont:
    candidates = FONT_CANDIDATES_COMIC_SANS if comic_sans else FONT_CANDIDATES
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _get_layout(n: int) -> list:
    layouts = {
        1: [1], 2: [1, 1], 3: [2, 1], 4: [2, 2],
        5: [2, 3], 6: [3, 3], 7: [2, 2, 3], 8: [2, 2, 2, 2],
    }
    if n in layouts:
        return layouts[n]
    rows, rem = [], n
    while rem > 0:
        c = min(2, rem)
        rows.append(c)
        rem -= c
    return rows


def _fit_panel(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    Contain-scale: shrink/grow the image so it fits ENTIRELY inside the cell
    (no cropping). Letterbox with white padding if aspect ratios differ.
    """
    sw, sh = img.size
    scale  = min(target_w / sw, target_h / sh)          # ← min = contain (was max = cover)
    nw     = int(sw * scale)
    nh     = int(sh * scale)
    img    = img.resize((nw, nh), Image.LANCZOS)

    # Paste centred on a white background the exact cell size
    canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
    left   = (target_w - nw) // 2
    top    = (target_h - nh) // 2
    canvas.paste(img, (left, top))
    return canvas


# ─────────────────────────────────────────────────────────────────────────────
# SPEECH BUBBLE — drawn directly on the assembled page at cell scale
# ─────────────────────────────────────────────────────────────────────────────

def _measure(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1]


def _wrap(text, font, draw, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if _measure(draw, test, font)[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _best_font(draw, text, bw, bh, px, py, ls, min_s, max_s, comic_sans):
    max_tw = bw - px * 2
    max_th = bh - py * 2
    for sz in range(max_s, min_s - 1, -2):
        f  = _load_font(sz, comic_sans)
        ln = _wrap(text, f, draw, max_tw)
        lh = _measure(draw, "Ay", f)[1]
        if len(ln) * (lh + ls) - ls <= max_th:
            return f, ln
    f = _load_font(min_s, comic_sans)
    return f, _wrap(text, f, draw, max_tw)


def _draw_bubble_on_page(
    page, text,
    cell_x, cell_y, cell_w, cell_h,
    position="top", speaker="left",
    top_offset=0, caption_h=0,
    bubble_w_frac=0.82,
    bubble_alpha=220,
    comic_sans=False,
):
    """
    Draw a speech bubble directly on `page` (RGBA Image) within the cell area.
    Every dimension is relative to (cell_w, cell_h) — completely independent
    of the source panel image dimensions.
    """
    text = text.strip().strip('"').strip("'")
    if not text:
        return

    draw = ImageDraw.Draw(page)

    # ── Cell-relative sizing ──────────────────────────────────────────────────
    bw       = int(cell_w * bubble_w_frac)
    bh       = max(int(cell_h * 0.22), int(cell_h * 0.15))
    px       = int(cell_w * 0.04)
    py       = int(cell_h * 0.025)
    ls       = int(cell_h * 0.01)
    radius   = int(min(cell_w, cell_h) * 0.035)
    border_w = max(2, int(cell_w * 0.004))
    tail_h   = int(cell_h * 0.07)
    v_margin = int(cell_h * 0.03)
    h_margin = int(cell_w * 0.04)

    min_font = max(14, int(cell_w * 0.028))
    max_font = int(cell_w * 0.09)
    font, lines = _best_font(draw, text, bw, bh, px, py, ls, min_font, max_font, comic_sans)

    lh     = _measure(draw, "Ay", font)[1]
    text_h = len(lines) * (lh + ls) - ls
    bh     = max(bh, text_h + py * 2)

    # Bubble top-left in PAGE coordinates
    bx = cell_x + (cell_w - bw) // 2
    bx = max(cell_x + h_margin, min(bx, cell_x + cell_w - bw - h_margin))

    if position == "top":
        by = cell_y + v_margin + top_offset + caption_h
    else:
        by = cell_y + cell_h - bh - tail_h - v_margin

    by = max(cell_y + v_margin, min(by, cell_y + cell_h - bh - tail_h - v_margin))

    # ── Tail ──────────────────────────────────────────────────────────────────
    tail_w  = int(bw * 0.10)
    tail_cx = (bx + int(bw * 0.22)) if speaker == "left" else (bx + int(bw * 0.78))
    tbl, tbr = tail_cx - tail_w // 2, tail_cx + tail_w // 2
    ttx = tail_cx + (int(tail_w * 0.4) if speaker == "right" else -int(tail_w * 0.4))
    ttx = max(cell_x + h_margin, min(ttx, cell_x + cell_w - h_margin))

    fill    = (255, 255, 255, bubble_alpha)
    outline = (0, 0, 0, 255)

    if position == "top":
        base_y   = by + bh - 1
        tty      = min(base_y + tail_h, cell_y + cell_h - v_margin)
        tail_pts = [(tbl, base_y), (tbr, base_y), (ttx, tty)]
    else:
        base_y   = by + 1
        tty      = max(base_y - tail_h, cell_y + v_margin)
        tail_pts = [(tbl, base_y), (tbr, base_y), (ttx, tty)]

    draw.polygon(tail_pts, fill=fill)
    draw.rounded_rectangle(
        [(bx, by), (bx + bw, by + bh)],
        radius=radius, fill=fill, outline=outline, width=border_w,
    )
    draw.line([tail_pts[0], tail_pts[2]], fill=outline, width=border_w)
    draw.line([tail_pts[1], tail_pts[2]], fill=outline, width=border_w)

    # ── Text ──────────────────────────────────────────────────────────────────
    ty     = by + (bh - text_h) // 2
    stroke = max(1, border_w // 3)
    for line in lines:
        lw, _ = _measure(draw, line, font)
        tx = bx + (bw - lw) // 2
        for dx in range(-stroke, stroke + 1):
            for dy in range(-stroke, stroke + 1):
                if dx or dy:
                    draw.text((tx + dx, ty + dy), line, fill=(255, 255, 255, 160), font=font)
        draw.text((tx, ty), line, fill=(10, 10, 10, 255), font=font)
        ty += lh + ls


def _draw_caption_on_page(
    page, text,
    cell_x, cell_y, cell_w, cell_h,
    comic_sans=False,
) -> int:
    """Draw narrator caption bar at top of cell. Returns its pixel height."""
    text = text.strip()
    if not text:
        return 0

    draw    = ImageDraw.Draw(page)
    font_sz = max(12, int(cell_w * 0.026))
    font    = _load_font(font_sz, comic_sans)
    h_pad   = int(cell_w * 0.04)
    v_pad   = int(cell_h * 0.015)
    ls      = int(cell_h * 0.006)
    max_w   = cell_w - h_pad * 2
    lines   = _wrap(text, font, draw, max_w)
    lh      = _measure(draw, "Ay", font)[1]
    text_h  = len(lines) * (lh + ls) - ls
    bh      = max(int(cell_h * 0.10), text_h + v_pad * 2)

    fill     = (255, 249, 196, 235)
    border_w = max(2, int(cell_w * 0.003))

    draw.rectangle(
        [(cell_x, cell_y), (cell_x + cell_w, cell_y + bh)],
        fill=fill,
    )
    draw.rectangle(
        [(cell_x, cell_y), (cell_x + cell_w, cell_y + bh)],
        outline=(0, 0, 0), width=border_w,
    )
    ty = cell_y + (bh - text_h) // 2
    for line in lines:
        draw.text((cell_x + h_pad, ty), line, fill=(15, 15, 15), font=font)
        ty += lh + ls

    return bh


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def create_comic_page(
    panel_paths: list,
    output: str = "outputs/final_comic.png",
    title: str = "",
    panel_data: list = None,
    bubble_cfg: dict = None,
) -> str:
    """
    Assemble panel images into a comic page and draw speech bubbles + captions
    directly on the assembled page at the correct cell scale.

    panel_paths : list of raw panel PNG paths (no bubbles pre-drawn)
    output      : destination PNG path
    title       : optional title banner text
    panel_data  : list of panel dicts {'dialogue', 'caption', 'emotion'}
    bubble_cfg  : {
        'alternate_position': bool,
        'show_captions': bool,
        'comic_sans': bool,
        'bubble_w_frac': float,
        'bubble_alpha': int,
    }
    """
    if not panel_paths:
        raise ValueError("No panel paths provided.")

    cfg        = bubble_cfg or {}
    alternate  = cfg.get("alternate_position", True)
    show_caps  = cfg.get("show_captions", True)
    comic_sans = cfg.get("comic_sans", False)
    bw_frac    = cfg.get("bubble_w_frac", 0.82)
    b_alpha    = cfg.get("bubble_alpha", 220)

    layout  = _get_layout(len(panel_paths))
    n_rows  = len(layout)

    has_title   = bool(title)
    title_space = TITLE_H + GUTTER if has_title else 0

    usable_w = PAGE_W - 2 * BORDER
    usable_h = PAGE_H - 2 * BORDER - title_space
    row_h    = (usable_h - GUTTER * (n_rows - 1)) // n_rows

    # Use RGBA throughout so we can draw semi-transparent bubbles
    page = Image.new("RGBA", (PAGE_W, PAGE_H), GUTTER_COLOR + (255,))
    page.paste(
        Image.new("RGBA", (usable_w, usable_h), BACKGROUND_COLOR + (255,)),
        (BORDER, BORDER + title_space),
    )

    cell_positions = []   # (inner_x, inner_y, inner_w, inner_h) per panel

    panel_idx = 0
    y = BORDER + title_space

    for n_cols in layout:
        if panel_idx >= len(panel_paths):
            break
        col_w = (usable_w - GUTTER * (n_cols - 1)) // n_cols
        x     = BORDER

        for col in range(n_cols):
            if panel_idx >= len(panel_paths):
                break

            inner_x = x + PANEL_BORDER_W
            inner_y = y + PANEL_BORDER_W
            inner_w = col_w - PANEL_BORDER_W * 2
            inner_h = row_h - PANEL_BORDER_W * 2

            # Panel border
            draw = ImageDraw.Draw(page)
            draw.rectangle(
                [(x, y), (x + col_w, y + row_h)],
                outline=PANEL_BORDER_COLOR, width=PANEL_BORDER_W,
            )

            # Place panel image (cover-scale + crop)
            try:
                pimg = Image.open(panel_paths[panel_idx]).convert("RGBA")
                pimg = _fit_panel(pimg.convert("RGB"), inner_w, inner_h).convert("RGBA")
                page.paste(pimg, (inner_x, inner_y))
            except Exception as e:
                print(f"  [Layout] Warning: {panel_paths[panel_idx]}: {e}")
                ph = Image.new("RGBA", (inner_w, inner_h), (200, 200, 210, 255))
                page.paste(ph, (inner_x, inner_y))

            cell_positions.append((inner_x, inner_y, inner_w, inner_h))
            x         += col_w + GUTTER
            panel_idx += 1

        y += row_h + GUTTER

    # ── Title bar ─────────────────────────────────────────────────────────────
    if has_title:
        draw = ImageDraw.Draw(page)
        draw.rectangle(
            [(BORDER, BORDER), (PAGE_W - BORDER, BORDER + TITLE_H)],
            fill=TITLE_BG_COLOR,
        )
        draw.text(
            (PAGE_W // 2, BORDER + TITLE_H // 2),
            title.upper(),
            fill=TITLE_TEXT_COLOR,
            font=_load_font(30),
            anchor="mm",
        )

    # ── Draw speech bubbles & captions at cell scale ──────────────────────────
    # Bubbles are sized relative to each cell — not the source image.
    # A 4-panel layout produces cells of ~(502x374)px on a 1080x1560 page,
    # so a 65%-wide bubble = 326px — always proportionate regardless of how
    # many panels are on the page.
    if panel_data:
        for idx, (cx, cy, cw, ch) in enumerate(cell_positions):
            if idx >= len(panel_data):
                break
            panel    = panel_data[idx]
            dialogue = panel.get("dialogue", "").strip()
            caption  = panel.get("caption",  "").strip()
            position = ("top" if idx % 2 == 0 else "bottom") if alternate else "top"
            speaker  = "left" if idx % 2 == 0 else "right"

            cap_h = 0
            if show_caps and caption:
                cap_h = _draw_caption_on_page(
                    page, caption, cx, cy, cw, ch, comic_sans=comic_sans
                )

            if dialogue:
                _draw_bubble_on_page(
                    page, dialogue,
                    cell_x=cx, cell_y=cy,
                    cell_w=cw, cell_h=ch,
                    position=position,
                    speaker=speaker,
                    top_offset=0,
                    caption_h=cap_h if position == "top" else 0,
                    bubble_w_frac=bw_frac,
                    bubble_alpha=b_alpha,
                    comic_sans=comic_sans,
                )

    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)
    page.convert("RGB").save(output, quality=95)
    print(f"[Layout] Comic page saved → {output}  ({PAGE_W}×{PAGE_H}px)")
    return output
