# tool_router.py
from tools import flood_checker
from tools.area_resolver import get_lat_lng_by_area_name

def route_tool_call(tool_name: str, arguments: dict) -> dict:
    if tool_name == "flood_checker":
        # 지역명으로 위도경도 찾기
        area = arguments.get("area")
        if area:
            lat, lng = get_lat_lng_by_area_name(area)
            return flood_checker.predict_flood_risk(lat, lng)
        
        # 위도경도 직접 입력 시
        lat = arguments.get("lat")
        lng = arguments.get("lng")
        return flood_checker.predict_flood_risk(lat, lng)

    return {"error": f"❌ '{tool_name}' 도구는 존재하지 않습니다."}
