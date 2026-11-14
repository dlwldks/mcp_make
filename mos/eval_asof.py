"""
eval_asof.py — '과거 시점으로 돌아가 실시간 예측'을 재현하고 실측과 대조하는 평가 스크립트

방법
  1) 기준 시각(--start)을 정하고, 그 이전 데이터로만 보정 모델을 학습한다.
     (mos_all.py와 동일: 과거 10년 같은 기간 + 기준 시각 직전 7일, ERA5 피처 + ASOS 관측)
  2) 기준 시각에 '실제로 발표됐던 예보'를 입력으로 넣어 --days일 동안을 예측한다.
     - Open-Meteo Previous Runs API 사용: k일차 값 = k일 전에 발표된 예보 (k=0..days-1)
  3) 같은 기간 기상청 ASOS 관측값과 대조한다 (관측값은 채점에만 사용).
  4) 원본 예보 vs 보정 결과를 MAE·적중률로 비교한다.

모델 성격
  학습 입력은 ERA5(재분석), 예측 입력은 발표 예보다. 따라서 이 모델은 '예보 오차'가 아니라
  '격자값 ↔ 관측소 지점값' 차이(지점 편향)를 보정한다.

사용법
  KMA_API_KEY 환경변수 또는 .env 파일 필요 (기상청 API허브 키)
  python eval_asof.py --start 2026-11-07 --days 7 --station suwon
"""
import argparse
import os
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv

import mos_all as M  # 원래 코드의 피처 생성 / 학습 / 예측 함수 재사용

load_dotenv()
VARS = ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "cloud_cover", "surface_pressure"]
KMA_RANGE_URL = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm3.php"
PREV_RUNS_URL = "https://previous-runs-api.open-meteo.com/v1/forecast"

# 적중률 허용 오차 (accuracy_percentage.py와 동일)
TOLERANCE = {"temperature": 2.0, "humidity": 10.0, "wind_speed": 1.5, "ca_tot": 2.0}


def fetch_range_asos(stn_id: int, start: datetime, end: datetime, api_key: str) -> pd.DataFrame:
    """ASOS 시간자료 기간 조회 (kma_sfctm3). 원래 코드의 1시간 단위 호출보다 빠름."""
    out, cur = [], start
    while cur <= end:
        nxt = min(cur + timedelta(days=7), end)
        text = ""
        for _ in range(4):
            r = requests.get(KMA_RANGE_URL, params={
                "tm1": cur.strftime("%Y%m%d%H00"), "tm2": nxt.strftime("%Y%m%d%H00"),
                "stn": str(stn_id), "help": "0", "authKey": api_key}, timeout=60)
            r.encoding = "euc-kr"
            text = r.text
            if "#7777END" in text:
                break
            time.sleep(2)
        for ln in text.splitlines():
            if not ln.strip() or ln.startswith("#"):
                continue
            parts = ln.split()
            parts += [None] * (len(M.COLUMNS) - len(parts))
            rec = dict(zip(M.COLUMNS, parts))
            rec["datetime"] = datetime.strptime(rec["datetime"], "%Y%m%d%H%M")
            rec = {k: (M.clean_value(v) if k != "datetime" else v) for k, v in rec.items()}
            out.append(rec)
        cur = nxt + timedelta(hours=1)
    if not out:
        raise RuntimeError("ASOS 관측이 비었습니다. (키/지점/기간 확인)")
    return pd.DataFrame(out).sort_values("datetime").drop_duplicates("datetime").reset_index(drop=True)


def fetch_issued_forecast(lat: float, lon: float, start: datetime, days: int) -> pd.DataFrame:
    """기준 시각에 발표된 예보를 재구성: k일차 값 = previous_day{k} (k=0이면 최신 실행값)."""
    hourly = VARS + [f"{v}_previous_day{k}" for v in VARS for k in range(1, days)]
    end = start + timedelta(days=days) - timedelta(hours=1)
    r = requests.get(PREV_RUNS_URL, params={
        "latitude": lat, "longitude": lon, "hourly": ",".join(hourly), "timezone": "Asia/Seoul",
        "start_date": start.strftime("%Y-%m-%d"), "end_date": end.strftime("%Y-%m-%d")}, timeout=60)
    r.raise_for_status()
    d = pd.DataFrame(r.json()["hourly"])
    d["datetime"] = pd.to_datetime(d.pop("time"))
    lead = (d["datetime"].dt.normalize() - pd.Timestamp(start.date())).dt.days
    out = d[["datetime"]].copy()
    for v in VARS:
        out[v] = [d.at[i, v if k == 0 else f"{v}_previous_day{k}"] for i, k in zip(d.index, lead)]
    out["lead_day"] = lead.values
    return out


