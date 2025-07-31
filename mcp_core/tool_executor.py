# 📂 파일명: mcp_core/tool_executor.py
# 📌 역할: tool 이름에 따라 실제 tool 함수를 실행하고 결과를 리턴
from tools.weather_info import get_weather_info
from tools.flood_checker import check_flood_risk
from tools.flood_map import draw_flood_map
from tools.evacuation import suggest_evacuation

def execute_tool(tool_name: str, user_input: str) -> str:
    if tool_name == "weather":
        return get_weather_info(user_input)
    elif tool_name == "flood_checker":
        return check_flood_risk(user_input)
    elif tool_name == "flood_map":
        return draw_flood_map(user_input)
    elif tool_name == "evacuation":
        return suggest_evacuation(user_input)
    else:
        return "죄송합니다. 해당 요청을 처리할 수 없습니다."