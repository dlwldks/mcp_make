# mcp_core/agent.py
from .tool_router import route_tool
from models import requests
import json

def run_agent(user_input: str):
    try:
        from .claude_client import ask_claude
        raw = ask_claude(user_input)      # '{"agent_name":"flood_checker","arguments":{"query":"부산"}}'
        plan = json.loads(raw)
        agent = plan.get("agent_name")
        args = plan.get("arguments", {})

        # 지역명만 들어온 경우에도 OK
        if agent == "flood_checker":
            # FloodRiskRequest는 lat/lng/rainfall이 필요하므로,
            # 내부에서 query -> 지오코딩 -> 날씨(강수) -> 위험평가까지 수행하는 high-level 요청으로 변환
            req = requests.FloodRiskHighLevelRequest(query=args.get("query"))
            return route_tool(req)

        elif agent == "weather_info":
            req = requests.WeatherHighLevelRequest(query=args.get("query"))
            return route_tool(req)

        elif agent == "evacuation":
            # 대피 경로도 query로 중심 좌표를 구해 붙이는 패턴
            req = requests.EvacuationHighLevelRequest(query=args.get("query"), destination=args.get("destination"))
            return route_tool(req)

        else:
            return {"error": f"Unknown agent_name: {agent}"}

    except Exception as e:
        return {"error": f"Agent Error: {str(e)}"}
