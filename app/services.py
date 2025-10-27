import requests
import random

COUNTRY_API = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
EXCHANGE_API = "https://open.er-api.com/v6/latest/USD"


def fetch_countries():
    try:
        res = requests.get(COUNTRY_API, timeout=10)
        if res.status_code != 200:
            return None, "RestCountries API failed"
        return res.json(), None
    except Exception as e:
        return None, str(e)


def fetch_exchange_rates():
    try:
        res = requests.get(EXCHANGE_API, timeout=10)
        if res.status_code != 200:
            return None, "Exchange rate API failed"
        data = res.json()
        if data.get("result") != "success":
            return None, "Exchange rate API returned error"
        return data.get("rates", {}), None
    except Exception as e:
        return None, str(e)


def compute_gdp(population, exchange_rate):
    if not exchange_rate or exchange_rate == 0:
        return 0
    multiplier = random.randint(1000, 2000)
    return (population * multiplier) / exchange_rate
