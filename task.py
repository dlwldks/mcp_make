from crewai import Task
from mcp_agents import data_analyst, report_writer, analyst

def get_report_tasks():
    analyze_data = Task(
        description="CSV로 제공되는 침수 데이터를 기반으로 침수 위험 지역을 식별하고 통계 요약을 만들어라.",
        expected_output="위험 지역 목록과 위험 정도 요약",
        agent=data_analyst
    )

    write_report = Task(
        description="분석된 결과를 바탕으로, 시민에게 제공할 침수 대응 보고서를 작성하라.",
        expected_output="위험 지역, 예상 침수량, 시민 행동 요령 포함된 보고서",
        agent=report_writer
    )

    return [analyze_data, write_report]

def get_user_task():
    user_question = input("❓ 무엇을 도와드릴까요? > ")

    task = Task(
        description=f"사용자의 요청: {user_question}. 적절한 툴을 이용해 응답하라.",
        expected_output="요청에 대한 정확한 정보 또는 결과",
        agent=analyst
    )

    return task
