"""
🗺️ Flood Map Tool
- 역할: 위험 지역들을 지도 위에 시각화합니다.
- 방식: folium을 사용한 HTML 지도 생성
"""

import folium
from pydantic import BaseModel
from typing import List

# ✅ 시각화에 필요한 데이터 구조
class FloodLocation(BaseModel):
    lat: float
    lng: float
    risk: str  # '낮음', '보통', '높음'

class FloodMapRequest(BaseModel):
    locations: List[FloodLocation]

# ✅ HTML 지도 생성 함수
def generate_flood_map(req: FloodMapRequest) -> str:
    # 중심 좌표를 첫 번째 위치로 설정
    center_lat = req.locations[0].lat
    center_lng = req.locations[0].lng
    m = folium.Map(location=[center_lat, center_lng], zoom_start=13)

    # 색상 매핑
    risk_color = {
        "낮음": "blue",
        "보통": "orange",
        "높음": "red"
    }

    # 마커 추가
    for loc in req.locations:
        folium.CircleMarker(
            location=[loc.lat, loc.lng],
            radius=10,
            color=risk_color.get(loc.risk, "gray"),
            fill=True,
            fill_opacity=0.6,
            popup=f"위험도: {loc.risk}"
        ).add_to(m)

    # 결과 HTML로 반환
    return m._repr_html_()
