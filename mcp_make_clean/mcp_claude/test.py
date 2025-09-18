# mcp_core/test.py

from tools import weather_info


from mcp_core.tool_executor import execute_tool
from models.requests import (
    WeatherRequest,
    RainfallRequest,
    FloodRiskRequest,
    ElevationRequest,
    EvacuationRequest
)

# ⛅ 날씨 테스트
def test_weather():
    req = WeatherRequest(city="Seoul")
    res = execute_tool(req)
    print("📦 Weather Test Result:")
    print(res)

# 🌧️ 강수량 테스트
def test_rainfall():
    print("📦 Rainfall Test Result:")
    city_name = "Seoul"
    try:
        rain_mm = weather_info.get_rainfall(city_name)
        print(f"☔ {city_name}의 최근 1시간 강수량은 {rain_mm}mm입니다.")
    except Exception as e:
        print(str(e))


# 🌊 침수위험 테스트
def test_flood():
    city = "Busan"
    # 위경도 자동 조회
    lat, lng = weather_info.get_coordinates(city)
    
    # 강수량 조회
    rainfall = weather_info.get_rainfall(city)

    # 요청 객체 생성
    req = FloodRiskRequest(
        lat=lat,
        lng=lng,
        rainfall=rainfall
    )

    # 툴 실행
    res = execute_tool(req)
    print("📦 Flood Risk Test Result:")
    print(res)

# 🏔️ 고도 테스트
def test_elevation():
    req = ElevationRequest(lat=37.5665, lng=126.9780)
    res = execute_tool(req)
    print("📦 Elevation Test Result:")
    print(res)

# 🏃‍♀️ 대피 테스트
def test_evacuation():
    req = EvacuationRequest(lat=37.5665, lng=126.9780)
    res = execute_tool(req)
    print("📦 Evacuation Test Result:")
    print(res)

# ✅ 테스트 실행
if __name__ == "__main__":
    print("🧪 MCP 시스템 테스트 시작")
    test_weather()
    test_rainfall()
    test_flood()
    test_elevation()
    test_evacuation()
