from crew_config import report_crew, user_query_crew

if __name__ == "__main__":
    print("1. 침수 보고서 작성")
    print("2. 사용자 질문 응답")
    choice = input("선택 > ")

    if choice == "1":
        result = report_crew.kickoff()
    else:
        result = user_query_crew.kickoff()

    print("\n🧠 최종 결과:")
    print(result)
