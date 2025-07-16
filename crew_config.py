import sys
import os

# 프로젝트 루트 경로를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from crewai import Crew
from task import get_report_tasks, get_user_task


# 어떤 작업을 할지 선택
mode = input("📌 모드 선택: (1) 보고서 생성 / (2) 사용자 요청 > ")

if mode == "1":
    tasks = get_report_tasks()
    agents = [task.agent for task in tasks]
elif mode == "2":
    task = get_user_task()
    tasks = [task]
    agents = [task.agent]
else:
    print("❗잘못된 선택입니다.")
    exit()

crew = Crew(
    agents=agents,
    tasks=tasks,
    verbose=True
)
