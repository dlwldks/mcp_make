# mcp_core/claude_client.py
import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def ask_claude(user_input: str) -> str:
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=512,
        system=(
            "당신은 MCP 판단 엔진입니다.\n"
            "아래 중 하나의 agent_name을 고르고 JSON만 반환하세요: "
            "'weather_info', 'flood_checker', 'evacuation'.\n"
            "지역명/구역명은 arguments.query에 담으세요.\n"
            "자연어 금지. JSON만:\n"
            "{\n  \"agent_name\": \"flood_checker\",\n  \"arguments\": { \"query\": \"부산\" }\n}"
        ),
        messages=[{"role": "user", "content": user_input}]
    )
    return response.content[0].text
