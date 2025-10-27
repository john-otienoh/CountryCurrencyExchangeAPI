# app/utils.py
import httpx
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import os

COUNTRIES_API = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
EXCHANGE_API = "https://open.er-api.com/v6/latest/USD"

DEFAULT_TIMEOUT = 10  # seconds, you can read from env if wanted

def fetch_countries(timeout=DEFAULT_TIMEOUT) -> List[dict]:
    with httpx.Client(timeout=timeout) as client:
        r = client.get(COUNTRIES_API)
        r.raise_for_status()
        return r.json()

def fetch_exchange_rates(timeout=DEFAULT_TIMEOUT) -> Dict[str, float]:
    with httpx.Client(timeout=timeout) as client:
        r = client.get(EXCHANGE_API)
        r.raise_for_status()
        data = r.json()
        # API returns rates in data['rates']
        rates = data.get("rates", {})
        return rates

def compute_estimated_gdp(population: int, exchange_rate: Optional[float]) -> Optional[float]:
    """
    estimated_gdp = population * rand(1000-2000) / exchange_rate
    If exchange_rate is None -> None (or 0 if spec says 0 for missing currency)
    Spec: If currencies empty -> estimated_gdp = 0
          If currency not found in rates -> estimated_gdp = null
    We'll let caller decide based on currency existence.
    """
    if exchange_rate is None or exchange_rate == 0:
        return None
    multiplier = random.uniform(1000, 2000)
    return population * multiplier / float(exchange_rate)

# Image generation: create cache/summary.png
def generate_summary_image(db, out_path: str, last_refreshed_at: datetime):
    """
    db: SQLAlchemy session
    out_path: path to save file (e.g. cache/summary.png)
    """
    from app import models
    # Query total
    total = db.query(models.Country).count()
    # top 5 by estimated_gdp (descending), ignoring nulls
    top5 = db.query(models.Country).filter(models.Country.estimated_gdp != None).order_by(models.Country.estimated_gdp.desc()).limit(5).all()

    # Create directory if not exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Basic image (800x600 white)
    W, H = 1000, 600
    background = (255, 255, 255)
    img = Image.new("RGB", (W, H), color=background)
    draw = ImageDraw.Draw(img)

    # You might want to bundle a TTF or use default fonts — try default
    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 18)
    except:
        font_title = ImageFont.load_default()
        font_small = ImageFont.load_default()

    title = "Countries summary"
    draw.text((20, 20), title, font=font_title, fill=(0, 0, 0))
    draw.text((20, 60), f"Total countries: {total}", font=font_small, fill=(0, 0, 0))
    draw.text((20, 90), f"Last refreshed: {last_refreshed_at.astimezone(timezone.utc).isoformat()}", font=font_small, fill=(0, 0, 0))

    # list top 5
    y = 140
    draw.text((20, y-20), "Top 5 countries by estimated GDP:", font=font_small, fill=(0,0,0))
    if top5:
        for c in top5:
            name = c.name
            gdp = f"{c.estimated_gdp:,.2f}" if c.estimated_gdp else "N/A"
            draw.text((30, y), f"{name} — {gdp}", font=font_small, fill=(0,0,0))
            y += 28
    else:
        draw.text((30, y), "No GDP data available", font=font_small, fill=(0,0,0))

    img.save(out_path)
    return out_path
