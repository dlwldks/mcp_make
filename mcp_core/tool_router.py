# 📂 파일명: mcp_core/tool_router.py
# 📌 역할: 자연어 질문을 분해하여 어떤 Tool (Agent)에 전달할지 결정하는 간단한 라우터

def route_tool(user_input: str) -> str:
    """
    사용자 입력을 분석하여 적절한 tool 이름을 반환한다.
    예: "오늘 비 와?" -> "weather"
        "침수 위험은?" -> "flood_checker"
    """
    input_lower = user_input.lower()
    if "비" in input_lower or "강수" in input_lower:
        return "weather"
    elif "침수" in input_lower or "물" in input_lower:
        return "flood_checker"
    elif "지도" in input_lower or "구간" in input_lower:
        return "flood_map"
    elif "대피" in input_lower:
        return "evacuation"
    else:
        return "default"