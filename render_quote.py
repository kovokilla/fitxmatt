#!/usr/bin/env python3
"""Render a FitXMatt branded quote-card (1080x1350) from a text post.

Usage:
  render_quote.py "<hook line>" ["<sub line>" | ""] [out_path]
  Reads the post body, picks a punchy HOOK (first 1-2 sentences) + a SUB
  (the closing CTA line or a mid sentence), and draws a branded card.

Brand palette matches render_carousel.py.
"""
import sys, os, json
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FD = "/System/Library/Fonts"
REG, BOLD = os.path.join(FD, "Arial Unicode.ttf"), os.path.join(FD, "Helvetica.ttc")
W, H = 1080, 1350
BG, PANEL, ACCENT, ACCENT2, TEXT, MUTE = (
    (28, 38, 32), (38, 51, 43), (143, 188, 148),
    (212, 175, 110), (237, 240, 235), (150, 162, 154),
)


def font(sz, bold=False):
    try:
        return ImageFont.truetype(BOLD, sz, index=1) if bold else ImageFont.truetype(REG, sz)
    except Exception:
        return ImageFont.load_default()


def wrap(d, text, fnt, max_w):
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


def render(hook, sub, out):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # top accent bar
    d.rectangle([0, 0, W, 14], fill=ACCENT)
    # handle
    d.text((60, 70), "@fitxmatt", font=font(40, True), fill=ACCENT)
    # hook (largest), wrapped + grown
    hf = font(60, True)
    hmax = W - 120
    # shrink if very long
    while hf.size > 38 and d.textlength(hook, font=hf) > hmax and len(hook) > 40:
        hf = font(hf.size - 4, True)
    hlines = wrap(d, hook, hf, hmax)
    y = 300
    for ln in hlines:
        d.text((60, y), ln, font=hf, fill=TEXT)
        y += hf.size + 14
    # sub panel
    if sub:
        sf = font(34)
        smax = W - 160
        slines = wrap(d, sub, sf, smax)
        box_top = y + 60
        box_h = len(slines) * 46 + 60
        d.rounded_rectangle([60, box_top, W - 60, box_top + box_h], radius=24, fill=PANEL)
        yy = box_top + 30
        for ln in slines:
            d.text((90, yy), ln, font=sf, fill=MUTE)
            yy += 46
    # footer CTA
    d.text((60, H - 90), "👉 See the real results: lnkd.in/eu5djaTU", font=font(30), fill=ACCENT2)
    img.save(out)
    return out


def main():
    hook = sys.argv[1] if len(sys.argv) > 1 else "Your health is a system problem."
    sub = sys.argv[2] if len(sys.argv) > 2 else ""
    out = sys.argv[3] if len(sys.argv) > 3 else "/tmp/fitxmatt_quote.png"
    print(render(hook, sub, out))


if __name__ == "__main__":
    main()
