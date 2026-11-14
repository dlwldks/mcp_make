# mos_all.py
# mos_all 다음으로 실행 -> realtime_make_obs.py -> accuracy_percentage.py

import os
import sys
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from math import sqrt
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error
from sklearn.multioutput import MultiOutputRegressor
from dotenv import load_dotenv

# backtest 시 돌린 결과물 -> agent_metric_calculation.py -> accuracy_percentage.py
# real time 시 돌린 결과물 -> agent_metric_calculation.py -> realtime_make_obs.py -> accuracy_percentage.py

# ==================== 사용자 설정 (숫자만 바꿔서 기간 조절) ====================
STATION_KEY = "suwon"   # seoul, suwon, busan, daegu, incheon, daejeon, gwangju, ulsan, sejong
MODE = "backtest"       # "backtest" = 과거 구간 예측(즉시 평가), "realtime" = 현재→미래 예측

# ⚠ 예전 TRAIN_DAYS 롤링 학습은 사용하지 않음 (10년치 + 직전 7일 구조로 교체)
TRAIN_DAYS = 119        # 남겨두지만 실제 학습엔 쓰지 않음

# --- backtest 전용(과거 예측·평가) ---
FCST_START = "2025-02-01 00:00"  # 예측/평가 시작
FCST_END   = "2025-02-16 23:59"  # 예측/평가 끝

# --- realtime 전용(현재→미래 예측) ---
FORECAST_DAYS = 16      # 앞으로 며칠 예측할지 (⚠ Open-Meteo는 최대 16일까지만 지원)

# 백테스트 입력을 ERA5(archive)로 넣을지 (True 권장). False면 당시 forecast API 사용 시도.
USE_ARCHIVE_FOR_BACKTEST_INPUT = True
# ============================================================================


# ==================== 설정 ====================
load_dotenv()
KMA_API_KEY = os.getenv("KMA_API_KEY")  # 필요
KMA_BASE_URL = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"

STATIONS = {
    "seoul": 108, "busan": 159, "daegu": 143, "incheon": 112,
    "gwangju": 156, "daejeon": 133, "ulsan": 152, "suwon": 119, "sejong": 239
}
STATION_META = {
    108: (37.571, 126.965), 119: (37.2636, 127.0286), 112: (37.474, 126.621),
    133: (36.371, 127.372), 156: (35.172, 126.891), 143: (35.877, 128.652),
    159: (35.101, 129.034), 152: (35.559, 129.319), 239: (36.480, 127.289),
}

# KMA 원시 응답 컬럼 (typ01 kma_sfctm2)
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

# 예측 타깃 4종
TARGETS = {
    "temperature": {"obs_col": "temperature", "clip": (-50, 60)},        # °C
    "humidity":    {"obs_col": "humidity",   "clip": (0, 100)},          # %
    "wind_speed":  {"obs_col": "wind_speed", "clip": (0, None)},         # m/s
    "cloud_total": {"obs_col": "ca_tot",     "clip": (0, 10)},           # 0~10(옥타)
}

# ==================== tqdm 준비 ====================
try:
    from tqdm.auto import tqdm
    def _tqdm(iterable=None, total=None, desc="", leave=False):
        return tqdm(iterable=iterable, total=total, desc=desc, leave=leave)
    TQDM_OK = True
except Exception:
    TQDM_OK = False
    def _tqdm(iterable=None, total=None, desc="", leave=False):
        # tqdm 미설치 시 폴백: 그냥 iterable 그대로 반환
        if iterable is None and total is not None:
            # dummy iterator
            return range(total)
        return iterable

def _stage(msg: str):
    # 굵게 구분선 출력
    print(f"\n=== {msg} ===")


