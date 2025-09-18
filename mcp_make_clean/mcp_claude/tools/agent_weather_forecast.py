from tqdm import tqdm
import os
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer
from dotenv import load_dotenv


# ====== 설정 ======
KMA_API_KEY = os.getenv("KMA_API_KEY")
BASE_URL = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"

STATIONS = {
    "seoul": 108, "busan": 159, "daegu": 143, "incheon": 112,
    "gwangju": 156, "daejeon": 133, "ulsan": 152, "suwon": 119, "sejong": 239
}

# 예측 타깃
TARGETS = {
    "temperature": "C",     # 기온
    "humidity": "%",        # 습도
    "wind_speed": "m/s",    # 풍속
    "ca_tot": "okta",       # 전운량(0~10)
}

# API 원시 응답 컬럼
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

# ====== 공통 유틸 ======
def clean_value(val: str):
    """기상청 결측 코드(-9, -9.0, '-') 처리 + 숫자 변환"""
    if val in ["-9", "-9.0", "-"]:
        return None
    try:
        if isinstance(val, (int, float)):
            return val
        if "." in val:
            return float(val)
        return int(val)
    except Exception:
        return val  # 문자열은 그대로 두고 이후 단계에서 처리

def fetch_hour(stn_id: int, ts: datetime, api_key: str) -> Optional[Dict]:
    """해당 시각(분=00)의 한 건을 호출해 dict로 반환(없으면 None)"""
    tm = ts.strftime("%Y%m%d%H%M")
    params = {"tm": tm, "stn": str(stn_id), "authKey": api_key}
    try:
        r = requests.get(BASE_URL, params=params, timeout=30)
    except requests.exceptions.RequestException:
        return None
    if r.status_code != 200:
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

