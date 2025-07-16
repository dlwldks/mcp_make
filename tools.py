import os
import shutil
import requests
from crewai import tool


# 1. 텍스트 파일 읽기
@tool("read_file")
def read_file(filename: str) -> str:
    """텍스트 파일을 읽어 반환합니다."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"파일을 읽을 수 없습니다: {str(e)}"

# 2. 날씨 조회 (OpenWeather API 사용)
@tool("get_weather")
def get_weather(city: str) -> str:
    """도시의 날씨를 반환합니다."""
    API_KEY = "your_openweather_api_key"  # 실제 키로 바꿔줘
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=kr"
    try:
        res = requests.get(url)
        data = res.json()
        if res.status_code != 200:
            return f"⚠️ 날씨 정보를 가져오지 못했어요: {data.get('message', 'Unknown error')}"
        weather = data['weather'][0]['description']
        temp = data['main']['temp']
        return f"{city}의 현재 날씨는 {weather}, 기온은 {temp}°C 입니다."
    except Exception as e:
        return f"❌ 에러 발생: {str(e)}"

# 3. 계산기
@tool("calculate")
def calculate(expression: str) -> str:
    """수학 수식을 계산합니다."""
    try:
        result = eval(expression, {"__builtins__": {}})
        return f"결과는 {result}입니다."
    except Exception as e:
        return f"계산 오류: {str(e)}"

# 4. 디스크 사용량 확인
@tool("check_disk_usage")
def check_disk_usage(path: str = "C:/") -> str:
    """디스크 사용량을 확인합니다."""
    try:
        total, used, free = shutil.disk_usage(path)
        return (
            f"{path} 디스크 용량 정보:\n"
            f"- 전체: {total // (2**30)} GB\n"
            f"- 사용 중: {used // (2**30)} GB\n"
            f"- 남은 공간: {free // (2**30)} GB"
        )
    except Exception as e:
        return f"디스크 정보 오류: {str(e)}"

# 5. 용량 큰 파일 찾기
@tool("get_largest_files")
def get_largest_files(directory: str = "C:/", limit: int = 5) -> str:
    """용량이 큰 파일 목록을 반환합니다."""
    file_sizes = []
    for root, _, files in os.walk(directory):
        for name in files:
            try:
                filepath = os.path.join(root, name)
                size = os.path.getsize(filepath)
                file_sizes.append((filepath, size))
            except:
                continue

    top_files = sorted(file_sizes, key=lambda x: x[1], reverse=True)[:limit]
    return "\n".join([
        f"{i+1}. {f} - {s // (2**10)} KB"
        for i, (f, s) in enumerate(top_files)
    ])

# 6. 현재 위치 조회
@tool("get_location")
def get_location() -> str:
    """현재 위치를 조회합니다."""
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        return f"당신의 IP 기반 위치는 {data['city']}, {data['region']}, {data['country']}입니다."
    except Exception as e:
        return f"위치 정보를 가져오는 데 실패했습니다: {str(e)}"

# ✅ 전체 툴을 리스트로 반환하는 함수
def get_tools():
    return [read_file, get_weather, calculate, check_disk_usage, get_largest_files, get_location]