# ==================== 학습 윈도우 빌더 ====================
def build_training_windows(fcst_start: datetime,
                           fcst_end: datetime,
                           years_back: int = 10,
                           extra_days: int = 7) -> List[Tuple[datetime, datetime, str]]:
    """
    예측 구간 (fcst_start ~ fcst_end)에 대해:
    1) 과거 years_back년 동안 같은 달/일/시 구간
    2) fcst_start 직전 extra_days일 구간
    을 학습용 윈도우로 반환.
    """
    windows: List[Tuple[datetime, datetime, str]] = []

    # 1) 같은 날짜/시간대 10년치
    for k in range(1, years_back + 1):
        year = fcst_start.year - k
        try:
            start_k = fcst_start.replace(year=year)
            end_k   = fcst_end.replace(year=year)
        except ValueError:
            # 2/29 같은 예외적인 날짜일 경우 스킵
            print(f"[WARN] {year}년 {fcst_start:%m-%d %H} → {fcst_end:%m-%d %H} 윈도우 생성 실패 (날짜 오류). 스킵.")
            continue
        windows.append((start_k, end_k, f"{year}_same_period"))

    # 2) 예측 직전 extra_days일
    prev_start = fcst_start - timedelta(days=extra_days)
    prev_end   = fcst_start
    windows.append((prev_start, prev_end, "prev_7days"))

    return windows


# ==================== 유틸 ====================
def clean_value(val: str):
    if val in ["-9", "-9.0", "-"]:
        return None
    try:
        if isinstance(val, (int, float)):
            return val
        s = str(val)
        return float(s) if "." in s else int(s)
    except Exception:
        return None


def fetch_hour_asos(stn_id: int, ts: datetime, api_key: str) -> Optional[Dict]:
    tm = ts.strftime("%Y%m%d%H%M")
    params = {"tm": tm, "stn": str(stn_id), "authKey": api_key}
    try:
        r = requests.get(KMA_BASE_URL, params=params, timeout=30)
        if r.status_code != 200:
            return None
        lines = r.text.splitlines()
        data_lines = [ln for ln in lines if ln.strip() and not ln.startswith("#")]
        if not data_lines:
            return None
        parts = data_lines[0].split()
        if len(parts) < len(COLUMNS):
            parts += [None] * (len(COLUMNS) - len(parts))
        rec = dict(zip(COLUMNS, parts))
        rec["datetime"] = datetime.strptime(rec["datetime"], "%Y%m%d%H%M")
        rec = {k: clean_value(v) if k != "datetime" else v for k, v in rec.items()}
        return rec
    except requests.exceptions.RequestException:
        return None

