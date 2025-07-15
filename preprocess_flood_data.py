import pandas as pd
import requests
import os

# 🔧 설정
api_url = "https://www.safetydata.go.kr/V2/api/DSSP-IF-00117?serviceKey=8A4C7OEF22M827Y8&numOfRows=1000&pageNo=1"
csv_dir = "./data"  # CSV 파일이 저장된 폴더

# ✅ 침수 API 호출 함수
def get_flood_api_items():
    try:
        response = requests.get(api_url)
        data = response.json()
        print(f"📦 응답 키 확인: {data.keys()}")

        body = data.get("body")
        if isinstance(body, dict):
            items = body.get("items", [])
        elif isinstance(body, list):
            print(f"📊 받은 item 개수: {len(body)}")
            items = body
        else:
            print(f"❗ body가 dict 또는 list 아님: {type(body)}")
            return pd.DataFrame()

        df = pd.DataFrame(items)
        print(f"📈 침수 API 데이터 shape: {df.shape}")
        return df

    except Exception as e:
        print(f"❌ API 요청 실패: {e}")
        return pd.DataFrame()

# ✅ CSV 파일 로드 함수
# ✅ CSV 파일 로드 함수 (수정)
def load_csv_files(directory):
    dfs = []
    for file in os.listdir(directory):
        if file.endswith(".csv"):
            path = os.path.join(directory, file)
            try:
                df = pd.read_csv(path, encoding="cp949")
            except UnicodeDecodeError:
                df = pd.read_csv(path, encoding="utf-8")
            df["출처파일명"] = file

            # ✅ 지역 코드 수동 매핑
            mapping = {
                "rn_20250714090833_seoul.csv": "11000",     # 서울
                "rn_20250714090852_busan.csv": "26000",     # 부산
                "rn_20250714090900_north_busan.csv": "26100"  # 북부산
            }
            df["STDG_SGG_CD"] = mapping.get(file, "00000")  # 기본값 00000 (없으면)
            dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

# ✅ 침수 데이터 전처리
def preprocess_flood_df(df):
    df["시작일시"] = pd.to_datetime(df["FLDN_BGNG_YMD"].astype(str) + df["FLDN_BGNG_TM"].astype(str).str.zfill(4),
                                format="%Y%m%d%H%M", errors="coerce")
    df["종료일시"] = pd.to_datetime(df["FLDN_END_YMD"].astype(str) + df["FLDN_END_TM"].astype(str).str.zfill(4),
                                format="%Y%m%d%H%M", errors="coerce")
    return df

# ✅ 실행
if __name__ == "__main__":
    print("📥 CSV 파일 불러오는 중...")
    df_local = load_csv_files(csv_dir)
    print(f"📂 CSV 데이터 shape: {df_local.shape}")

    print("\n🌐 침수 API 데이터 가져오는 중...")
    df_flood = get_flood_api_items()
    if not df_flood.empty:
        df_flood = preprocess_flood_df(df_flood)

        # 병합 기준 컬럼 확인
        print("📋 df_local 컬럼 목록:")
        print(df_local.columns.tolist())
        print("📋 df_flood 컬럼 목록:")
        print(df_flood.columns.tolist())

        # ✅ 병합 (법정동시군구코드 기준)
        merged = pd.merge(df_local, df_flood, how="left", on="STDG_SGG_CD")
        print(f"\n✅ 병합 결과 shape: {merged.shape}")

        # 💾 결과 저장
        merged.to_csv("merged_output.csv", index=False, encoding="utf-8-sig")
        print("💾 병합 결과 저장 완료: merged_output.csv")
    else:
        print("🚫 API 데이터 없음. 병합 생략.")
