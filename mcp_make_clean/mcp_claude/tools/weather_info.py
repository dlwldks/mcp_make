# tools/weather_info.py
# ─────────────────────────────────────────────────────────────
# 역할:
# - city 문자열 또는 (lat,lng)로 입력받아 → Google Geocoding(필요시)
#   → OpenWeather v2.5 (weather + forecast) 호출 → 요약 반환
# - 라우터에서 호출하는 함수 시그니처 유지:
#     - get_weather_summary(input_data)
#     - get_rainfall(input_data)
# - 반환은 구조화된 dict로 통일 (침수위험 계산에 바로 사용 가능)
# ─────────────────────────────────────────────────────────────

import time
import requests
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

# ─────────────────────────────────────────────────────────────
# 🔑 API Keys (.env 미사용 → 코드 상수)
# ─────────────────────────────────────────────────────────────
GOOGLE_GEOCODING_API_KEY = "AIzaSyAkPWGJi-XtTtz5D9Pt9sYmy4xcB9HuDtc"
OPENWEATHER_API_KEY      = "640c24f59616729fd42cff9972c93165"

# ─────────────────────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────────────────────
HTTP_TIMEOUT = 8
OW_UNITS = "metric"   # 섭씨/밀리미터
OW_LANG  = "kr"

# TTL 캐시
_GEOCODE_CACHE: Dict[str, Tuple[float, float, str, float]] = {}      # city -> (lat,lng,formatted,expires_at)
_WEATHER_CACHE: Dict[str, Tuple[Dict[str, Any], float]] = {}         # "lat,lng" -> (json,expires_at)
_FORECAST_CACHE: Dict[str, Tuple[Dict[str, Any], float]] = {}        # "lat,lng" -> (json,expires_at)
GEOCODE_TTL_SEC  = 3600 * 24   # 24h
WEATHER_TTL_SEC  = 60 * 1      # 1m (현재 날씨는 짧게)
FORECAST_TTL_SEC = 60 * 5      # 5m (예보는 조금 길게)

# ─────────────────────────────────────────────────────────────
# 내부 유틸
# ─────────────────────────────────────────────────────────────
def _get_attr(obj: Any, name: str) -> Any:
    """dict/객체 모두 대응되는 안전한 attr getter"""
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)

def _has_coords(obj: Any) -> bool:
    try:
        return (_get_attr(obj, "lat") is not None) and (_get_attr(obj, "lng") is not None)
    except Exception:
        return False

def _has_city(obj: Any) -> bool:
    city = _get_attr(obj, "city")
    return isinstance(city, str) and city.strip() != ""

