from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    out = Path("examples/demo_bundle/regional_chart.png")
    image = Image.new("RGB", (900, 500), "white")
    draw = ImageDraw.Draw(image)
    draw.text((35, 25), "Regional change (Q3 2026)", fill="#172033")
    baseline = 350
    values = [("North", -10), ("South", 4), ("West", -7)]
    for index, (label, value) in enumerate(values):
        x = 150 + index * 220
        height = abs(value) * 16
        top = baseline if value < 0 else baseline - height
        bottom = baseline + height if value < 0 else baseline
        draw.rectangle((x, top, x + 90, bottom), fill="#3157d5" if value >= 0 else "#e07a5f")
        draw.text((x, 390), label, fill="#172033")
        draw.text((x + 20, top - 25 if value >= 0 else bottom + 8), f"{value}%", fill="#172033")
    draw.line((80, baseline, 820, baseline), fill="#667085", width=2)
    image.save(out)


if __name__ == "__main__":
    main()
