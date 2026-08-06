#!/usr/bin/env python3
"""Render a FitXMatt text carousel (3 prose slides, 1080x1350) from
ig_text_carousels.json. Each slide is a prose block that GROWS to fit.

Usage:
  render_text_carousel.py            # uses .ig_text_pointer (rotates)
  render_text_carousel.py 2          # render index 2 (0-based)
Output: /tmp/fitxmatt_text_carousel/slide1.png,2,3.png
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, "ig_text_carousels.json")
POINTER = os.path.join(HERE, ".ig_text_pointer")
OUT = "/tmp/fitxmatt_text_carousel"

W, H = 1080, 1350
MARGIN = 60
BG, PANEL, ACCENT, ACCENT2, TEXT, MUTE = (
    (28, 38, 32), (38, 51, 43), (143, 188, 148),
    (212, 175, 110), (237, 240, 235), (150, 162, 154),
)
FD = "/System/Library/Fonts"
REG, BOLD = os.path.join(FD, "Arial Unicode.ttf"), os.path.join(FD, "Helvetica.ttc")


def font(sz, bold=False):
    try:
        return ImageFont.truetype(BOLD, sz, index=1) if bold else ImageFont.truetype(REG, sz)
    except Exception:
        try:
            return ImageFont.truetype(BOLD, sz, index=0)
        except Exception:
            return ImageFont.load_default()


def clean(text):
    """Normalize Unicode that the font can't render (boxes) to ASCII."""
    return (text.replace("\u2014", "-").replace("\u2013", "-")
                .replace("\u2026", "...")
                .replace("\u2018", "'").replace("\u2019", "'")
                .replace("\u201c", '"').replace("\u201d", '"')
                .replace("\u25b6", "\u2192").replace("\ufe0f", ""))  # ▶/emoji -> ->


def wrap(d, text, fnt, max_w):
    text = clean(text)
    words, cur, lines = text.split(), "", []
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_h(lines, lh):
    return len(lines) * lh + (lh // 3)


def load(idx=None):
    data = json.load(open(SPEC))
    carousels = data["carousels"]
    if idx is None:
        idx = int(open(POINTER).read().strip() or "0") if os.path.exists(POINTER) else 0
    idx = idx % len(carousels)
    return data, carousels[idx], idx, len(carousels)


def render_prose(img, d, handle, body, cta_color, footer):
    """Render a prose slide: handle, wrapped body that GROWS to fit, footer.
    Guarantees body ends above the footer (never clipped)."""
    d.rectangle([0, 0, W, 14], fill=cta_color)
    d.text((MARGIN, 70), handle, font=font(40, True), fill=ACCENT)
    maxw = W - 2 * MARGIN
    top = 210
    footer_y = H - 70
    # pick the LARGEST font size that fits the body between top and footer
    bfont = font(42)
    while bfont.size >= 24:
        blines = wrap(d, body, bfont, maxw)
        lh = bfont.size + 12
        if top + text_h(blines, lh) + 30 <= footer_y:
            break
        bfont = font(bfont.size - 2)
    blines = wrap(d, body, bfont, maxw)
    lh = bfont.size + 12
    y = top
    for ln in blines:
        d.text((MARGIN, y), ln, font=bfont, fill=TEXT); y += lh
    d.text((MARGIN, footer_y), footer, font=font(32), fill=MUTE)
    return img


def render(c, data):
    os.makedirs(OUT, exist_ok=True)
    h = data["brand"]["handle"]
    cta = data["brand"].get("cta_word", "SYSTEM")
    # SLIDE 1 - hook
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    render_prose(img, d, h, c["slide1"], ACCENT, "-> Slide 2 for the insight")
    p1 = f"{OUT}/slide1.png"; img.save(p1)
    # SLIDE 2 - insight
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    render_prose(img, d, h, c["slide2"], ACCENT, "-> Slide 3 for the fix")
    p2 = f"{OUT}/slide2.png"; img.save(p2)
    # SLIDE 3 - payoff + CTA (NO external URL - IG only)
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    s3 = c["slide3"]
    cta_block = f"\n\nComment {cta} and I'll send you my free framework."
    render_prose(img, d, h, s3 + cta_block, ACCENT2, h)
    p3 = f"{OUT}/slide3.png"; img.save(p3)
    return p1, p2, p3


def main():
    args = sys.argv[1:]
    idx = None
    for a in args:
        if a.isdigit():
            idx = int(a)
    data, c, idx, total = load(idx)
    p1, p2, p3 = render(c, data)
    print(f"rendered text carousel #{idx+1}/{total} (id={c['id']}) -> {p1}")


if __name__ == "__main__":
    main()
