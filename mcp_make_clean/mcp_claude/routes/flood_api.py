from fastapi import APIRouter, Query
from tools.weather_info import get_lat_lng, get_rainfall
from tools.flood_checker import predict_flood_risk
from models.responses import FloodResponse

router = APIRouter()

@router.get("/api/flood-info", response_model=FloodResponse)
def get_flood_info(city: str = Query(..., description="도시명 또는 지역명 (예: 서울, 부산)")):
    try:
        lat, lng = get_lat_lng(city)
        rainfall = get_rainfall(city)
        result = predict_flood_risk(lat=lat, lng=lng, rainfall=rainfall)
        return FloodResponse(
            lat=lat,
            lng=lng,
            rainfall=rainfall,
            risk_level=result["risk_level"],
            message=result["message"]
        )
    except Exception as e:
        return FloodResponse(
            lat=0.0,
            lng=0.0,
            rainfall=0.0,
            risk_level="알 수 없음",
            message=f"오류 발생: {str(e)}"
        )
