# tools/flood_checker.py

"""
🌊 Flood Risk Checker Tool
- 역할: 날씨 설명과 기온 데이터를 기반으로 침수 위험 여부를 판정합니다.
- 현재는 단순 규칙 기반 (강한 비/폭우 등 문구 포함 여부)
- 추후에는 강수량 수치 기반 또는 침수 예측 모델로 확장 가능
"""

from pydantic import BaseModel

# ✅ 입력값 정의
class FloodCheckRequest(BaseModel):
    city: str
    description: str
    temp: float

# ✅ 침수 위험 판정 함수
def check_flood_risk(data: FloodCheckRequest) -> str:
    desc = data.description.lower()
    flood_keywords = ["폭우", "호우", "강한 비", "heavy rain", "집중호우", "torrential", "downpour", "장대비"]

    # 간단한 키워드 기반 판단
    if any(keyword in desc for keyword in flood_keywords):
        return f"⚠️ {data.city} 지역은 현재 '{data.description}' 상태이며 침수 위험이 있습니다. 기온은 {data.temp}°C입니다."

    # 낮은 기온이면 상대적으로 위험 낮음
    if data.temp < 5:
        return f"✅ {data.city} 지역은 현재 '{data.description}' 상태이며 기온이 낮아 침수 위험은 낮습니다."

    # 일반적인 경우
    return f"✅ {data.city} 지역은 현재 '{data.description}' 상태이며 특별한 침수 위험은 감지되지 않습니다."
