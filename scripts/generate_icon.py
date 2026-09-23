"""Regenerate the multi-resolution Windows icon from the VISOR visual mark."""

from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    size = 512
    image = Image.new("RGBA", (size, size), (17, 25, 35, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((16, 16, 496, 496), radius=72, fill=(17, 25, 35, 255))
    for x in (144, 368):
        draw.line((x, 104, x, 408), fill=(41, 60, 80, 255), width=16)
    for y in (144, 368):
        draw.line((104, y, 408, y), fill=(41, 60, 80, 255), width=16)
    draw.ellipse((142, 142, 370, 370), fill=(27, 44, 60, 255), outline=(140, 184, 223, 255), width=20)
    draw.ellipse((206, 206, 306, 306), fill=(83, 198, 170, 255))
    nodes = ((144, 144), (368, 144), (144, 368), (368, 368))
    for x, y in nodes:
        draw.line((x, y, 220 if x < 256 else 292, 220 if y < 256 else 292), fill=(140, 184, 223, 255), width=10)
        draw.ellipse((x - 18, y - 18, x + 18, y + 18), fill=(227, 239, 249, 255))
    output = Path(__file__).resolve().parents[1] / "src" / "visor" / "assets" / "visor.ico"
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
