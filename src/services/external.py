import httpx
from typing import Dict, List, Optional, Tuple
import random
from dotenv import load_dotenv
import os

load_dotenv()

REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", 10))
COUNTRIES_API_URL = os.getenv("COUNTRIES_API_URL")
EXCHANGE_RATE_API_URL = os.getenv("EXCHANGE_RATE_API_URL")


class ExternalAPIService:
    """Service for fetching data from external APIs"""

    @staticmethod
    async def fetch_countries() -> List[Dict]:
        """
        Fetch country data from restcountries.com API

        Returns:
            List of country dictionaries

        Raises:
            httpx.HTTPError: If API request fails
        """
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.get(COUNTRIES_API_URL)
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:

            return None
        except httpx.HTTPStatusError as e:

            return None

    @staticmethod
    async def fetch_exchange_rates() -> Dict[str, float]:
        """
        Fetch exchange rates from open.er-api.com

        Returns:
            Dictionary mapping currency codes to exchange rates

        Raises:
            httpx.HTTPError: If API request fails
        """
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(EXCHANGE_RATE_API_URL)
            response.raise_for_status()
            data = response.json()
            return data.get("rates", {})

    @staticmethod
    def extract_currency_code(currencies: List[Dict]) -> Optional[str]:
        """
        Extract the first currency code from currencies array

        Args:
            currencies: List of currency dictionaries

        Returns:
            First currency code or None if empty
        """
        if not currencies or len(currencies) == 0:
            return None

        first_currency = currencies[0]
        return first_currency.get("code")

    @staticmethod
    def calculate_gdp(
        population: int, exchange_rate: Optional[float]
    ) -> Optional[float]:
        """
        Calculate estimated GDP using the formula:
        estimated_gdp = population × random(1000–2000) ÷ exchange_rate

        Args:
            population: Country population
            exchange_rate: Exchange rate for country's currency

        Returns:
            Calculated GDP or None if exchange_rate is None
        """
        if exchange_rate is None or exchange_rate == 0:
            return None

        random_multiplier = random.uniform(1000, 2000)
        estimated_gdp = (population * random_multiplier) / exchange_rate
        return round(estimated_gdp, 2)

    @staticmethod
    async def fetch_all_data() -> Tuple[List[Dict], Dict[str, float]]:
        """
        Fetch both countries and exchange rates concurrently

        Returns:
            Tuple of (countries_list, exchange_rates_dict)

        Raises:
            httpx.HTTPError: If either API request fails
        """
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                countries_response, rates_response = await client.get(
                    COUNTRIES_API_URL
                ), await client.get(EXCHANGE_RATE_API_URL)

            countries_response.raise_for_status()
            rates_response.raise_for_status()

            countries = countries_response.json()
            rates = rates_response.json().get("rates", {})

            return countries, rates
        except httpx.HTTPStatusError as e:

            raise
        except httpx.TimeoutException as e:

            raise
        except Exception as e:

            raise httpx.HTTPError("Unexpected error") from e
