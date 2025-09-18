# tools/flood_checker.py
"""
🌊 Flood Checker Tool (실데이터 기반, OpenWeather v2.5 사용)
- 역할:
  1) 실시간 강수량(OpenWeather) + 지면고도(Google Elevation) API를 이용해 침수 위험을 평가
  2) 3시간 강수량 중심의 rule 기반 평가 + 저고도 보정
- 의존:
  - tools.weather_info.get_weather_summary(input)  # city 또는 (lat,lng) 입력 지원
  - tools.elevation.get_ground_level(lat, lng)    # meters
- 반환:
  {
    "region": str,
    "lat": float, "lng": float,
    "weather": {
        "rain_mm_1h": float,
        "rain_mm_3h": float,
        "rain_mm_3h_used": float,   # ✅ 실제 계산에 사용한 값
        "rain_3h_source": "api_v2_5" | "override_param",
        "temp_c": float,
        "humidity": float,
        "wind_speed": float,
        "weather_desc": str,
        "timestamp": int
    },
    "elevation_m": float,
    "risk": { "level": "낮음|보통|높음", "score": float, "factors": [str, ...] },
    "explanations": [str, ...]
  }
"""

from typing import Optional, Dict, Any, List
import math

from tools.weather_info import get_weather_summary
from tools.elevation import get_ground_level


# ─────────────────────────────────────────────────────────────
# 내부 규칙: 3시간 강수량 기반 base score + 저고도 보정
# ─────────────────────────────────────────────────────────────
def _risk_score_from_rain_3h(rain_mm_3h: float) -> float:
    """
    3시간 누적 강수량을 [0,1] 스코어로 매핑.
    - 0mm → 0.0
    - 20mm → 1.0 (상한 클램프)
    """
    if rain_mm_3h is None:
        return 0.0
    return max(0.0, min(1.0, float(rain_mm_3h) / 20.0))


def _apply_low_elevation_boost(score: float, elevation_m: Optional[float]) -> float:
    """
    고도가 5m 미만이면 위험도 +0.15 가산 (최대 1.0)
    """
    if elevation_m is None:
        return score
    if elevation_m < 5.0:
        score += 0.15
    return min(score, 1.0)


def _score_to_level(score: float) -> str:
    if score < 0.2:
        return "낮음"
    elif score < 0.6:
        return "보통"
    else:
        return "높음"


# ─────────────────────────────────────────────────────────────
# 공개 함수
# ─────────────────────────────────────────────────────────────
def predict_flood_risk(
    lat: float,
    lng: float,
    rainfall: Optional[float] = None,   # ⬅ override 값(mm/3h). 있으면 우선 사용
    city: Optional[str] = None,
    elevation_override: Optional[float] = None
) -> Dict[str, Any]:
    """
    침수 위험 평가 실행
    - lat/lng는 필수
    - rainfall이 None이면 weather_summary에서 추정한 3h 강수량 사용
    - elevation_override가 없으면 Google Elevation API로 조회
    """
    try:
        # 1) 날씨 요약 확보
        weather_summary = get_weather_summary({"lat": lat, "lng": lng, "city": city})
        region = weather_summary.get("region") or (city or "Unknown")
        weather = weather_summary.get("weather", {})

        rain_1h = float(weather.get("rain_mm_1h") or 0.0)
        rain_3h_auto = float(weather.get("rain_mm_3h") or 0.0)

        # 2) 실제 계산에 사용할 3h 강수량 결정
        if rainfall is not None:
            rain_3h_used = float(rainfall)
            rain_3h_source = "override_param"
        else:
            rain_3h_used = rain_3h_auto
            rain_3h_source = "api_v2_5"

        # 3) 고도 확보
        elevation_m = elevation_override if elevation_override is not None else get_ground_level(lat, lng)

        # 4) 스코어/레벨 산정
        base = _risk_score_from_rain_3h(rain_3h_used)
        score = _apply_low_elevation_boost(base, elevation_m)
        level = _score_to_level(score)

        # 5) 설명 요소 구성
        factors: List[str] = [f"3시간 강수량 {rain_3h_used:.1f}mm"]
        explanations: List[str] = [
            "OpenWeather v2.5(weather/forecast) 기반 3시간 강수량 사용" if rainfall is None
            else "요청 파라미터(rainfall)로 3시간 강수량 오버라이드 사용"
        ]
        if elevation_m is not None and elevation_m < 5.0:
            factors.append(f"저고도({elevation_m:.1f}m) 보정")
            explanations.append("고도 5m 미만 구간에 위험도 보정(+0.15) 적용")

        return {
            "region": region,
            "lat": lat,
            "lng": lng,
            "weather": {
                "rain_mm_1h": rain_1h,
                "rain_mm_3h": rain_3h_auto,      # API에서 추정된 값
                "rain_mm_3h_used": rain_3h_used, # 실제 계산에 사용한 값
                "rain_3h_source": rain_3h_source,
                "temp_c": weather.get("temp_c"),
                "humidity": weather.get("humidity"),
                "wind_speed": weather.get("wind_speed"),
                "weather_desc": weather.get("weather_desc"),
                "timestamp": weather.get("timestamp"),
            },
            "elevation_m": elevation_m,
            "risk": {
                "level": level,
                "score": round(score, 3),
                "factors": factors,
            },
            "explanations": explanations,
        }

    except Exception as e:
        return {"error": f"❌ 침수 위험 판단 중 오류 발생: {str(e)}"}


# ─────────────────────────────────────────────────────────────
# (선택) 거리 계산 유틸
# ─────────────────────────────────────────────────────────────
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    두 좌표 사이 거리(km) 계산 (사용하지 않으면 삭제 가능)
    """
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
