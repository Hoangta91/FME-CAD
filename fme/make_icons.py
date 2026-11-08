#!/usr/bin/env python3
"""Sinh bo icon FME-CAD vao fme/assets/app-icon/ tu logo FME (hoac icon tam neu khong co logo).

Logo that cua FME: fme/assets/logo/ (nguon). Sinh icon:  python3 fme/make_icons.py --from-png fme/assets/logo/fme-logo.ico
(--no-plate: bo nen trang). Nen dung logo do phan giai cao (PNG >= 1024 px hoac SVG xuat PNG) de icon lon khong bi mo.
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


def from_logo(path, plate=True):
    """Logo bat ky (PNG/ICO, khong can vuong) -> icon 1024 vuong, giu ty le.
    plate=True: dat len nen trang bo goc de logo chu den van doc duoc tren thanh tac vu nen toi."""
    logo = Image.open(path)
    if logo.format == "ICO":                        # lay anh lon nhat trong file .ico
        logo.size = max(logo.info.get("sizes", [logo.size]))
    logo = logo.convert("RGBA")
    logo = logo.crop(logo.getbbox() or (0, 0, *logo.size))
    s = 1024
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    inner = s - 2 * (95 if plate else 20)
    k = inner / max(logo.size)
    logo = logo.resize((round(logo.width * k), round(logo.height * k)), Image.LANCZOS)
    if plate:
        ImageDraw.Draw(im).rounded_rectangle((48, 48, s - 48, s - 48), radius=200, fill=(255, 255, 255, 255))
    im.alpha_composite(logo, ((s - logo.width) // 2, (s - logo.height) // 2))
    return im


def main():
    brand = tomllib.load(open(os.path.join(HERE, "brand.toml"), "rb"))["brand"]
    os.makedirs(OUT, exist_ok=True)
    if "--from-png" in sys.argv:
        src = from_logo(sys.argv[sys.argv.index("--from-png") + 1], plate="--no-plate" not in sys.argv)
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