def fetch_range(stn_id: int, start: datetime, end: datetime, api_key: str) -> pd.DataFrame:
    """시작~끝 시각 구간 데이터를 1시간 간격으로 수집 (tqdm 프로그래스 바 추가)"""
    cur = start
    out: List[Dict] = []

    total_hours = int((end - start).total_seconds() // 3600)
    for _ in tqdm(range(total_hours), desc=f"Fetching data for station {stn_id}"):
        rec = fetch_hour(stn_id, cur, api_key)
        if rec:
            out.append(rec)
        time.sleep(0.30)  # 서버 부하 방지
        cur += timedelta(hours=1)

    df = pd.DataFrame(out)
    if df.empty:
        raise RuntimeError("해당 기간 데이터가 비었습니다. (키/지점/기간 확인)")
    df = df.sort_values("datetime").reset_index(drop=True)

    # 중복 datetime 제거
    df = df.drop_duplicates(subset=["datetime"])
    return df

# ====== 피처 엔지니어링 ======
def make_base_features(df: pd.DataFrame) -> pd.DataFrame:
    """기본 시계열 피처(시간/요일/래그/롤링) 생성"""
    df = df.copy()

    # datetime 보정
    if not np.issubdtype(df["datetime"].dtype, np.datetime64):
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.drop_duplicates(subset=["datetime"])  # 중복 제거
    df = df.set_index("datetime")

    keep = ["temperature", "humidity", "wind_speed", "ca_tot"]
    for k in keep:
        if k not in df.columns:
            df[k] = np.nan

    # 시간 기반 순환 피처
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["month"] = df.index.month
    df["sin_hour"] = np.sin(2 * np.pi * df["hour"] / 24.0)
    df["cos_hour"] = np.cos(2 * np.pi * df["hour"] / 24.0)
    df["sin_dow"] = np.sin(2 * np.pi * df["dow"] / 7.0)
    df["cos_dow"] = np.cos(2 * np.pi * df["dow"] / 7.0)

    # 래그/이동 통계
    for lag in [1, 3, 6, 24]:
        for c in keep:
            df[f"{c}_lag{lag}"] = df[c].shift(lag)

    for win in [3, 6, 12, 24]:
        for c in keep:
            df[f"{c}_rollmean{win}"] = df[c].rolling(win, min_periods=1).mean()
            df[f"{c}_rollstd{win}"] = df[c].rolling(win, min_periods=1).std()

    # 결측 보간
    df[keep] = df[keep].interpolate(limit_direction="both")

    return df.reset_index(drop=False)

def add_domain_features(df: pd.DataFrame, le_vs: Optional[LabelEncoder] = None):
    """풍향 벡터화 + 구름코드 인코딩"""
    df = df.copy()

    # 풍향 → 라디안/사인/코사인
    if "wind_dir" in df.columns:
        df["wind_dir"] = pd.to_numeric(df["wind_dir"], errors="coerce")
        df["wind_dir_rad"] = np.deg2rad(df["wind_dir"].fillna(0))
        df["wind_dir_sin"] = np.sin(df["wind_dir_rad"])
        df["wind_dir_cos"] = np.cos(df["wind_dir_rad"])

    # 구름 타입 vs → 레이블 인코딩
    if "vs" in df.columns:
        vs_series = df["vs"].astype(str)
        if le_vs is None:
            le_vs = LabelEncoder()
            df["vs_code"] = le_vs.fit_transform(vs_series)
        else:
            known = set(le_vs.classes_)
            mapped = [x if x in known else le_vs.classes_[0] for x in vs_series]
            df["vs_code"] = le_vs.transform(mapped)
    else:
        le_vs = None

    return df, le_vs

def coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """숫자형으로 변환 가능한 컬럼은 전부 수치화"""
    df = df.copy()
    ignore = {"datetime", "vs"}
    for col in df.columns:
        if col in ignore or col == "station_id":
            continue
        if df[col].dtype == "O":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def build_features_pipeline(df: pd.DataFrame, le_vs: Optional[LabelEncoder] = None):
    base = make_base_features(df)
    dom, le_vs = add_domain_features(base, le_vs=le_vs)
    num = coerce_numeric(dom)
    return num, le_vs

# ====== 학습/예측 ======
def fit_gbr_model(train_df: pd.DataFrame, target: str):
    numeric_cols = train_df.select_dtypes(include=[np.number]).columns.tolist()
    exclude = set([target, "station_id"])
    feature_cols = [c for c in numeric_cols if c not in exclude]

    X_raw = train_df[feature_cols].values
    y = train_df[target].values
    mask = ~np.isnan(y)
    X_raw, y = X_raw[mask], y[mask]

    imputer = SimpleImputer(strategy="mean")
    X = imputer.fit_transform(X_raw)

    model = GradientBoostingRegressor(random_state=42)
    model.fit(X, y)
    return model, feature_cols, imputer

def rolling_predict(models: Dict[str, Dict], hist_df: pd.DataFrame,
                    start_dt: datetime, end_dt: datetime,
                    le_vs: Optional[LabelEncoder]) -> pd.DataFrame:
    df = hist_df.copy()
    cur = start_dt
    preds = []

    while cur < end_dt:
        tmp_feat, _ = build_features_pipeline(df, le_vs=le_vs)
        latest_ts = tmp_feat["datetime"].max()
        latest_row = tmp_feat[tmp_feat["datetime"] == latest_ts].iloc[0]

        next_row = latest_row.copy()
        next_row["datetime"] = cur

        for tgt, pack in models.items():
            feature_cols = pack["features"]
            imputer = pack["imputer"]

            x_raw = tmp_feat[tmp_feat["datetime"] == latest_ts][feature_cols].values
            x = imputer.transform(x_raw)
            yhat = float(pack["model"].predict(x)[0])
            next_row[tgt] = yhat

        preds.append(next_row[["datetime"] + list(TARGETS.keys())])

        # 필요한 컬럼만 append (중복 방지)
        append_row = pd.DataFrame([next_row])
        df = pd.concat([df, append_row], ignore_index=True)

        cur += timedelta(hours=1)

    return pd.DataFrame(preds)

def train_and_forecast(
    station_id: int,
    train_start: str = "2024-05-18",
    train_end: str   = "2024-06-01",
    forecast_start: str = "2024-06-01 00:00",
    forecast_end: str   = "2024-06-08 00:00",
    api_key: str = KMA_API_KEY
) -> Dict[str, pd.DataFrame]:
    raw = fetch_range(station_id, pd.to_datetime(train_start), pd.to_datetime(train_end), api_key)
    feat, le_vs = build_features_pipeline(raw, le_vs=None)

    models = {}
    for tgt in TARGETS.keys():
        mdl, feats, imp = fit_gbr_model(feat, tgt)
        models[tgt] = {"model": mdl, "features": feats, "imputer": imp}

    start_dt = pd.to_datetime(forecast_start)
    end_dt   = pd.to_datetime(forecast_end)
    hist = feat.copy()
    pred_df = rolling_predict(models, hist, start_dt, end_dt, le_vs=le_vs)

    holdout_h = 48
    if len(feat) > holdout_h + 24:
        tr = feat.iloc[:-holdout_h]
        ho = feat.iloc[-holdout_h:]
        eval_pack = {}
        for tgt in TARGETS.keys():
            mdl, feats, imp = fit_gbr_model(tr, tgt)
            X_ho_raw = ho[feats].values
            X_ho = imp.transform(X_ho_raw)
            y_true = ho[tgt].values
            y_pred = mdl.predict(X_ho)
            eval_pack[tgt] = round(float(mean_absolute_error(y_true, y_pred)), 3)
    else:
        eval_pack = {t: None for t in TARGETS.keys()}

    return {"train_df": raw, "features_df": feat, "forecast_df": pred_df, "eval_mae": eval_pack}

# ====== 실행 예시 ======
if __name__ == "__main__":
    stn = STATIONS["suwon"]
    out = train_and_forecast(
        station_id=stn,
        train_start="2024-05-18",
        train_end="2024-06-01",
        forecast_start="2024-06-01 00:00",
        forecast_end="2024-06-08 00:00",
        api_key=KMA_API_KEY
    )
    print("=== 학습 데이터(상위 5행) ===")
    print(out["train_df"].head())
    print("\n=== 피처화 데이터(상위 5행) ===")
    print(out["features_df"].head())
    print("\n=== 예측 결과(상위 10행) ===")
    print(out["forecast_df"].head(10))
    print("\n=== 간단 MAE(학습 말미 48h 홀드아웃) ===")
    print(out["eval_mae"])

    forecast_friendly = out["forecast_df"].rename(columns={
        "datetime": "날짜/시간",
        "temperature": "예측 기온(°C)",
        "humidity": "예측 습도(%)",
        "wind_speed": "예측 풍속(m/s)",
        "ca_tot": "예측 전운량(0~10)"
    })

    forecast_friendly.to_csv("forecast_suwon_june1to8_friendly.csv", index=False, encoding="utf-8-sig")
    print("\n📄 예측 결과 CSV 저장 완료: forecast_suwon_june1to8_friendly.csv")