# 📂 tools/elevation.py

"""
🗻 Elevation Tool (Google API 버전, 최적화)
- 역할: 위도/경도를 입력받아 지형 고도(m) 반환
- API: Google Elevation API
- 특이사항:
  - TTL 캐시(2h)
  - 타임아웃(8s), 간단 재시도(최대 2회, 지수 백오프)
  - 좌표 유효성 검사
"""

from __future__ import annotations
import time
import math
import requests
from typing import Dict, Tuple

# ✅ Google Elevation API Key (요청대로 코드에 상수 보관)
GOOGLE_ELEVATION_API_KEY = "AIzaSyAkPWGJi-XtTtz5D9Pt9sYmy4xcB9HuDtc"

# ─────────────────────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────────────────────
HTTP_TIMEOUT = 8  # seconds
TTL_SECONDS = 60 * 60 * 2  # 2h
MAX_RETRIES = 2
BACKOFF_BASE = 0.7  # seconds

# 간단 TTL 캐시: "lat,lng" -> (elevation_m, expires_at)
_ELEV_CACHE: Dict[str, Tuple[float, float]] = {}


def _validate_coords(lat: float, lng: float) -> None:
    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"[Elevation] 위도(lat) 범위 오류: {lat}")
    if not (-180.0 <= lng <= 180.0):
        raise ValueError(f"[Elevation] 경도(lng) 범위 오류: {lng}")


def _cache_key(lat: float, lng: float) -> str:
    # 캐시 키를 소수점 5자리로 통일해 과도한 키 분산 방지
    return f"{lat:.5f},{lng:.5f}"


def _request_elevation(lat: float, lng: float) -> float:
    """
    실제 HTTP 호출(재시도 포함). elevation(m) 반환.
    """
    url = "https://maps.googleapis.com/maps/api/elevation/json"
    params = {
        "locations": f"{lat},{lng}",
        "key": GOOGLE_ELEVATION_API_KEY,
    }
    headers = {"User-Agent": "flood-mcp/1.0"}

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=HTTP_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()

            # Google Elevation 응답 status 검사
            status = data.get("status", "UNKNOWN")
            if status != "OK":
                # OVER_QUERY_LIMIT, REQUEST_DENIED 등 다양한 status가 올 수 있음
                err_msg = data.get("error_message", "")
                raise RuntimeError(f"[Elevation] API status={status} {err_msg}".strip())

            results = data.get("results", [])
            if not results:
                raise RuntimeError("[Elevation] API 응답에 results가 비어 있습니다.")

            elevation = results[0].get("elevation")
            if elevation is None:
                raise RuntimeError("[Elevation] elevation 필드를 찾을 수 없습니다.")

            return float(elevation)

        except (requests.Timeout, requests.ConnectionError) as net_err:
            # 네트워크 계열은 재시도
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_BASE * (2 ** attempt))
                continue
            raise RuntimeError(f"❌ [Elevation] 네트워크 오류: {net_err}") from net_err

        except requests.HTTPError as http_err:
            # 상태코드 4xx/5xx
            raise RuntimeError(f"❌ [Elevation] HTTP 오류: {http_err}") from http_err

        except Exception as e:
            # 기타 예외(파싱/상태/필드 등)
            raise RuntimeError(f"❌ [Elevation] 처리 실패: {e}") from e

    # 논리상 도달하지 않음
    raise RuntimeError("❌ [Elevation] 알 수 없는 오류")


def get_ground_level(lat: float, lng: float) -> float:
    """
    위도/경도 기반 고도 정보 조회 (단위: m)
    - TTL 캐시 사용
    - 유효성 검증 및 재시도 포함
    """
    _validate_coords(lat, lng)

    now = time.time()
    key = _cache_key(lat, lng)
    cached = _ELEV_CACHE.get(key)
    if cached and cached[1] > now:
        return cached[0]

    elevation = _request_elevation(lat, lng)

    # 고도는 음수가 나올 수 있음(해수면 이하). 별도 클램프 없이 그대로 반환.
    _ELEV_CACHE[key] = (elevation, now + TTL_SECONDS)
    return elevation
