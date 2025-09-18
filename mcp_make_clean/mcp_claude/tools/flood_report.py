import requests
from pydantic import BaseModel
from typing import Dict

API_KEY = "640c24f59616729fd42cff9972c93165"

class ReportRequest(BaseModel):
    location: str

def generate_report(request: ReportRequest) -> Dict:
    city = request.location
    try:
        # 1. 도시명 → 위경도 검색
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
        geo_res = requests.get(geo_url)
        geo_data = geo_res.json()

        if not geo_data:
            return {"error": f"도시 '{city}'에 대한 정보를 찾을 수 없습니다."}

        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]

        # 2. 날씨 + 강수량 정보
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        weather_res = requests.get(weather_url)
        weather = weather_res.json()

        description = weather["weather"][0]["description"]
        temp = weather["main"]["temp"]
        rainfall = weather.get("rain", {}).get("1h", 0.0)

        # 3. 수위 예측 (룰 기반)
        base_level = 0.5
        predicted_level = base_level + (rainfall * 0.8)
        risk_level = (
            "low" if predicted_level < 1.0
            else "medium" if predicted_level < 2.0
            else "high"
        )

        return {
            "location": city,
            "lat": lat,
            "lon": lon,
            "weather": description,
            "temperature": temp,
            "rainfall_mm": rainfall,
            "predicted_water_level": round(predicted_level, 2),
            "risk_level": risk_level,
        }

    except Exception as e:
        return {"error": f"예외 발생: {str(e)}"}
