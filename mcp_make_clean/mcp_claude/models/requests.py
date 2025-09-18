# models/requests.py
from typing import Optional
from pydantic import BaseModel, Field, model_validator

# 공통 필드 제약
CityStr = Field(min_length=1, max_length=120)
LatF = Field(ge=-90, le=90)
LngF = Field(ge=-180, le=180)
NonNegF = Field(ge=0.0)


# ─────────────────────────────────────────────────────────────
# High-level (추천): 프론트가 'city'만 보내면 백엔드에서
# 지오코딩 → 실날씨 수집 → 위험도 산정까지 처리
# ─────────────────────────────────────────────────────────────

class WeatherHighLevelRequest(BaseModel):
    """도시명만으로 현재/예측 날씨를 조회할 때 사용."""
    city: str = CityStr


class RainfallHighLevelRequest(BaseModel):
    """도시명만으로 1h/3h 강수량 요약을 조회할 때 사용."""
    city: str = CityStr


class FloodRiskHighLevelRequest(BaseModel):
    """도시명만으로 침수 위험도를 평가할 때 사용(지오코딩+날씨 내부 처리)."""
    city: str = CityStr


class ElevationHighLevelRequest(BaseModel):
    """도시명만으로 중심 좌표의 지면고도 조회."""
    city: str = CityStr


class EvacuationHighLevelRequest(BaseModel):
    """도시명만으로 대피 관련 정보를 조회(차후 경로 검색 등 연동)."""
    city: str = CityStr
    destination: Optional[str] = None  # 필요 시 목적지 문자열 사용


# ─────────────────────────────────────────────────────────────
# Low-level (기존 유지): 프론트가 lat/lng/rainfall을 직접 전달
# ─────────────────────────────────────────────────────────────

class WeatherRequest(BaseModel):
    """좌표로 날씨 조회 (기존 로직 사용시)."""
    lat: float = LatF
    lng: float = LngF


class RainfallRequest(BaseModel):
    """좌표로 강수량 요약 조회 (기존 로직 사용시)."""
    lat: float = LatF
    lng: float = LngF


class FloodRiskRequest(BaseModel):
    """
    좌표 + (선택) 강수량으로 침수 위험 평가.
    - rainfall을 주지 않으면 백엔드에서 실날씨를 조회해 계산 가능(옵션 B 호환).
    """
    lat: float = LatF
    lng: float = LngF
    rainfall: Optional[float] = NonNegF  # ⬅ 기존 호환 위해 Optional로 완화
    city: Optional[str] = None


class ElevationRequest(BaseModel):
    """좌표로 지면고도 조회 (기존 로직 사용시)."""
    lat: float = LatF
    lng: float = LngF


class EvacuationRequest(BaseModel):
    """좌표로 대피 관련 정보 조회 (기존 로직 사용시)."""
    lat: float = LatF
    lng: float = LngF
    destination: Optional[str] = None


# ─────────────────────────────────────────────────────────────
# 선택: City 또는 좌표 중 하나만 받는 혼합 요청이 필요할 때 사용
# (지금은 필요 없지만, 확장 여지를 남겨둠)
# ─────────────────────────────────────────────────────────────

#class CityOrCoordsRequest(BaseModel):
#   """
#   city 또는 (lat,lng) 중 하나만 제공해야 하는 혼합 형태.
#   현재는 직접 사용하지 않지만, 라우팅 확장 시 유용.
#   """
#   city: Optional[str] = None
#   lat: Optional[float] = None
#   lng: Optional[float] = None

#   @root_validator
#   def validate_one_of_city_or_coords(cls, values):
#       city, lat, lng = values.get("city"), values.get("lat"), values.get("lng")
#       has_city = city is not None and city.strip() != ""
#       has_coords = lat is not None and lng is not None
#       if has_city == has_coords:
#           raise ValueError("city 또는 (lat,lng) 중 정확히 하나만 제공해야 합니다.")
#       return values
