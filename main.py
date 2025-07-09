import sys
import os
from dotenv import load_dotenv
from openai import OpenAI
from tools import (
    tools,
    read_file,
    get_weather,
    calculate,
    check_disk_usage,
    get_largest_files,
    get_location,
)

# 🌱 환경 변수 로드
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🎯 사용자 프롬프트 받기
while True:
    print("❓ 질문을 입력하세요 (종료하려면 'q'): ", end="")
    user_input = input()
    if user_input.lower() in ["q", "quit", "exit"]:
        print("👋 종료합니다.")
        break

    messages = [{"role": "user", "content": user_input}]

    # 🔁 1차 GPT 호출 (툴 선택)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    message = response.choices[0].message

    # 🧠 툴 없이 응답만 받은 경우
    if not message.tool_calls:
        print(f"\n🧠 [GPT 응답]\n{message.content}\n")
        continue

    # 🛠 툴 호출 처리
    tool_call = message.tool_calls[0]
    fn_name = tool_call.function.name
    args = eval(tool_call.function.arguments)

    # 🧪 연쇄 처리 로직: get_location → get_weather
    if fn_name == "get_location":
        location_result = get_location()

        if "현위치 날씨" in user_input:
            try:
                city = location_result.split("는 ")[-1].split(",")[0].strip()
                weather_result = get_weather(city)
                print(f"\n☁️ [현위치 날씨]\n{weather_result}\n")
            except Exception as e:
                print(f"\n❌ 도시 이름 파싱 실패: {e}\n")
        else:
            print(f"\n📍 [현위치 확인]\n{location_result}\n")

        continue

    # 📌 일반 툴 실행
    tool_result = None
    if fn_name == "read_file":
        tool_result = read_file(**args)
    elif fn_name == "get_weather":
        tool_result = get_weather(**args)
    elif fn_name == "calculate":
        tool_result = calculate(**args)
    elif fn_name == "check_disk_usage":
        tool_result = check_disk_usage(**args)
    elif fn_name == "get_largest_files":
        tool_result = get_largest_files(**args)

    # 🔁 2차 GPT 호출 (툴 응답 기반 대화)
    followup = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            *messages,
            message.model_dump(),
            {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": fn_name,
                "content": tool_result,
            },
        ],
    )

    print(f"\n🧠 [GPT 응답]\n{followup.choices[0].message.content}\n")
