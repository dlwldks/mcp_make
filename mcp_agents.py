from crewai import Agent
from tools import get_tools  # tools.py에서 함수 불러오기

# 에이전트 1: 침수 데이터 분석가
data_analyst = Agent(
    role="침수 데이터 분석가",
    goal="최근 침수 데이터를 정제하고 분석해 인사이트를 제공",
    backstory="기상청에서 데이터를 다루며 AI 모델로 예측을 해온 전문가입니다.",
    allow_delegation=False
)

# 에이전트 2: 보고서 작성가
report_writer = Agent(
    role="위험 지역 보고서 작성가",
    goal="침수 위험 지역에 대한 문서 및 대응 방안 작성",
    backstory="재난 대응 매뉴얼 작성 경험이 풍부한 보고서 전문가입니다.",
    allow_delegation=False
)

# 에이전트 3: 사용자 요청 분석 비서
analyst = Agent(
    role="도움 도우미",
    goal="사용자의 요청을 받아 적절한 툴을 호출해 도움을 줍니다.",
    backstory="당신은 다양한 유틸리티 도구에 정통한 비서입니다.",
    tools=get_tools(),  # ✅ 툴 주입
    allow_delegation=False
)
