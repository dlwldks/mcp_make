#mos_all 다음으로 실행 -> realtime_make_obs.py -> accuracy_percentage.py

import pandas as pd
import numpy as np
from math import sqrt
from pathlib import Path

# ---- 사용자 입력 ----
CSV_PATH = "mos_multi_realtime_suwon_2025120112_2025123112_with_obs_eval.csv"  # <- CSV 경로 수정
SAVE_PREFIX = "accuracy_result"  # 출력 파일 앞에 붙는 이름

# ---- 한글 컬럼 이름 매핑 ----
COLS = {
    "기온":     {"pred": "예측 기온(°C)",      "actual": "실측 기온(°C)"},
    "습도":     {"pred": "예측 습도(%)",        "actual": "실측 습도(%)"},
    "풍속":     {"pred": "예측 풍속(m/s)",      "actual": "실측 풍속(m/s)"},
    "전운량":   {"pred": "예측 전운량(0~10)",   "actual": "실측 전운량(0~10)"},
}

# ---- 타깃별 합리적 기본 범위 (fallback) ----
DEFAULT_RANGE = {
    "기온": 40.0,
    "습도": 100.0,
    "풍속": 15.0,
    "전운량": 10.0,
}

# ---- 타깃별 허용 오차(히트율 계산용) ----
TOLERANCE = {
    "기온": 2.0,
    "습도": 10.0,
    "풍속": 1.5,
    "전운량": 2.0,
}


def clamp_pct(x):
    return float(np.clip(x, 0.0, 100.0))


# ---- 비율 기반 정확도 (기온, 습도용) ----
def compute_accuracy_ratio_based(y_true, y_pred):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    if not mask.any():
        return np.nan
    acc_each = 100.0 * (1.0 - np.abs(y_pred[mask] - y_true[mask]) / np.maximum(np.abs(y_true[mask]), 1e-6))
    acc_each = np.clip(acc_each, 0.0, 100.0)
    return float(np.mean(acc_each))


# ---- 범위 기반 정확도 (풍속, 전운량용) ----
def compute_accuracy_range_based(y_true, y_pred, target_name: str):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    if not mask.any():
        return np.nan

    yt = y_true[mask]
    yp = y_pred[mask]

    observed_range = float(np.max(yt) - np.min(yt))
    base_range = DEFAULT_RANGE.get(target_name, None)
    R = observed_range if observed_range >= 1e-6 else base_range

    acc_each = 100.0 * (1.0 - np.abs(yp - yt) / R)
    acc_each = np.clip(acc_each, 0.0, 100.0)
    return float(np.mean(acc_each))


def mape_percent(y_true, y_pred):
    mask = np.isfinite(y_true) & np.isfinite(y_pred) & (np.abs(y_true) > 1e-6)
    if not mask.any():
        return np.nan
    return float(np.mean(np.abs((y_pred[mask] - y_true[mask]) / y_true[mask])) * 100.0)


def hit_rate_percent(y_true, y_pred, target_name: str):
    tol = TOLERANCE.get(target_name)
    if tol is None:
        return np.nan

    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    if not mask.any():
        return np.nan

    diff = np.abs(y_pred[mask] - y_true[mask])
    hit = diff <= tol
    return float(np.mean(hit) * 100.0)


# ---- 통계 계산 ----
def compute_stats(df, pred_col, act_col, target_name: str):
    out = {}
    y_pred = pd.to_numeric(df[pred_col], errors="coerce")
    y_true = pd.to_numeric(df[act_col], errors="coerce")

    mask = y_pred.notna() & y_true.notna()
    n = int(mask.sum())
    out["n"] = n

    if n == 0:
        out.update({k: np.nan for k in ["MAE","RMSE","MBE","MAPE(%)","Accuracy(%)","Hit-Rate(%)"]})
        return out

    e = (y_pred[mask] - y_true[mask]).to_numpy()

    out["MAE"] = float(np.mean(np.abs(e)))
    out["RMSE"] = float(np.sqrt(np.mean(e**2)))
    out["MBE"] = float(np.mean(e))
    out["MAPE(%)"] = mape_percent(y_true[mask].to_numpy(), y_pred[mask].to_numpy())

    # 정확도
    if target_name in ["기온","습도"]:
        acc = compute_accuracy_ratio_based(y_true[mask], y_pred[mask])
    else:
        acc = compute_accuracy_range_based(y_true[mask], y_pred[mask], target_name)
    out["Accuracy(%)"] = acc

    # Hit-Rate
    out["Hit-Rate(%)"] = hit_rate_percent(y_true[mask], y_pred[mask], target_name)

    return out


# ---- 특정 그룹 전체 타깃 계산 ----
def compute_all_targets_stats(df, group_label: str):
    rows = []
    for name, cfg in COLS.items():
        pred, act = cfg["pred"], cfg["actual"]

        if pred not in df.columns or act not in df.columns:
            continue

        stats = compute_stats(df, pred, act, target_name=name)

        row = {
            "group": group_label,
            "target": name,
            **stats
        }
        rows.append(row)
    return rows


def main():
    path = Path(CSV_PATH)
    df = pd.read_csv(path)
    df["날짜/시간"] = pd.to_datetime(df["날짜/시간"], errors="coerce")

    print(f"\n[파일] {path.resolve()}")

    # ===========================================================
    # [1] 전체 기간 요약
    # ===========================================================
    summary_rows = []
    for name, cfg in COLS.items():
        stats = compute_stats(df, cfg["pred"], cfg["actual"], target_name=name)
        summary_rows.append({"target": name, **stats})

    summary_df = pd.DataFrame(summary_rows)
    print("\n=== [1] 전체 기간 요약 ===")
    print(summary_df)

    # CSV 저장
    summary_df.to_csv(f"{SAVE_PREFIX}_summary_total.csv", index=False, encoding="utf-8-sig")

    # ===========================================================
    # [2] 날짜별 요약
    # ===========================================================
    df["date"] = df["날짜/시간"].dt.date
    daily_rows = []

    for d, sdf in df.groupby("date"):
        daily_rows.extend(compute_all_targets_stats(sdf, group_label=str(d)))

    daily_df = pd.DataFrame(daily_rows)
    print("\n=== [2] 날짜별 요약 ===")
    print(daily_df)

    daily_df.to_csv(f"{SAVE_PREFIX}_summary_daily.csv", index=False, encoding="utf-8-sig")

    # ===========================================================
    # [3] 리드타임 구간 요약
    # ===========================================================
    df = df.sort_values("날짜/시간").reset_index(drop=True)
    df["lead_hours"] = df.index * 1.0

    lead_bins = [0,24,48,72,120,np.inf]
    lead_labels = ["0-24h","24-48h","48-72h","72-120h","120h+"]

    df["lead_bin"] = pd.cut(df["lead_hours"], bins=lead_bins, labels=lead_labels, right=False)

    lt_rows = []
    for b, sdf in df.groupby("lead_bin"):
        lt_rows.extend(compute_all_targets_stats(sdf, group_label=str(b)))

    lt_df = pd.DataFrame(lt_rows)
    print("\n=== [3] 리드타임 구간 요약 ===")
    print(lt_df)

    lt_df.to_csv(f"{SAVE_PREFIX}_summary_leadtime.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
