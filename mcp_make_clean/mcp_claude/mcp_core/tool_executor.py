# mcp_core/tool_executor.py

from mcp_core.tool_router import route_tool
from models import requests, responses
from typing import Union

def execute_tool(input_data: Union[
    requests.WeatherRequest,
    requests.RainfallRequest,
    requests.FloodRiskRequest,
    requests.ElevationRequest,
    requests.EvacuationRequest
]) -> Union[
    responses.WeatherResponse,
    responses.RainfallResponse,
    responses.FloodRiskResponse,
    responses.ElevationResponse,
    responses.EvacuationResponse
]:
    """
    MCP의 핵심 실행 함수.
    라우터에서 알맞은 Tool로 전달된 요청 데이터를 처리하고,
    그 결과를 적절한 Response 모델로 감싸서 반환함.
    """
    result = route_tool(input_data)
    return result
