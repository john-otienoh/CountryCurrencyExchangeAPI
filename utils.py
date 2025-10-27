import requests, random, os
from PIL import Image, ImageDraw
from datetime import datetime

def fetch_countries():
    url = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
    res = requests.get(url, timeout=10)
    res.raise_for_status()
    return res.json()

def fetch_exchange_rates():
    url = "https://open.er-api.com/v6/latest/USD"
    res = requests.get(url, timeout=10)
    res.raise_for_status()
    return res.json()["rates"]

def compute_estimated_gdp(population, exchange_rate):
    if not exchange_rate or exchange_rate == 0:
        return 0
    multiplier = random.randint(1000, 2000)
    return (population * multiplier) / exchange_rate

def generate_summary_image(countries):
    top5 = sorted(countries, key=lambda x: x.estimated_gdp or 0, reverse=True)[:5]
    img = Image.new("RGB", (600, 400), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), f"Total Countries: {len(countries)}", fill="black")
    draw.text((20, 50), f"Last Refresh: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}", fill="black")
    y = 100
    for c in top5:
        draw.text((20, y), f"{c.name}: {round(c.estimated_gdp or 0, 2)}", fill="blue")
        y += 40
    os.makedirs("cache", exist_ok=True)
    img.save("cache/summary.png")

