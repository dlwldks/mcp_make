
# 📂 파일명: main.py
# 📌 역할: 사용자 입력을 받아 Claude + Tool 흐름 실행
from mcp_core.claude_client import ask_claude

if __name__ == "__main__":
    user_input = input("\U0001F4AC 사용자 질문 > ")
    print("\u2705 결과:", ask_claude(user_input))
