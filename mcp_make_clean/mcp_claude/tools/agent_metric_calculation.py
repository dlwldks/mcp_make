import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from sklearn.metrics import mean_absolute_error, mean_squared_error
from dotenv import load_dotenv

# ====== 공통 설정 ======
load_dotenv()  # ✅ .env 파일 불러오기
KMA_API_KEY = os.getenv("KMA_API_KEY")
TARGETS = {
    "temperature": "C",
    "humidity": "%",
    "wind_speed": "m/s",
    "ca_tot": "okta",
}

# --- Agent1에서 사용했던 fetch_range 함수 재사용 ---
def fetch_range(stn_id: int, start: datetime, end: datetime, api_key: str) -> pd.DataFrame:
    """기상청 API에서 start~end 구간 데이터를 가져옴"""
    from tqdm import tqdm
    import time, requests

    BASE_URL = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"
    COLUMNS = [
        "datetime", "station_id", "wind_dir", "wind_speed",
        "gust_dir", "gust_speed", "gust_time",
        "pressure", "sea_level_pressure", "pt", "pr",
        "temperature", "dew_point", "humidity", "pv",
        "rainfall_mm", "rain_day", "rain_jun", "rain_int",
        "rain_3hr", "snow_day", "snow_tot",
        "wc", "wp", "ww", "ca_tot", "ca_mid", "ca_low",
        "vs", "ss", "si", "st", "ts", "te1", "te2", "te3", "te4",
        "st2", "wh", "bf", "ir", "ix"
    ]

    def clean_value(val: str):
        if val in ["-9", "-9.0", "-"]: 
            return None
        try:
            if "." in str(val): 
                return float(val)
            return int(val)
        except: 
            return val

    def fetch_hour(stn_id: int, ts: datetime, api_key: str):
        tm = ts.strftime("%Y%m%d%H%M")
        params = {"tm": tm, "stn": str(stn_id), "authKey": api_key}
        try:
            r = requests.get(BASE_URL, params=params, timeout=30)
            if r.status_code != 200: 
                return None
        except: 
            return None

        lines = r.text.splitlines()
        data_lines = [ln for ln in lines if ln.strip() and not ln.startswith("#")]
        if not data_lines: 
            return None
        parts = data_lines[0].split()
        rec = dict(zip(COLUMNS, parts))
        rec["datetime"] = datetime.strptime(rec["datetime"], "%Y%m%d%H%M")
        rec = {k: clean_value(v) for k, v in rec.items()}
        return rec

    cur = start
    out = []
    total_hours = int((end - start).total_seconds() // 3600)
    for _ in tqdm(range(total_hours), desc=f"Fetching data for station {stn_id}"):
        rec = fetch_hour(stn_id, cur, api_key)
        if rec: 
            out.append(rec)
        time.sleep(0.3)
        cur += pd.Timedelta(hours=1)

    df = pd.DataFrame(out)
    df = df.sort_values("datetime").reset_index(drop=True)
    return df[["datetime"] + list(TARGETS.keys())]

# ====== Metric Agent ======
def metric_agent(
    forecast_file: str,
    station_id: int,
    start_dt: str,
    end_dt: str,
    api_key: str,
    out_prefix: str = "suwon_june1to8"
):
    # 1) 예측 데이터 불러오기
    forecast_df = pd.read_csv(forecast_file)

    # 컬럼명이 한글로 되어 있을 때 리네임
    rename_map = {
        "날짜/시간": "datetime",
        "예측 기온(°C)": "temperature",
        "예측 습도(%)": "humidity",
        "예측 풍속(m/s)": "wind_speed",
        "예측 전운량(0~10)": "ca_tot",
    }
    forecast_df = forecast_df.rename(columns=rename_map)

    forecast_df["datetime"] = pd.to_datetime(forecast_df["datetime"])

    # 2) 실제 데이터 불러오기
    actual_df = fetch_range(station_id, pd.to_datetime(start_dt), pd.to_datetime(end_dt), api_key)
    actual_df["datetime"] = pd.to_datetime(actual_df["datetime"])

    # CSV 저장 (자료1)
    actual_csv = f"{out_prefix}_actual.csv"
    actual_df.to_csv(actual_csv, index=False, encoding="utf-8-sig")

    # 3) merge (datetime 기준)
    merged = pd.merge(forecast_df, actual_df, on="datetime", suffixes=("_pred", "_actual"))

    # 4) 정확도(%) 계산 = (1 - |예측-실제| / (실제+ε)) * 100
    eps = 1e-5
    for tgt in TARGETS.keys():
        merged[f"{tgt}_accuracy"] = (
            1 - abs(merged[f"{tgt}_pred"] - merged[f"{tgt}_actual"]) / (abs(merged[f"{tgt}_actual"]) + eps)
        ) * 100

    # CSV 저장 (자료2)
    acc_csv = f"{out_prefix}_accuracy.csv"
    merged.to_csv(acc_csv, index=False, encoding="utf-8-sig")

    # 5) 시각화 (자료3)
    plt.figure(figsize=(12, 8))
    for i, tgt in enumerate(TARGETS.keys(), 1):
        plt.subplot(2, 2, i)
        plt.plot(merged["datetime"], merged[f"{tgt}_pred"], label="Predicted", color="blue")
        plt.plot(merged["datetime"], merged[f"{tgt}_actual"], label="Actual", color="orange")
        plt.title(f"{tgt} 예측 vs 실제")
        plt.xticks(rotation=45)
        plt.legend()
    plt.tight_layout()
    plt.savefig(f"{out_prefix}_comparison.png", dpi=150)
    plt.close()

    return actual_csv, acc_csv, f"{out_prefix}_comparison.png"

# ====== 실행 예시 ======
if __name__ == "__main__":
    STATIONS = {"suwon": 119}
    actual_csv, acc_csv, graph_file = metric_agent(
        forecast_file="forecast_suwon_june1to8_friendly.csv",
        station_id=STATIONS["suwon"],
        start_dt="2024-06-01 00:00",
        end_dt="2024-06-08 00:00",
        api_key=KMA_API_KEY,
        out_prefix="suwon_june1to8"
    )

    print("1️⃣ 실제 데이터 CSV:", actual_csv)
    print("2️⃣ 정확도 비교 CSV:", acc_csv)
    print("3️⃣ 그래프 파일:", graph_file)
