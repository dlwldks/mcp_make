from typing import Optional, Any, Dict
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from mcp_core.tool_router import route_tool
from mcp_core.agent import run_agent
from models.requests import FloodRiskRequest
# ⬇️ response_model을 유지하려면 responses.FloodRiskResponse와 실제 리턴 구조가 일치해야 합니다.
# from models.responses import FloodRiskResponse

app = FastAPI(title="Flood MCP Backend", version="1.0.0")

# ─────────────────────────────────────────────────────────────
# CORS (배포 시 도메인으로 제한하는 것을 권장)
# ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 예: ["https://your-frontend.example.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# 헬스체크/버전
# ─────────────────────────────────────────────────────────────
@app.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok"}

@app.get("/version")
def version() -> Dict[str, str]:
    return {"version": app.version}

# ─────────────────────────────────────────────────────────────
# 저수준 GET (lat/lng/rainfall 직접) - 기존 엔드포인트
# NOTE:
# - response_model을 유지하려면 flood_checker 출력과 1:1로 맞추세요.
# - 일단 안정성을 위해 임시로 response_model 제거. 맞췄다면 주석 해제하세요.
# ─────────────────────────────────────────────────────────────
@app.get("/api/flood-info")  # , response_model=FloodRiskResponse
def get_flood_info(
    lat: float = Query(..., description="위도"),
    lng: float = Query(..., description="경도"),
    rainfall: Optional[float] = Query(None, description="3시간 누적 강수량(mm). 없으면 실날씨로 산정"),
    city: Optional[str] = Query(None, description="지역명(선택)")
):
    try:
        # FloodRiskRequest는 기존 스키마 사용
        req = FloodRiskRequest(lat=lat, lng=lng, rainfall=rainfall, city=city)
    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=ve.errors())

    try:
        resp = route_tool(req)  # dict 반환 (표준 스키마와 일치해야 response_model 검증 통과)
        if isinstance(resp, dict) and "error" in resp:
            raise HTTPException(status_code=502, detail=resp["error"])
        return resp
    except HTTPException:
        raise
    except Exception as e:
        # 외부 API 오류/예상치 못한 예외를 502로 래핑
        raise HTTPException(status_code=502, detail=f"flood-info failed: {str(e)}")

# ─────────────────────────────────────────────────────────────
# 고수준 POST: 자연어/지역명 → Claude → 지오코딩+날씨 → 위험평가
# ─────────────────────────────────────────────────────────────
class QueryIn(BaseModel):
    user_input: str  # 예: "부산 침수 위험 알려줘" / "서울 마포구"

@app.post("/query")
def query(in_: QueryIn):
    try:
        result = run_agent(in_.user_input)
        if isinstance(result, dict) and "error" in result:
            # agent 내부에서 에러 포맷을 dict로 준 경우
            raise HTTPException(status_code=502, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"agent pipeline failed: {str(e)}")

# ─────────────────────────────────────────────────────────────
# (선택) 고수준 바로가기: Claude 거치지 않고 '도시명'만 받아 즉시 위험평가
# 프론트에서 간편 호출할 곳이 필요하면 사용하세요.
# ─────────────────────────────────────────────────────────────
class CityIn(BaseModel):
    city: str

@app.post("/api/flood-risk/by-city")
def flood_risk_by_city(in_: CityIn):
    """
    도시명만 받아 end-to-end(지오코딩+날씨+고도→위험평가) 처리.
    tool_router가 HighLevel 요청을 지원하면 그걸 써도 되고,
    여기서는 간단히 기존 LowLevel 경로를 재활용합니다.
    """
    try:
        # weather_info를 통해 좌표/요약 확보 → flood_checker에 전달하는 방식도 가능
        # 여기서는 route_tool가 HighLevel을 지원하지 않는 프로젝트라도
        # 동작하도록, city만 넣고 weather_summary→coords를 뽑아 재사용하는
        # 접근을 추천하지만, 현재 route_tool 시그니처만 쓰고 싶다면
        # 별도 HighLevelRequest를 만들어 route_tool로 넘기세요.
        from tools.weather_info import get_weather_summary
        summary = get_weather_summary({"city": in_.city})
        lat = float(summary["lat"])
        lng = float(summary["lng"])
        # rainfall은 None으로 두면 flood_checker가 실날씨 3h를 사용
        req = FloodRiskRequest(lat=lat, lng=lng, rainfall=None, city=summary.get("region"))
        resp = route_tool(req)
        if isinstance(resp, dict) and "error" in resp:
            raise HTTPException(status_code=502, detail=resp["error"])
        return resp
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"by-city failed: {str(e)}")

# ─────────────────────────────────────────────────────────────
# 전역 예외 핸들러 (선택): dict 형태의 에러 JSON 표준화
# ─────────────────────────────────────────────────────────────
@app.exception_handler(HTTPException)
def http_exception_handler(_, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.status_code, "message": exc.detail}},
    )