def score(pred: pd.Series, obs: pd.Series, tol: float) -> dict:
    e = (pred - obs).dropna()
    return {"n": int(len(e)), "MAE": float(e.abs().mean()), "MBE": float(e.mean()),
            "Hit(%)": float((e.abs() <= tol).mean() * 100)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2026-11-07", help="기준 시각(YYYY-MM-DD, 00시)")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--station", default="suwon", choices=list(M.STATIONS))
    ap.add_argument("--outdir", default="results")
    args = ap.parse_args()

    api_key = os.getenv("KMA_API_KEY")
    if not api_key:
        raise SystemExit("KMA_API_KEY가 없습니다 (.env 또는 환경변수).")

    start = datetime.strptime(args.start, "%Y-%m-%d")
    end = start + timedelta(days=args.days) - timedelta(hours=1)
    stn = M.STATIONS[args.station]
    lat, lon = M.STATION_META[stn]
    os.makedirs(args.outdir, exist_ok=True)
    tag = f"{args.station}_{start:%Y%m%d}_{args.days}d"

    # 1) 학습 — 기준 시각 이전 데이터만
    wins = M.build_training_windows(start, end, years_back=10, extra_days=7)
    asos_tr = pd.concat([fetch_range_asos(stn, s, e, api_key) for s, e, _ in wins], ignore_index=True)
    asos_tr = asos_tr.drop_duplicates("datetime")
    asos_tr = asos_tr[asos_tr["datetime"] < start].sort_values("datetime").reset_index(drop=True)
    for cfg in M.TARGETS.values():
        c = cfg["obs_col"]
        asos_tr[c] = pd.to_numeric(asos_tr[c], errors="coerce").interpolate(limit_direction="both")
    era = pd.concat([M.fetch_openmeteo_archive(lat, lon, s, e) for s, e, _ in wins], ignore_index=True)
    era = era.drop_duplicates("datetime")
    era = era[era["datetime"] < start].sort_values("datetime").reset_index(drop=True)
    print(f"[train] 마지막 학습 시각 = {asos_tr['datetime'].max()} (기준 시각 {start} 이전)")
    pack = M.train_mos_multi(asos_tr, era)

    # 2) 기준 시각에 발표된 예보로 예측
    raw = fetch_issued_forecast(lat, lon, start, args.days)
    mos = M.predict_mos_multi(pack, raw[["datetime"] + VARS].copy()).rename(columns={"날짜/시간": "datetime"})

    # 3) 실측 대조
    obs = fetch_range_asos(stn, start, end, api_key)
    obs = obs[(obs["datetime"] >= start) & (obs["datetime"] <= end)]
    obs = obs[["datetime", "temperature", "humidity", "wind_speed", "ca_tot"]].copy()
    for c in ["temperature", "humidity", "wind_speed", "ca_tot"]:
        obs[c] = pd.to_numeric(obs[c], errors="coerce")
    df = obs.merge(raw, on="datetime").merge(mos, on="datetime")

    raw_conv = {  # 원본 예보를 관측 단위로 변환 (Open-Meteo 풍속 km/h, 운량 %)
        "temperature": df["temperature_2m"],
        "humidity": df["relative_humidity_2m"],
        "wind_speed": df["wind_speed_10m"] / 3.6,
        "ca_tot": df["cloud_cover"] / 10.0,
    }
    mos_col = {"temperature": "예측 기온(°C)", "humidity": "예측 습도(%)",
               "wind_speed": "예측 풍속(m/s)", "ca_tot": "예측 전운량(0~10)"}
    label = {"temperature": "기온(°C)", "humidity": "습도(%)", "wind_speed": "풍속(m/s)", "ca_tot": "전운량(0~10)"}

    groups = [("전체", df.index == df.index)]
    for a, b in [(1, 2), (3, 4), (5, args.days)]:
        if a <= args.days:
            groups.append((f"{a}~{b}일차", df["lead_day"].between(a - 1, b - 1)))

    rows = []
    for t in ["temperature", "humidity", "wind_speed", "ca_tot"]:
        for gname, m in groups:
            r0 = score(raw_conv[t][m], df.loc[m, t], TOLERANCE[t])
            r1 = score(df.loc[m, mos_col[t]], df.loc[m, t], TOLERANCE[t])
            rows.append({"항목": label[t], "구간": gname, "n": r1["n"],
                         "원본 MAE": r0["MAE"], "보정 MAE": r1["MAE"],
                         "MAE 개선(%)": (r0["MAE"] - r1["MAE"]) / r0["MAE"] * 100,
                         "원본 적중률(%)": r0["Hit(%)"], "보정 적중률(%)": r1["Hit(%)"],
                         "허용 오차": TOLERANCE[t],
                         "원본 MBE": r0["MBE"], "보정 MBE": r1["MBE"]})
    summary = pd.DataFrame(rows)

    hourly = df.rename(columns={"temperature": "실측 기온(°C)", "humidity": "실측 습도(%)",
                                "wind_speed": "실측 풍속(m/s)", "ca_tot": "실측 전운량(0~10)"})
    hourly.to_csv(os.path.join(args.outdir, f"asof_{tag}_hourly.csv"), index=False, encoding="utf-8-sig")
    summary.to_csv(os.path.join(args.outdir, f"asof_{tag}_summary.csv"), index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 200)
    print(summary.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
