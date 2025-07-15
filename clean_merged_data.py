import pandas as pd

# 원본 CSV 파일 로드
df = pd.read_csv("merged_output.csv", encoding="utf-8-sig", low_memory=False)
print(f"🔍 원본 데이터 shape: {df.shape}")

# ✅ 열 이름 공백 제거
df.columns = df.columns.str.strip()

# ✅ 1. 불필요한 컬럼 제거
drop_cols = ["Unnamed: 1", "Unnamed: 2"]
df.drop(columns=[col for col in drop_cols if col in df.columns], inplace=True)

# ✅ 2. 시작일시/종료일시 datetime 변환
if "FLDN_BGNG_YMD" in df.columns and "FLDN_BGNG_TM" in df.columns:
    df["시작일시"] = pd.to_datetime(df["FLDN_BGNG_YMD"].astype(str).str.zfill(8) + df["FLDN_BGNG_TM"].astype(str).str.zfill(4),
                                 format="%Y%m%d%H%M", errors="coerce")
if "FLDN_END_YMD" in df.columns and "FLDN_END_TM" in df.columns:
    df["종료일시"] = pd.to_datetime(df["FLDN_END_YMD"].astype(str).str.zfill(8) + df["FLDN_END_TM"].astype(str).str.zfill(4),
                                 format="%Y%m%d%H%M", errors="coerce")

# ✅ 3. 중복 컬럼 제거
df = df.loc[:, ~df.columns.duplicated()]

# ✅ 4. 중복 행 제거
df.drop_duplicates(inplace=True)

# ✅ 5. 결측치 많은 열 제거
null_ratio = df.isnull().mean()
df = df.loc[:, null_ratio < 0.7]

# ✅ 6. 결과 저장
df.to_csv("cleaned_merged_output.csv", index=False, encoding="utf-8-sig")
print(f"✅ 정제된 데이터 저장 완료: cleaned_merged_output.csv")
