#!/usr/bin/env python3
"""Sinh bo icon TAM THOI cho FME-CAD vao fme/assets/app-icon/ (chu "FME" tren nen mau nhan dien).

Khi co logo that: thay fme/assets/app-icon/fme-1024.png bang logo 1024x1024 roi chay lai voi --from-png.
Can Pillow:  pip install pillow
    python3 fme/make_icons.py                 # icon tam
    python3 fme/make_icons.py --from-png logo.png
"""
import os, sys, tomllib
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets", "app-icon")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
HICOLOR = [16, 24, 32, 48, 64, 128, 256, 512]


def placeholder(accent):
    s = 1024
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((64, 64, s - 64, s - 64), radius=180, fill=tuple(accent) + (255,))
    # luoi ky thuat mo
    for i in range(1, 8):
        x = 64 + i * (s - 128) // 8
        d.line((x, 120, x, s - 120), fill=(255, 255, 255, 40), width=4)
        d.line((120, x, s - 120, x), fill=(255, 255, 255, 40), width=4)
    f1 = ImageFont.truetype(FONT, 300)
    f2 = ImageFont.truetype(FONT, 150)
    d.text((s / 2, s / 2 - 60), "FME", font=f1, fill="white", anchor="mm")
    d.text((s / 2, s / 2 + 200), "CAD", font=f2, fill=(255, 255, 255, 220), anchor="mm")
    return im


def main():
    brand = tomllib.load(open(os.path.join(HERE, "brand.toml"), "rb"))["brand"]
    os.makedirs(OUT, exist_ok=True)
    if "--from-png" in sys.argv:
        src = Image.open(sys.argv[sys.argv.index("--from-png") + 1]).convert("RGBA").resize((1024, 1024), Image.LANCZOS)
    else:
        src = placeholder(brand["accent"])
    src.save(os.path.join(OUT, "fme-1024.png"))
    for size, name in [(256, "fme-256.png"), (64, "fme-64.png"), (512, "fme-macos-512.png")]:
        src.resize((size, size), Image.LANCZOS).save(os.path.join(OUT, name))
    for size in HICOLOR:
        src.resize((size, size), Image.LANCZOS).save(os.path.join(OUT, f"hicolor-{size}.png"))
    src.save(os.path.join(OUT, "fme.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    src.save(os.path.join(OUT, "fme.icns"))
    print("icons ->", OUT)


if __name__ == "__main__":
    main()
