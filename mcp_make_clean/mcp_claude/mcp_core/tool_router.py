# mcp_core/tool_router.py
from typing import Union, Any, Dict

from models import requests as req, responses  # responses 형은 유지(사용 중이면)
from tools import weather_info, flood_checker, elevation, evacuation


def route_tool(
    input_data: Union[
        # Low-level (좌표 기반)
        req.WeatherRequest,
        req.RainfallRequest,
        req.FloodRiskRequest,
        req.ElevationRequest,
        req.EvacuationRequest,
        # High-level (도시명 기반; 옵션 B)
        req.WeatherHighLevelRequest,
        req.RainfallHighLevelRequest,
        req.FloodRiskHighLevelRequest,
        req.ElevationHighLevelRequest,
        req.EvacuationHighLevelRequest
    ]
) -> Dict[str, Any]:
    """
    라우터는 가능한 한 '표준화된 dict' 응답을 반환하도록 통일한다.
    responses.* 모델을 쓰는 경우 FastAPI 레이어에서 pydantic이 직렬화 가능.
    """

    # ─────────────────────────────────────────
    # High-level: city만 들어오는 요청 (옵션 B)
    # ─────────────────────────────────────────
    if isinstance(input_data, req.WeatherHighLevelRequest):
        # city -> geocode -> onecall -> summary
        return weather_info.get_weather_summary({"city": input_data.city})

    if isinstance(input_data, req.RainfallHighLevelRequest):
        return weather_info.get_rainfall({"city": input_data.city})

    if isinstance(input_data, req.FloodRiskHighLevelRequest):
        # city만 받았을 때도 end-to-end로 침수위험 평가
        # 방법 A) geocode/날씨를 라우터에서 먼저 불러오고 flood_checker로 넘기기
        # 방법 B) flood_checker에 좌표만 넘기고 내부에서 날씨 조회(간단)
        # 여기선 B: 중복 호출 줄이고 싶으면 flood_checker에 from_weather 버전 추가
        summary = weather_info.get_weather_summary({"city": input_data.city})
        lat = float(summary["lat"])
        lng = float(summary["lng"])
        region = summary.get("region")
        return flood_checker.predict_flood_risk(lat=lat, lng=lng, city=region)

    if isinstance(input_data, req.ElevationHighLevelRequest):
        # city -> geocode -> elevation
        summary = weather_info.get_weather_summary({"city": input_data.city})
        lat = float(summary["lat"])
        lng = float(summary["lng"])
        elev = elevation.get_ground_level(lat, lng)
        return {
            "region": summary.get("region"),
            "lat": lat,
            "lng": lng,
            "elevation_m": elev
        }

    if isinstance(input_data, req.EvacuationHighLevelRequest):
        # TODO: 경로 API 연동 시 확장
        # 우선 좌표만 확보해서 응답 뼈대 제공
        summary = weather_info.get_weather_summary({"city": input_data.city})
        lat = float(summary["lat"])
        lng = float(summary["lng"])
        return {
            "region": summary.get("region"),
            "lat": lat,
            "lng": lng,
            "routes": [],
            "note": "경로 API 미연동"
        }

    # ─────────────────────────────────────────
    # Low-level: 좌표 기반 기존 분기 (유지)
    # ─────────────────────────────────────────
    if isinstance(input_data, req.WeatherRequest):
        return weather_info.get_weather_summary(input_data)

    if isinstance(input_data, req.RainfallRequest):
        return weather_info.get_rainfall(input_data)

    if isinstance(input_data, req.FloodRiskRequest):
        # city 함께 전달하면 region이 보기 좋게 표시됨
        return flood_checker.predict_flood_risk(
            lat=input_data.lat,
            lng=input_data.lng,
            rainfall=input_data.rainfall,
            city=input_data.city
        )

    if isinstance(input_data, req.ElevationRequest):
        # ElevationRequest는 좌표 기반으로 사용하는 것이 안전함
        # (만약 아직 city만 받는 형태라면 models를 최신으로 업데이트하거나,
        #  여기서 weather_info를 통해 좌표를 먼저 구해도 됨)
        lat = getattr(input_data, "lat", None)
        lng = getattr(input_data, "lng", None)
        region = getattr(input_data, "city", None)

        if lat is None or lng is None:
            # 좌표가 없다면 city로부터 좌표를 얻어낸다 (후방호환)
            if region:
                summary = weather_info.get_weather_summary({"city": region})
                lat = float(summary["lat"])
                lng = float(summary["lng"])
                region = summary.get("region")
            else:
                raise ValueError("ElevationRequest에 lat/lng 또는 city가 필요합니다.")

        elev = elevation.get_ground_level(lat, lng)
        return {
            "region": region or "Unknown",
            "lat": float(lat),
            "lng": float(lng),
            "elevation_m": elev
        }

    if isinstance(input_data, req.EvacuationRequest):
        # 아직 미구현이라면 안전한 기본값 반환
        return {
            "region": getattr(input_data, "city", None),
            "lat": getattr(input_data, "lat", None),
            "lng": getattr(input_data, "lng", None),
            "routes": [],
            "note": "evacuation route tool is not implemented yet"
        }

    # ─────────────────────────────────────────
    # Unsupported
    # ─────────────────────────────────────────
    raise ValueError("❌ [Tool Router] 지원하지 않는 요청 타입입니다.")
