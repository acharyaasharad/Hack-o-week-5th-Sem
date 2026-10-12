"""Weather service integrating Open-Meteo Forecast API with local caching and offline fallback.
Provides hourly future weather predictions for Tetouan or custom coordinates.
"""

from typing import Dict, Any, Optional, List
import time
import logging
import requests
import pandas as pd
import numpy as np

import config

logger = logging.getLogger(__name__)


class WeatherService:
    """Fetches Open-Meteo weather forecasts with in-memory caching and offline resilience."""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: float = 0.0
        self._cache_ttl: float = config.WEATHER_CACHE_TTL_SECONDS

    def get_forecast(
        self,
        latitude: float = config.DEFAULT_LATITUDE,
        longitude: float = config.DEFAULT_LONGITUDE,
        timezone: str = config.DEFAULT_TIMEZONE,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Retrieves hourly forecast from Open-Meteo API or fallback."""
        cache_key = f"{round(latitude, 3)}_{round(longitude, 3)}_{timezone}"
        now = time.time()

        if (
            not force_refresh
            and cache_key in self._cache
            and (now - self._cache_timestamp) < self._cache_ttl
        ):
            logger.info("Returning cached Open-Meteo weather forecast.")
            return self._cache[cache_key]

        # Attempt live API call
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m"],
            "timezone": timezone,
            "forecast_days": 3,
        }

        try:
            logger.info(f"Querying Open-Meteo API at {config.OPEN_METEO_BASE_URL} for lat={latitude}, lon={longitude}...")
            resp = requests.get(config.OPEN_METEO_BASE_URL, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                hourly = data.get("hourly", {})
                times = hourly.get("time", [])
                temps = hourly.get("temperature_2m", [])
                humids = hourly.get("relative_humidity_2m", [])
                winds = hourly.get("wind_speed_10m", [])

                weather_records = []
                for i in range(len(times)):
                    weather_records.append({
                        "DateTime": times[i].replace("T", " ") + (":00" if len(times[i]) == 13 else ""),
                        "Temperature": round(float(temps[i]), 1) if i < len(temps) else 20.0,
                        "Humidity": round(float(humids[i]), 1) if i < len(humids) else 60.0,
                        "WindSpeed": round(float(winds[i]), 1) if i < len(winds) else 2.5,
                    })

                result = {
                    "success": True,
                    "source": "Open-Meteo Forecast API (Live)",
                    "is_live": True,
                    "latitude": latitude,
                    "longitude": longitude,
                    "timezone": timezone,
                    "records_count": len(weather_records),
                    "forecast_records": weather_records,
                    "disclaimer": "Live weather forecast from Open-Meteo. Observations represent meteorological simulations.",
                }

                self._cache[cache_key] = result
                self._cache_timestamp = now
                return result

            else:
                logger.warning(f"Open-Meteo returned status {resp.status_code}: {resp.text}")

        except Exception as exc:
            logger.info(f"Open-Meteo API request failed or timed out: {exc}. Using calibrated offline fallback.")

        # Offline fallback
        fallback = self._generate_offline_fallback(latitude, longitude, timezone)
        self._cache[cache_key] = fallback
        self._cache_timestamp = now
        return fallback

    def _generate_offline_fallback(
        self,
        latitude: float,
        longitude: float,
        timezone: str,
        hours: int = 72,
    ) -> Dict[str, Any]:
        """Generates calibrated synthetic future weather observations when offline."""
        now = pd.Timestamp.now().floor("h")
        date_range = pd.date_range(start=now, periods=hours, freq="1h")

        np.random.seed(int(now.timestamp()) % 100000)
        h_vals = date_range.hour.values

        # Typical Mediterranean / Tetouan coastal climate pattern
        base_temp = 19.5 + 6.5 * np.sin(2 * np.pi * (h_vals - 9) / 24) + np.random.normal(0, 0.8, hours)
        base_humid = 65.0 - 18.0 * np.sin(2 * np.pi * (h_vals - 9) / 24) + np.random.normal(0, 2.0, hours)
        base_wind = np.abs(2.8 + 1.2 * np.sin(2 * np.pi * h_vals / 24) + np.random.normal(0, 0.6, hours))

        records = []
        for i, dt in enumerate(date_range):
            records.append({
                "DateTime": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "Temperature": round(float(base_temp[i]), 1),
                "Humidity": round(float(np.clip(base_humid[i], 25, 95)), 1),
                "WindSpeed": round(float(base_wind[i]), 1),
            })

        return {
            "success": True,
            "source": "Calibrated Offline Microclimate Model (Fallback)",
            "is_live": False,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "records_count": len(records),
            "forecast_records": records,
            "disclaimer": "Offline mode: Synthetic microclimate pattern calibrated for Tetouan geographic coordinates.",
        }
