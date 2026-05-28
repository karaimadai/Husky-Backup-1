from PIL import Image, ImageDraw, ImageFont, ImageColor
import os

# ─────────────────────────────────────────────────────────────────────────────
# FONT CANDIDATES  (first found wins)
# ─────────────────────────────────────────────────────────────────────────────
FONT_CANDIDATES_COMIC_SANS = [
    # Windows
    "C:/Windows/Fonts/comic.ttf",
    "C:/Windows/Fonts/comicbd.ttf",
    # macOS
    "/Library/Fonts/Comic Sans MS.ttf",
    "/Library/Fonts/Comic Sans MS Bold.ttf",
    # Linux fallbacks
    "/usr/share/fonts/truetype/msttcorefonts/Comic_Sans_MS.ttf",
    "/usr/share/fonts/truetype/msttcorefonts/comic.ttf",
    # Bundled in project
    "fonts/ComicSans.ttf",
    "fonts/comic.ttf",
]

FONT_CANDIDATES_DEFAULT = [
    "fonts/Bangers-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]

# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT CONSTANTS (fractions of image dimensions)
# ─────────────────────────────────────────────────────────────────────────────
BUBBLE_W_FRAC   = 0.92   # default bubble width (overridable via bubble_w_frac param)
BUBBLE_H_FRAC   = 0.22   # bubble height = at least 22% of image height
CAPTION_H_FRAC  = 0.12   # caption box   = at least 12% of image height
H_MARGIN_FRAC   = 0.04   # horizontal margin from image edge
V_MARGIN_FRAC   = 0.05   # vertical margin
TAIL_H_FRAC     = 0.06   # tail length   = 6% of image height
BORDER_W_FRAC   = 0.005  # border stroke width


def _load_font(size: int, use_comic_sans: bool = False) -> ImageFont.FreeTypeFont:
    candidates = FONT_CANDIDATES_COMIC_SANS if use_comic_sans else FONT_CANDIDATES_DEFAULT
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    # If comic sans requested but not found, fall through to default
    if use_comic_sans:
        for path in FONT_CANDIDATES_DEFAULT:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _measure_text(draw: ImageDraw.Draw, text: str, font) -> tuple:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap_text(text: str, font, draw: ImageDraw.Draw, max_width: int) -> list:
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        if _measure_text(draw, test, font)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _best_font_for_bubble(
    draw: ImageDraw.Draw,
    text: str,
    bubble_w: int,
    bubble_h: int,
    padding_x: int,
    padding_y: int,
    line_spacing: int,
    min_size: int = 18,
    max_size: int = 80,
    use_comic_sans: bool = False,
) -> tuple:
    max_text_w = bubble_w - padding_x * 2
    max_text_h = bubble_h - padding_y * 2
    best_font, best_lines = None, None

    for size in range(max_size, min_size - 1, -2):
        font  = _load_font(size, use_comic_sans=use_comic_sans)
        lines = _wrap_text(text, font, draw, max_text_w)
        lh    = _measure_text(draw, "Ay", font)[1]
        text_h = len(lines) * (lh + line_spacing) - line_spacing
        if text_h <= max_text_h:
            best_font  = font
            best_lines = lines
            break

    if best_font is None:
        best_font  = _load_font(min_size, use_comic_sans=use_comic_sans)
        best_lines = _wrap_text(text, best_font, draw, max_text_w)

    return best_font, best_lines


def _draw_speech_bubble(
    draw: ImageDraw.Draw,
    lines: list,
    font,
    img_width: int,
    img_height: int,
    position: str = "top",
    speaker: str = "left",
    top_offset: int = 0,
    bubble_w_frac: float = BUBBLE_W_FRAC,
    bubble_alpha: int = 230,           # 0=fully transparent, 255=fully opaque
) -> None:
    h_margin     = int(img_width  * H_MARGIN_FRAC)
    v_margin     = int(img_height * V_MARGIN_FRAC)
    tail_h       = int(img_height * TAIL_H_FRAC)
    padding_x    = int(img_width  * 0.04)
    padding_y    = int(img_height * 0.03)
    line_spacing = int(img_height * 0.012)
    radius       = int(min(img_width, img_height) * 0.04)
    border_w     = max(3, int(img_width * BORDER_W_FRAC))

    lh     = _measure_text(draw, "Ay", font)[1]
    text_h = len(lines) * (lh + line_spacing) - line_spacing

    bw = int(img_width * bubble_w_frac)
    bh = max(int(img_height * BUBBLE_H_FRAC), text_h + padding_y * 2)

    bx = (img_width - bw) // 2

    if position == "top":
        by = v_margin + top_offset
    else:
        by = img_height - bh - tail_h - v_margin

    bx = max(h_margin, min(bx, img_width  - bw - h_margin))
    by = max(v_margin, min(by, img_height - bh - tail_h - v_margin))

    # Bubble fill and outline colors (RGBA)
    fill_color    = (255, 255, 255, bubble_alpha)
    outline_color = (0, 0, 0, 255)

    # ── Tail ──────────────────────────────────────────────────────────────────
    tail_w  = int(bw * 0.10)
    tail_cx = (bx + int(bw * 0.22)) if speaker == "left" else (bx + int(bw * 0.78))

    tbl = tail_cx - tail_w // 2
    tbr = tail_cx + tail_w // 2
    ttx = tail_cx + (int(tail_w * 0.4) if speaker == "right" else -int(tail_w * 0.4))

    if position == "top":
        base_y = by + bh - 1
        tty    = min(base_y + tail_h, img_height - v_margin)
        tail_pts = [(tbl, base_y), (tbr, base_y), (ttx, tty)]
    else:
        base_y = by + 1
        tty    = max(base_y - tail_h, v_margin)
        tail_pts = [(tbl, base_y), (tbr, base_y), (ttx, tty)]

    ttx = max(h_margin, min(ttx, img_width - h_margin))
    tail_pts[2] = (ttx, tty)

    # ── Draw ──────────────────────────────────────────────────────────────────
    draw.polygon(tail_pts, fill=fill_color)
    draw.rounded_rectangle(
        [(bx, by), (bx + bw, by + bh)],
        radius=radius, fill=fill_color, outline=outline_color, width=border_w,
    )
    draw.line([tail_pts[0], tail_pts[2]], fill=outline_color, width=border_w)
    draw.line([tail_pts[1], tail_pts[2]], fill=outline_color, width=border_w)

    # ── Text ──────────────────────────────────────────────────────────────────
    ty = by + (bh - text_h) // 2
    stroke = max(1, border_w // 3)

    for line in lines:
        lw, _ = _measure_text(draw, line, font)
        tx = bx + (bw - lw) // 2
        # Thin stroke for legibility over transparent background
        for dx in range(-stroke, stroke + 1):
            for dy in range(-stroke, stroke + 1):
                if dx != 0 or dy != 0:
                    draw.text((tx + dx, ty + dy), line, fill=(255, 255, 255, 180), font=font)
        draw.text((tx, ty), line, fill=(15, 15, 15, 255), font=font)
        ty += lh + line_spacing


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def add_speech_bubble(
    image_path: str,
    dialogue: str,
    output_path: str,
    font_size: int = 26,
    position: str = "top",
    speaker: str = "left",
    top_offset: int = 0,
    use_comic_sans: bool = False,      # ← True when Minimalist style is active
    bubble_w_frac: float = BUBBLE_W_FRAC,  # ← 0.4–0.95 to shrink/grow bubble width
    bubble_alpha: int = 230,           # ← 0=transparent 255=opaque (default 230 = mostly opaque)
) -> str:
    img     = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    text = dialogue.strip().strip('"').strip("'").strip()
    if not text:
        img.convert("RGB").save(output_path, quality=95)
        return output_path

    W, H = img.width, img.height
    bw        = int(W * bubble_w_frac)
    bh        = int(H * BUBBLE_H_FRAC)
    padding_x = int(W * 0.04)
    padding_y = int(H * 0.03)
    line_spacing = int(H * 0.012)

    min_font = max(font_size, int(W * 0.030))
    font, lines = _best_font_for_bubble(
        draw, text,
        bubble_w=bw, bubble_h=bh,
        padding_x=padding_x, padding_y=padding_y,
        line_spacing=line_spacing,
        min_size=min_font, max_size=int(W * 0.10),
        use_comic_sans=use_comic_sans,
    )

    _draw_speech_bubble(
        draw, lines, font, W, H,
        position=position, speaker=speaker, top_offset=top_offset,
        bubble_w_frac=bubble_w_frac,
        bubble_alpha=bubble_alpha,
    )

    Image.alpha_composite(img, overlay).convert("RGB").save(output_path, quality=95)
    return output_path


def get_caption_box_height(image_path: str, font_size: int = 20) -> int:
    img  = Image.open(image_path)
    draw = ImageDraw.Draw(Image.new("RGBA", img.size))
    scaled = max(font_size, int(img.width * 0.026))
    font   = _load_font(scaled)
    lh     = _measure_text(draw, "Ay", font)[1]
    return max(int(img.height * CAPTION_H_FRAC), lh + int(img.height * 0.015) * 2)


def add_caption_box(
    image_path: str,
    caption: str,
    output_path: str,
    font_size: int = 20,
    color: str = "#FFF9C4",
    position: str = "top",
) -> str:
    img     = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    W, H = img.width, img.height
    scaled       = max(font_size, int(W * 0.026))
    font         = _load_font(scaled)
    h_pad        = int(W * 0.04)
    v_pad        = int(H * 0.015)
    line_spacing = int(H * 0.006)
    max_w        = W - h_pad * 2
    lines        = _wrap_text(caption.strip(), font, draw, max_w)

    lh     = _measure_text(draw, "Ay", font)[1]
    text_h = len(lines) * (lh + line_spacing) - line_spacing
    bh     = max(int(H * CAPTION_H_FRAC), text_h + v_pad * 2)

    rgb      = ImageColor.getrgb(color)
    fill     = rgb + (235,)
    border_w = max(2, int(W * 0.003))

    if position == "top":
        rect     = [(0, 0), (W, bh)]
        ty_start = (bh - text_h) // 2
    else:
        rect     = [(0, H - bh), (W, H)]
        ty_start = H - bh + (bh - text_h) // 2

    draw.rectangle(rect, fill=fill)
    draw.rectangle(rect, outline=(0, 0, 0, 220), width=border_w)

    ty = ty_start
    for line in lines:
        draw.text((h_pad, ty), line, fill=(15, 15, 15, 255), font=font)
        ty += lh + line_spacing

    Image.alpha_composite(img, overlay).convert("RGB").save(output_path, quality=95)
    return output_path

