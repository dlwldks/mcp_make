# 📂 파일명: tools/evacuation.py

"""
🧭 Evacuation Tool
- 역할: 사용자의 현재 위치(lat/lng)를 기준으로 가장 가까운 고지대 또는 대피소를 찾음
- 방식: 샘플 고지대 데이터 + 거리 기반 탐색
"""

import math
from typing import List
from pydantic import BaseModel

# ✅ 사용자 요청 모델
class EvacuationRequest(BaseModel):
    lat: float
    lng: float

# ✅ 고지대 샘플 데이터 (위도, 경도, 이름)
SHELTERS = [
    {"lat": 37.5915, "lng": 127.0012, "name": "북악스카이웨이"},
    {"lat": 37.5603, "lng": 127.0036, "name": "남산 정상"},
    {"lat": 37.5778, "lng": 126.9895, "name": "북한산 입구"},
]

# ✅ 거리 계산 함수
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # 지구 반지름 (km)
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# ✅ 대피소 탐색 함수
def find_nearest_shelter(req: EvacuationRequest) -> str:
    user_lat = req.lat
    user_lng = req.lng

    nearest = min(
        SHELTERS,
        key=lambda shelter: haversine(user_lat, user_lng, shelter["lat"], shelter["lng"])
    )

    distance = haversine(user_lat, user_lng, nearest["lat"], nearest["lng"])
    return (
        f"📍 가장 가까운 대피소는 '{nearest['name']}'입니다.\n"
        f"    - 거리: 약 {distance:.2f}km\n"
        f"    - 위치: ({nearest['lat']}, {nearest['lng']})"
    )
"""
🏃 Evacuation Route Tool
- 역할: 침수 위험 지역 기준 고지대로 대피 경로 제공
- 사용 API 예시: Kakao Directions API or dummy data
"""

def get_evacuation_route(lat: float, lng: float) -> dict:
    """
    현재 위치(lat, lng)를 기반으로 임시 대피소 또는 고지대 방향으로
    이동 경로 데이터를 반환 (현재는 더미 데이터 사용)
    """
    # TODO: 향후 Kakao Directions API 등으로 대체
    return {
        "start": {"lat": lat, "lng": lng},
        "end": {"lat": lat + 0.01, "lng": lng + 0.01},  # 고지대 가정
        "steps": [
            {"instruction": "100m 직진 후 좌회전", "distance": 100},
            {"instruction": "300m 직진 후 대피소 도착", "distance": 300}
        ]
    }
