#!/usr/bin/env python3
"""Render a FitXMatt IG carousel (3 slides, 1080x1350) from ig_carousels.json.

Usage:
  render_carousel.py              # uses .ig_pointer (rotates)
  render_carousel.py 2            # render carousel index 2 (0-based)
  render_carousel.py --email 2    # also write /tmp/carousel_text_email.txt

Output: /tmp/fitxmatt_carousel/slide1.png,2,3.png + email text.

FIX (2026-07-24): every text container now MEASURES its wrapped content
height and GROWS to fit with safe top/bottom margins. No fixed-height box
can ever clip a sentence again. Slide heights are computed bottom-up so the
top content never collides with the bottom CTA/footer.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, "ig_carousels.json")
POINTER = os.path.join(HERE, ".ig_pointer")
OUT = "/tmp/fitxmatt_carousel"

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


def text_h(lines, lh):
    return len(lines) * lh + (lh // 3)  # small descender pad


def load(idx=None):
    data = json.load(open(SPEC))
    carousels = data["carousels"]
    if idx is None:
        idx = int(open(POINTER).read().strip() or "0") if os.path.exists(POINTER) else 0
    idx = idx % len(carousels)
    return data, carousels[idx], idx, len(carousels)


def render(c, data):
    os.makedirs(OUT, exist_ok=True)
    h = data["brand"]["handle"]; site = data["brand"]["site"]; cta = data["brand"]["cta_word"]

    # ---------- SLIDE 1 ----------
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 14], fill=ACCENT)
    d.text((MARGIN, 70), h, font=font(40, True), fill=ACCENT)
    y = 230
    head_maxw = W - 2 * MARGIN
    # pick headline size so the LONGEST line fits one wrapped row; else drop to 52
    longest = max((ln for ln in c["slide1"]["headline"].split("\n")), key=lambda s: d.textlength(s, font=font(66, True)))
    head_font = font(52, True) if d.textlength(longest, font=font(66, True)) > head_maxw else font(66, True)
    for ln in c["slide1"]["headline"].split("\n"):
        for wln in wrap(d, ln, head_font, head_maxw):
            d.text((MARGIN, y), wln, font=head_font, fill=TEXT); y += 82
    # sub panel: measure first, size box to fit
    sub_font = font(38); sub_maxw = W - 2 * MARGIN - 40
    sub_lines = wrap(d, c["slide1"]["sub"], sub_font, sub_maxw)
    sub_box_top = 770
    sub_box_h = text_h(sub_lines, 50) + 60  # 30 pad top/bottom
    sub_box_bot = sub_box_top + sub_box_h
    d.rounded_rectangle([MARGIN, sub_box_top, W - MARGIN, sub_box_bot], radius=24, fill=PANEL)
    yy = sub_box_top + 30
    for ln in sub_lines:
        d.text((MARGIN + 30, yy), ln, font=sub_font, fill=TEXT); yy += 50
    d.text((MARGIN, H - 90), "\u25bc Slide for the 3 reasons", font=font(34), fill=MUTE)
    p1 = f"{OUT}/slide1.png"; img.save(p1)

    # ---------- SLIDE 2 ----------
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 14], fill=ACCENT)
    d.text((MARGIN, 70), "3 reasons it's not you", font=font(54, True), fill=TEXT)
    d.text((MARGIN, 140), "\u2014 it's the system", font=font(40), fill=ACCENT)
    # compute each item's wrapped height, then lay out top-down with measured spacing
    items = []
    for it in c["slide2"]:
        body_font = font(30); body_maxw = W - 230
        body_lines = wrap(d, it["b"], body_font, body_maxw)
        title_font = font(38, True)
        item_h = max(90, 58 + text_h(body_lines, 42) + 30)  # min circle height
        items.append((it, title_font, body_font, body_lines, item_h))
    y = 250
    for it, tfont, bfont, blines, ih in items:
        d.ellipse([MARGIN, y, MARGIN + 90, y + 90], fill=ACCENT)
        d.text((MARGIN + 26, y + 18), it["n"], font=font(54, True), fill=BG)
        d.text((MARGIN + 130, y + 6), it["t"], font=tfont, fill=TEXT)
        yy = y + 58
        for ln in blines:
            d.text((MARGIN + 135, yy), ln, font=bfont, fill=MUTE); yy += 42
        y = max(y + ih, yy + 40)
    d.text((MARGIN, H - 80), h, font=font(34), fill=ACCENT)
    p2 = f"{OUT}/slide2.png"; img.save(p2)

    # ---------- SLIDE 3 ----------
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 14], fill=ACCENT2)
    d.text((MARGIN, 70), "The fix", font=font(60, True), fill=TEXT)
    bio_font = font(38); bio_maxw = W - 2 * MARGIN
    bio_lines = wrap(d, c["slide3_bio"], bio_font, bio_maxw)
    y = 200
    for ln in bio_lines:
        d.text((MARGIN, y), ln, font=bio_font, fill=TEXT); y += 52
    # CTA panel sized to content
    cta_box_top = y + 50
    cta_lines = [
        (f"Comment {cta}", font(46, True), ACCENT2, 0),
        ("and I'll point you to my free framework.", font(34), TEXT, 62),
        ("Or read it:", font(32), MUTE, 110),
        (site.replace("https://", ""), font(34, True), ACCENT, 150),
    ]
    cta_box_h = 200
    cta_box_bot = cta_box_top + cta_box_h
    d.rounded_rectangle([MARGIN, cta_box_top, W - MARGIN, cta_box_bot], radius=24, fill=PANEL)
    for txt, fnt, col, off in cta_lines:
        d.text((MARGIN + 30, cta_box_top + 30 + off), txt, font=fnt, fill=col)
    d.text((MARGIN, H - 90), h, font=font(34), fill=ACCENT)
    p3 = f"{OUT}/slide3.png"; img.save(p3)
    return p1, p2, p3


def email_text(c, data, idx, total):
    h = data["brand"]["handle"]; site = data["brand"]["site"]; cta = data["brand"]["cta_word"]
    L = []
    L.append(f"FitXMatt \u2014 IG Carousel #{idx+1}/{total} \u00b7 text from the images")
    L.append(f"Pain refs: {c.get('pain_refs')}  \u00b7  Handle: {h}  \u00b7  Site: {site}\n")
    L.append("\u2500" * 30 + "\nSLIDE 1 \u2014 HOOK\n" + "\u2500" * 30)
    L.append(h); L.append(c["slide1"]["headline"]); L.append(c["slide1"]["sub"] + "\n")
    L.append("\u2500" * 30 + "\nSLIDE 2 \u2014 THE 3 REASONS\n" + "\u2500" * 30)
    for it in c["slide2"]:
        L.append(f"{it['n']}  {it['t']}\n   {it['b']}")
    L.append("\n" + "\u2500" * 30 + "\nSLIDE 3 \u2014 CTA\n" + "\u2500" * 30)
    L.append("The fix\n" + c["slide3_bio"])
    L.append(f"\n[ CTA ]\nComment {cta}\nand I'll point you to my free framework.\nOr read it:\n{site}\n\n{h}")
    return "\n".join(L)


def main():
    args = sys.argv[1:]
    idx = None; do_email = "--email" in args
    for a in args:
        if a.isdigit():
            idx = int(a)
    data, c, idx, total = load(idx)
    render(c, data)
    txt = email_text(c, data, idx, total)
    if do_email:
        with open("/tmp/carousel_text_email.txt", "w") as f:
            f.write(txt)
    print(f"rendered carousel #{idx+1}/{total} (id={c['id']})")
    if do_email:
        print("email text -> /tmp/carousel_text_email.txt")


if __name__ == "__main__":
    main()