# ─────────────────────────────────────────────────────────────
# 지오코딩 (Google)
# ─────────────────────────────────────────────────────────────
def _geocode_city(city: str) -> Optional[Tuple[float, float, str]]:
    """city -> (lat, lng, formatted_address) with TTL cache"""
    now = time.time()
    cached = _GEOCODE_CACHE.get(city)
    if cached and cached[3] > now:
        return (cached[0], cached[1], cached[2])

    params = urlencode({"address": city, "key": GOOGLE_GEOCODING_API_KEY, "language": "ko"})
    url = f"https://maps.googleapis.com/maps/api/geocode/json?{params}"
    r = requests.get(url, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    data = r.json()

    if data.get("status") != "OK" or not data.get("results"):
        return None

    result = data["results"][0]
    loc = result["geometry"]["location"]
    formatted = result.get("formatted_address") or city

    _GEOCODE_CACHE[city] = (loc["lat"], loc["lng"], formatted, now + GEOCODE_TTL_SEC)
    return (loc["lat"], loc["lng"], formatted)

# ─────────────────────────────────────────────────────────────
# OpenWeather v2.5: 현재 + 5일/3시간 예보
# ─────────────────────────────────────────────────────────────
def _fetch_weather_v25(lat: float, lng: float) -> Dict[str, Any]:
    """현재 날씨 /data/2.5/weather"""
    now = time.time()
    key = f"{lat:.5f},{lng:.5f}"
    cached = _WEATHER_CACHE.get(key)
    if cached and cached[1] > now:
        return cached[0]

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat, "lon": lng,
        "appid": OPENWEATHER_API_KEY,
        "units": OW_UNITS, "lang": OW_LANG
    }
    r = requests.get(url, params=params, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    _WEATHER_CACHE[key] = (data, now + WEATHER_TTL_SEC)
    return data

def _fetch_forecast_v25(lat: float, lng: float) -> Dict[str, Any]:
    """5일/3시간 예보 /data/2.5/forecast"""
    now = time.time()
    key = f"{lat:.5f},{lng:.5f}"
    cached = _FORECAST_CACHE.get(key)
    if cached and cached[1] > now:
        return cached[0]

    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat, "lon": lng,
        "appid": OPENWEATHER_API_KEY,
        "units": OW_UNITS, "lang": OW_LANG
    }
    r = requests.get(url, params=params, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    _FORECAST_CACHE[key] = (data, now + FORECAST_TTL_SEC)
    return data

def _summarize_v25(lat: float, lng: float) -> Dict[str, Any]:
    """
    v2.5 응답으로 요약값 생성
    - rain_mm_1h: 현재 weather.rain.1h (없으면 0)
    - rain_mm_3h: 근사값 = 현재 1h + (다음 3h 예보 / 3) * 2
      (즉 최근1h + 향후2h의 근사 합; 서비스 초기 운영에 유용)
    """
    cur = _fetch_weather_v25(lat, lng)
    fc  = {}
    try:
        fc = _fetch_forecast_v25(lat, lng)
    except Exception:
        # 예보 실패해도 서비스는 지속
        fc = {}

    # 현재 값
    main = cur.get("main") or {}
    wind = cur.get("wind") or {}
    weather_arr = cur.get("weather") or [{}]
    current_rain_1h = float((cur.get("rain") or {}).get("1h", 0.0) or 0.0)

    # 예보 첫 슬롯(3시간 강수 mm)
    fc_list = fc.get("list") or []
    fc_first_3h = float((fc_list[0].get("rain") or {}).get("3h", 0.0)) if fc_list else 0.0

    # 3시간 근사: 최근1h + 미래2h(3h 예보를 균등 분배 → 1h * 2)
    rain_3h_proxy = current_rain_1h + (fc_first_3h / 3.0) * 2.0

    return {
        "rain_mm_1h": current_rain_1h,
        "rain_mm_3h": float(rain_3h_proxy),
        "temp_c": main.get("temp"),
        "humidity": main.get("humidity"),
        "wind_speed": wind.get("speed"),
        "weather_desc": weather_arr[0].get("description"),
        "timestamp": cur.get("dt"),
    }

# ─────────────────────────────────────────────────────────────
# 공개 함수 (라우터에서 호출)
# ─────────────────────────────────────────────────────────────
def get_weather_summary(input_data: Any) -> Dict[str, Any]:
    """
    반환 예:
    {
      "region": "부산광역시 ...",
      "lat": 35.17,
      "lng": 129.07,
      "weather": { "rain_mm_1h": ..., "rain_mm_3h": ..., "temp_c": ..., ... }
    }
    """
    # 1) 좌표 모드
    if _has_coords(input_data):
        lat = float(_get_attr(input_data, "lat"))
        lng = float(_get_attr(input_data, "lng"))
        region = _get_attr(input_data, "city") or "Unknown"
        weather = _summarize_v25(lat, lng)
        return {"region": region, "lat": lat, "lng": lng, "weather": weather}

    # 2) 도시명 모드
    if _has_city(input_data):
        city = str(_get_attr(input_data, "city"))
        geo = _geocode_city(city)
        if not geo:
            raise ValueError(f"Geocoding failed for city='{city}'")
        lat, lng, formatted = geo
        weather = _summarize_v25(lat, lng)
        return {"region": formatted, "lat": lat, "lng": lng, "weather": weather}

    # 3) 어떤 모드도 아님 → 에러
    raise ValueError("get_weather_summary: need either city or (lat,lng)")

def get_rainfall(input_data: Any) -> Dict[str, Any]:
    """
    강수량만 요약해서 반환:
    { "region": "...", "lat": ..., "lng": ..., "rain_mm_1h": 0.5, "rain_mm_3h": 1.2 }
    """
    summary = get_weather_summary(input_data)
    w = summary.get("weather", {})
    return {
        "region": summary.get("region"),
        "lat": summary.get("lat"),
        "lng": summary.get("lng"),
        "rain_mm_1h": w.get("rain_mm_1h"),
        "rain_mm_3h": w.get("rain_mm_3h"),
    }
