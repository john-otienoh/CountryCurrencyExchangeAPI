import os
import random
from datetime import datetime, timezone
import httpx
from typing import Tuple, List, Dict
from PIL import Image, ImageDraw, ImageFont
from config import RESTCOUNTRIES_URL, EXCHANGE_URL, CACHE_DIR
from repositories.country_exchange import upsert_country, top_n_by_gdp, total_and_last_refreshed


async def fetch_external() -> Tuple[List[dict], Dict[str, float]]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        r1 = await client.get(RESTCOUNTRIES_URL)
        if r1.status_code != 200:
            raise RuntimeError('countries_api')
        countries = r1.json()

        r2 = await client.get(EXCHANGE_URL)
        if r2.status_code != 200:
            raise RuntimeError('exchange_api')
        exchange = r2.json()
    return countries, exchange.get('rates', {})


def compute_estimated_gdp(population: int, exchange_rate: float) -> float:
    m = random.uniform(1000, 2000)
    return (population * m) / exchange_rate


async def process_and_save(countries: List[dict], rates: dict) -> None:
    now = datetime.now(timezone.utc)
    for c in countries:
        name = c.get('name')
        capital = c.get('capital')
        region = c.get('region')
        population = c.get('population') or 0
        flag = c.get('flag')
        currencies = c.get('currencies') or []

        if not name or population is None:
            continue

        if currencies and len(currencies)>0:
            currency_code = currencies[0].get('code')
        else:
            currency_code = None

        if currency_code:
            rate = rates.get(currency_code)
            if rate is None:
                exchange_rate = None
                estimated_gdp = None
            else:
                exchange_rate = float(rate)
                estimated_gdp = compute_estimated_gdp(population, exchange_rate) if exchange_rate != 0 else None
        else:
            exchange_rate = None
            estimated_gdp = 0

        payload = {
            'name': name,
            'capital': capital,
            'region': region,
            'population': population,
            'currency_code': currency_code,
            'exchange_rate': exchange_rate,
            'estimated_gdp': estimated_gdp,
            'flag_url': flag,
            'last_refreshed_at': now,
        }
        await upsert_country(payload)


async def generate_summary_image():
    os.makedirs(CACHE_DIR, exist_ok=True)
    stats = await total_and_last_refreshed()
    top5 = await top_n_by_gdp(5)
    path = os.path.join(CACHE_DIR, 'summary.png')

    w, h = 1200, 800
    img = Image.new('RGB', (w,h), color=(255,255,255))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('arial.ttf', 24)
    except Exception:
        font = ImageFont.load_default()
    d.text((40,40), f"Total countries: {stats['total']}", font=font)
    if stats['last']:
        d.text((40,80), f"Last refreshed at: {stats['last'].isoformat()}", font=font)
    d.text((40,130), 'Top 5 by estimated GDP:', font=font)
    y = 170
    for idx, c in enumerate(top5, start=1):
        d.text((60,y), f"{idx}. {c['name']} — {c.get('estimated_gdp')}", font=font)
        y += 40
    img.save(path)
    return path
