from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime

def generate_summary_image(total_countries, top5, last_refreshed):
    os.makedirs("cache", exist_ok=True)
    img = Image.new("RGB", (600, 400), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)

    title_font = ImageFont.load_default()
    text_font = ImageFont.load_default()

    draw.text((20, 20), "Country Currency Summary", font=title_font, fill=(255, 255, 255))
    draw.text((20, 60), f"Total Countries: {total_countries}", font=text_font, fill=(200, 200, 200))
    draw.text((20, 90), f"Last Refresh: {last_refreshed}", font=text_font, fill=(200, 200, 200))
    draw.text((20, 130), "Top 5 by Estimated GDP:", font=text_font, fill=(255, 215, 0))

    y = 160
    for idx, c in enumerate(top5, start=1):
        draw.text((40, y), f"{idx}. {c.name} - {round(c.estimated_gdp or 0, 2):,}", font=text_font, fill=(180, 180, 255))
        y += 25

    img_path = os.path.join("cache", "summary.png")
    img.save(img_path)
    return img_path
