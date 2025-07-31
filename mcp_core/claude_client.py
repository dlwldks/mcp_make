# 📂 파일명: mcp_core/claude_client.py
# 📌 역할: Claude API와 연결하고, MCP 컨텍스트 흐름을 통해 응답 생성
import os
from anthropic import Anthropic
from mcp_core.tool_router import route_tool
from mcp_core.tool_executor import execute_tool

def ask_claude(user_input: str) -> str:
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    tool_name = route_tool(user_input)
    tool_result = execute_tool(tool_name, user_input)

    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=512,
        messages=[
            {"role": "user", "content": f"사용자 질문: {user_input}\n도구 실행 결과: {tool_result}\n이 정보들을 통합해서 사용자에게 응답해줘."}
        ]
    )
    return response.content[0].text
