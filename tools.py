import os
import shutil
import requests

# 1. 텍스트 파일 읽기
def read_file(filename: str) -> str:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"파일을 읽을 수 없습니다: {str(e)}"

# 2. 날씨 조회 (OpenWeather API 사용)
def get_weather(city: str) -> str:
    API_KEY = "640c24f59616729fd42cff9972c93165"  # OpenWeather API 키
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
def calculate(expression: str) -> str:
    try:
        result = eval(expression, {"__builtins__": {}})
        return f"결과는 {result}입니다."
    except Exception as e:
        return f"계산 오류: {str(e)}"

# 4. 디스크 사용량 확인
def check_disk_usage(path: str = "C:/") -> str:
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
def get_largest_files(directory: str = "C:/", limit: int = 5) -> str:
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
def get_location() -> str:
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        return f"당신의 IP 기반 위치는 {data['city']}, {data['region']}, {data['country']}입니다."
    except Exception as e:
        return f"위치 정보를 가져오는 데 실패했습니다: {str(e)}"


# GPT Tool 사양 목록
tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "텍스트 파일을 읽어 반환합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"}
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "도시의 날씨를 반환합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "수학 수식을 계산합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_disk_usage",
            "description": "지정된 경로의 디스크 사용량을 반환합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_largest_files",
            "description": "디렉토리에서 가장 큰 파일 목록을 반환합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string"},
                    "limit": {"type": "integer"}
                },
                "required": ["directory", "limit"]
            }
        }
    },
        {
        "type": "function",
        "function": {
            "name": "get_location",
            "description": "사용자의 현재 위치를 반환합니다.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]