def fetch_range_asos(stn_id: int, start: datetime, end: datetime, api_key: str, show_progress: bool=True) -> pd.DataFrame:
    """ASOS 관측 구간 조회 (1시간 간격) + tqdm 진행바"""
    out: List[Dict] = []
    cur = start
    total = int((end - start).total_seconds() // 3600)

    # ✅ iterable을 반드시 지정해준다
    it = _tqdm(iterable=range(total), total=total, desc="1) ASOS 수집", leave=False) if show_progress else range(total)

    for _ in it:
        rec = fetch_hour_asos(stn_id, cur, api_key)
        if rec:
            out.append(rec)
        time.sleep(0.25)  # API 예의상 지연
        cur += timedelta(hours=1)

    df = pd.DataFrame(out)
    if df.empty:
        raise RuntimeError("ASOS 관측이 비었습니다. (키/지점/기간 확인)")
    df = df.sort_values("datetime").drop_duplicates(subset=["datetime"]).reset_index(drop=True)
    return df

def fetch_openmeteo_archive(lat: float, lon: float, start: datetime, end: datetime) -> pd.DataFrame:
    _stage("2) ERA5(아카이브) 수집")
    url = "https://archive-api.open-meteo.com/v1/era5"
    params = {
        "latitude": lat, "longitude": lon,
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,cloud_cover,surface_pressure",
        "timezone": "Asia/Seoul"
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    j = r.json()
    df = pd.DataFrame(j.get("hourly", {}))
    if df.empty:
        raise RuntimeError("Open-Meteo ERA5 응답이 비었습니다.")
    df["datetime"] = pd.to_datetime(df["time"])
    df.drop(columns=["time"], inplace=True)
    # [start, end)로 정확히 슬라이스
    df = df[(df["datetime"] >= start) & (df["datetime"] < end)].reset_index(drop=True)
    return df


def fetch_openmeteo_forecast(lat: float, lon: float, start: datetime, end: datetime) -> pd.DataFrame:
    """
    Open-Meteo Forecast API에서 NWP 입력을 가져옴.
    - start, end 차이로 필요한 일수를 계산
    - forecast_days 파라미터로 요청 (최대 16일로 클램프)
    - 최종적으로는 [start, end) 범위만 슬라이스해서 반환
    """
    _stage("4) Open-Meteo Forecast(입력) 수집")
    url = "https://api.open-meteo.com/v1/forecast"

    # 요청해야 할 일수 계산
    total_hours = (end - start).total_seconds() / 3600.0
    days_needed = int(np.ceil(total_hours / 24.0))

    # Open-Meteo 제약: 최대 16일
    days_needed_clamped = max(1, min(days_needed, 16))

    if days_needed != days_needed_clamped:
        print(f"[WARN] 요청 기간이 {days_needed}일이지만 Open-Meteo 제한으로 "
              f"{days_needed_clamped}일만 요청합니다. (start={start}, end={end})")

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,cloud_cover,surface_pressure",
        "timezone": "Asia/Seoul",
        "forecast_days": days_needed_clamped,
    }

    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    j = r.json()
    df = pd.DataFrame(j.get("hourly", {}))
    if df.empty:
        raise RuntimeError("Open-Meteo forecast 응답이 비었습니다.")
    df["datetime"] = pd.to_datetime(df["time"])
    df.drop(columns=["time"], inplace=True)

    # 우리가 원하는 [start, end)만 다시 슬라이스
    m = (df["datetime"] >= start) & (df["datetime"] < end)
    return df.loc[m].reset_index(drop=True)


def _add_time_feats(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    dt = pd.to_datetime(df["datetime"])
    df["hour"] = dt.dt.hour
    df["month"] = dt.dt.month
    df["sin_hour"] = np.sin(2*np.pi*df["hour"]/24)
    df["cos_hour"] = np.cos(2*np.pi*df["hour"]/24)
    return df


def _add_lags(df: pd.DataFrame, cols: List[str], lags: List[int]) -> pd.DataFrame:
    df = df.copy()
    for c in cols:
        for L in lags:
            df[f"{c}_lag{L}"] = df[c].shift(L)
    return df


def build_feats(nwp_df: pd.DataFrame) -> pd.DataFrame:
    rename = {
        "temperature_2m": "temp2m_nwp",
        "relative_humidity_2m": "rh2m_nwp",
        "wind_speed_10m": "wspd10_nwp",
        "cloud_cover": "tcc_nwp",            # 0~100 (%)
        "surface_pressure": "mslp_nwp",
    }
    df = nwp_df.rename(columns=rename).copy()
    df = _add_time_feats(df)
    df = _add_lags(df, cols=["temp2m_nwp", "rh2m_nwp", "wspd10_nwp", "tcc_nwp", "mslp_nwp"], lags=[1, 3, 6])
    return df


def _clip_series(s: pd.Series, lo: Optional[float], hi: Optional[float]) -> pd.Series:
    if lo is not None:
        s = s.clip(lower=lo)
    if hi is not None:
        s = s.clip(upper=hi)
    return s


# 🔹 전운량 전용 후처리 함수 (MOS 출력 → 살짝 안정화)
def postprocess_cloud_total_series(series: pd.Series) -> pd.Series:
    """
    - 0~10 범위로 한 번 더 클리핑
    - 지수형(EMWA 비슷한) smoothing으로 시간적으로 덜 튀게 함
    - 0.5 단위로 스냅
    - 거의 맑음 / 거의 흐림 구간은 0 / 10으로 정리
    """
    s = series.astype(float).copy()
    s = s.clip(0, 10)

    alpha = 0.7  # 최근 값 가중치 (0.7: 새 값 70%, 이전 값 30%)
    smoothed = []
    prev = None
    for v in s:
        if np.isnan(v):
            # 결측이면 이전 값 그대로 유지
            smoothed.append(prev if prev is not None else np.nan)
            continue
        if prev is None or np.isnan(prev):
            prev = v
        else:
            prev = alpha * v + (1 - alpha) * prev
        smoothed.append(prev)

    s2 = pd.Series(smoothed, index=s.index)
    s2 = s2.clip(0, 10)

    # 0.5 단위로 스냅
    s2 = np.round(s2 * 2) / 2.0

    # 거의 맑음(<1)은 0, 거의 흐림(>9)은 10으로 정리
    s2 = s2.where(~((s2 < 1) & s2.notna()), 0.0)
    s2 = s2.where(~((s2 > 9) & s2.notna()), 10.0)

    return s2


def train_mos_multi(asos_df: pd.DataFrame, nwp_hist_df: pd.DataFrame):
    """4개 타깃(기온, 습도, 풍속, 전운량) MOS 학습"""
    _stage("3) MOS 멀티타깃 학습")
    obs = asos_df[["datetime"] + [cfg["obs_col"] for cfg in TARGETS.values()]].copy()
    for _, cfg in TARGETS.items():
        col = cfg["obs_col"]
        obs[col] = pd.to_numeric(obs[col], errors="coerce")

    nwp = build_feats(nwp_hist_df)
    pair = pd.merge(nwp, obs, on="datetime", how="inner").dropna(subset=[cfg["obs_col"] for cfg in TARGETS.values()])
    if pair.empty or len(pair) < 100:
        raise RuntimeError("MOS 학습쌍 부족 (>=100 샘플 권장)")

    feat_cols = [c for c in pair.columns if c not in ["datetime"] + [cfg["obs_col"] for cfg in TARGETS.values()]]
    X = pair[feat_cols].values
    Y = pair[[cfg["obs_col"] for cfg in TARGETS.values()]].values

    imp = SimpleImputer(strategy="median")
    Ximp = imp.fit_transform(X)

    base = GradientBoostingRegressor(random_state=42)
    mdl = MultiOutputRegressor(base)
    mdl.fit(Ximp, Y)

    pred = mdl.predict(Ximp)
    cols = list(TARGETS.keys())
    maes = {cols[i]: mean_absolute_error(Y[:, i], pred[:, i]) for i in range(len(cols))}
    print("[Train] In-sample MAE", {k: f"{v:.2f}" for k, v in maes.items()}, f"(n={len(pair)})")

    return {
        "model": mdl,
        "imputer": imp,
        "features": feat_cols,
        "target_order": [cfg["obs_col"] for cfg in TARGETS.values()]
    }


def predict_mos_multi(mos_pack: Dict, nwp_fore_df: pd.DataFrame) -> pd.DataFrame:
    _stage("5) MOS 예측")
    nwp = build_feats(nwp_fore_df).copy()
    X = nwp[mos_pack["features"]].values
    Ximp = mos_pack["imputer"].transform(X)
    yhat = mos_pack["model"].predict(Ximp)
    out = nwp[["datetime"]].copy()

    for i, (key, cfg) in enumerate(TARGETS.items()):
        lo, hi = cfg["clip"]
        pred = pd.Series(yhat[:, i])
        pred = _clip_series(pred, lo, hi)

        # 🔹 전운량만 별도 후처리
        if key == "cloud_total":
            pred = postprocess_cloud_total_series(pred)

        out[key] = pred.values

    out = out.rename(columns={
        "temperature": "예측 기온(°C)",
        "humidity": "예측 습도(%)",
        "wind_speed": "예측 풍속(m/s)",
        "cloud_total": "예측 전운량(0~10)",
    })
    out.insert(0, "날짜/시간", out.pop("datetime"))
    return out[["날짜/시간", "예측 기온(°C)", "예측 습도(%)", "예측 풍속(m/s)", "예측 전운량(0~10)"]]


# ==================== 평가 유틸(백테스트용) ====================
def evaluate_predictions(pred_df: pd.DataFrame, asos_df: pd.DataFrame) -> Tuple[Dict[str, Dict[str, float]], pd.DataFrame]:
    _stage("6) 백테스트 평가")
    """
    pred_df: ["날짜/시간","예측 기온(°C)","예측 습도(%)","예측 풍속(m/s)","예측 전운량(0~10)"]
    asos_df: ASOS 원본 (datetime, temperature, humidity, wind_speed, ca_tot)
    """
    obs = asos_df[["datetime", "temperature", "humidity", "wind_speed", "ca_tot"]].copy()
    obs = obs.rename(columns={
        "datetime": "날짜/시간",
        "temperature": "실측 기온(°C)",
        "humidity": "실측 습도(%)",
        "wind_speed": "실측 풍속(m/s)",
        "ca_tot": "실측 전운량(0~10)",
    })
    df = pd.merge(pred_df, obs, on="날짜/시간", how="inner")

    for c in ["예측 기온(°C)", "예측 습도(%)", "예측 풍속(m/s)", "예측 전운량(0~10)",
              "실측 기온(°C)", "실측 습도(%)", "실측 풍속(m/s)", "실측 전운량(0~10)"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    metrics = {}
    pairs = [
        ("기온", "예측 기온(°C)", "실측 기온(°C)"),
        ("습도", "예측 습도(%)", "실측 습도(%)"),
        ("풍속", "예측 풍속(m/s)", "실측 풍속(m/s)"),
        ("전운량", "예측 전운량(0~10)", "실측 전운량(0~10)"),
    ]
    for name, pcol, ocol in pairs:
        tmp = df[[pcol, ocol]].dropna()
        if tmp.empty:
            metrics[name] = {"n": 0, "MAE": np.nan, "RMSE": np.nan, "MBE": np.nan}
            continue
        e = tmp[pcol] - tmp[ocol]
        mae = float(np.abs(e).mean())
        rmse = float(sqrt((e**2).mean()))
        mbe = float(e.mean())  # bias(+는 과대)
        metrics[name] = {"n": int(len(tmp)), "MAE": mae, "RMSE": rmse, "MBE": mbe}

    return metrics, df


# ==================== 실행 ====================
if __name__ == "__main__":
    # 디버그: 어떤 파일/폴더인지
    print("[DEBUG] __file__ =", os.path.abspath(__file__))
    print("[DEBUG] CWD     =", os.getcwd())

    # 지점/좌표
    stn_id = STATIONS[STATION_KEY]
    lat, lon = STATION_META[stn_id]

    # 기간 설정: 예측 구간 먼저 결정
    now0 = datetime.now().replace(minute=0, second=0, microsecond=0)
    if MODE == "realtime":
        fcst_start = now0
        fcst_end   = now0 + timedelta(days=FORECAST_DAYS)
    else:
        fcst_start = pd.to_datetime(FCST_START).replace(minute=0, second=0, microsecond=0)
        fcst_end   = pd.to_datetime(FCST_END).replace(minute=0, second=0, microsecond=0)

    print(f"[INFO] station={STATION_KEY}, forecast={fcst_start:%Y-%m-%d %H} → {fcst_end:%Y-%m-%d %H}, mode={MODE}")
    print(f"[INFO] USE_ARCHIVE_FOR_BACKTEST_INPUT={USE_ARCHIVE_FOR_BACKTEST_INPUT}, TQDM_OK={TQDM_OK}")

    # 🔹 학습 윈도우 구성 (예측 구간 기준 10년치 + 직전 7일)
    train_windows = build_training_windows(fcst_start, fcst_end, years_back=10, extra_days=7)
    for s, e, tag in train_windows:
        print(f"  - train window [{tag}]: {s:%Y-%m-%d %H} → {e:%Y-%m-%d %H}")

    # 1) ASOS(학습) 수집 - 여러 윈도우 합치기
    asos_list: List[pd.DataFrame] = []
    for s, e, tag in train_windows:
        print(f"[INFO] ASOS train window {tag}: {s:%Y-%m-%d %H} → {e:%Y-%m-%d %H}")
        df_win = fetch_range_asos(stn_id, s, e, KMA_API_KEY, show_progress=True)
        df_win["train_tag"] = tag
        asos_list.append(df_win)

    asos_train = pd.concat(asos_list, ignore_index=True)
    asos_train = asos_train.sort_values("datetime").drop_duplicates(subset=["datetime"]).reset_index(drop=True)

    # 관측 타깃 정리(숫자 & 간단 보간)
    for _, cfg in TARGETS.items():
        col = cfg["obs_col"]
        asos_train[col] = pd.to_numeric(asos_train[col], errors="coerce").interpolate(limit_direction="both")

    # 2) ERA5(학습 피처) - 같은 윈도우들로 합치기
    nwp_list: List[pd.DataFrame] = []
    for s, e, tag in train_windows:
        print(f"[INFO] ERA5 train window {tag}: {s:%Y-%m-%d %H} → {e:%Y-%m-%d %H}")
        df_nwp = fetch_openmeteo_archive(lat, lon, s, e)
        df_nwp["train_tag"] = tag
        nwp_list.append(df_nwp)

    nwp_hist = pd.concat(nwp_list, ignore_index=True)
    nwp_hist = nwp_hist.sort_values("datetime").drop_duplicates(subset=["datetime"]).reset_index(drop=True)

    # 3) MOS 학습
    mos_pack = train_mos_multi(asos_train, nwp_hist)

    # 4) 예측 입력(NWP)
    if MODE == "realtime":
        nwp_input = fetch_openmeteo_forecast(lat, lon, fcst_start, fcst_end)
    else:
        if USE_ARCHIVE_FOR_BACKTEST_INPUT:
            _stage("4) ERA5 Archive(백테스트 입력) 수집")
            nwp_input = fetch_openmeteo_archive(lat, lon, fcst_start, fcst_end)
        else:
            _stage("4) Open-Meteo Forecast(백테스트 입력) 수집")
            nwp_input = fetch_openmeteo_forecast(lat, lon, fcst_start, fcst_end)

    # 5) MOS 예측
    pred_df = predict_mos_multi(mos_pack, nwp_input)

    # 6) 저장(+ 백테스트면 평가)
    if MODE == "realtime":
        out_name = f"mos_multi_realtime_cloud_{STATION_KEY}_{fcst_start:%Y%m%d%H}_{fcst_end:%Y%m%d%H}.csv"
        pred_df.to_csv(out_name, index=False, encoding="utf-8-sig")
        print("\n=== 예측 샘플 ===")
        print(pred_df.head(12))
        print("\n📄 저장 완료:", out_name)
    else:
        _stage("6) ASOS(백테스트 관측) 수집")
        # 백테스트 평가용 관측도 진행바로 수집
        asos_eval = fetch_range_asos(stn_id, fcst_start, fcst_end, KMA_API_KEY, show_progress=True)
        for _, cfg in TARGETS.items():
            col = cfg["obs_col"]
            asos_eval[col] = pd.to_numeric(asos_eval[col], errors="coerce")

        metrics, merged = evaluate_predictions(pred_df, asos_eval)
        ordered_cols = [
            "날짜/시간",
            "예측 기온(°C)", "실측 기온(°C)",
            "예측 습도(%)", "실측 습도(%)",
            "예측 풍속(m/s)", "실측 풍속(m/s)",
            "예측 전운량(0~10)", "실측 전운량(0~10)"
        ]
        for c in ordered_cols:
            if c not in merged.columns:
                merged[c] = np.nan
        merged = merged[ordered_cols]

        out_name = f"Last_mos_multi_backtest_{STATION_KEY}_{fcst_start:%Y%m%d%H}_{fcst_end:%Y%m%d%H}.csv"
        pred_df.to_csv(out_name, index=False, encoding="utf-8-sig")

        merged_name = f"{out_name.replace('.csv', '')}_with_obs.csv"
        merged.to_csv(merged_name, index=False, encoding="utf-8-sig")

        print("\n=== 백테스트 지표 ===")
        for k, v in metrics.items():
            print(f"- {k}: n={v['n']}, MAE={v['MAE']:.2f}, RMSE={v['RMSE']:.2f}, MBE={v['MBE']:.2f}")
        print("\n📄 예측 저장:", out_name)
        print("📄 병합(예측+실측) 저장:", merged_name)
