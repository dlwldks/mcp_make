# tools/weather_info.py

"""
🔧 Weather Tool
- 역할: 사용자가 입력한 도시 이름을 기준으로 현재 날씨와 기온 정보를 가져옵니다.
- 사용 API: OpenWeatherMap (https://openweathermap.org/current)
- 반환 형식: '{도시}의 날씨는 '{날씨 상태}', 현재 기온은 {기온}°C입니다.'
"""

import requests
from pydantic import BaseModel

# ✅ Tool에 필요한 입력값 정의
class WeatherRequest(BaseModel):
    city: str  # 사용자로부터 입력받을 도시명

# ✅ 실제 실행 함수
def get_weather(data: WeatherRequest) -> str:
    API_KEY = "640c24f59616729fd42cff9972c93165"  # OpenWeatherMap API KEY
    url = f"https://api.openweathermap.org/data/2.5/weather?q={data.city}&appid={API_KEY}&units=metric&lang=kr"

    try:
        res = requests.get(url)
        result = res.json()

        if res.status_code != 200:
            return f"❌ 날씨 데이터를 가져오지 못했어요: {result.get('message', '')}"

        weather = result["weather"][0]["description"]
        temp = result["main"]["temp"]

        return f"📍 {data.city}의 날씨는 '{weather}', 현재 기온은 {temp}°C입니다."

    except Exception as e:
        return f"❌ 에러 발생: {str(e)}"
# 📂 파일명: tools/weather_info.py