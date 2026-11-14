#mos_all 다음으로 실행 -> realtime_make_obs.py -> accuracy_percentage.py
import os
import pandas as pd
from datetime import timedelta
from mos_all import (   # mos_all 파일 이름에 맞게 import 해줘
    STATIONS,
    KMA_API_KEY,
    fetch_range_asos,
    evaluate_predictions,
)

STATION_KEY = "suwon"  # 그때 돌렸던 지점
PRED_CSV = "mos_multi_realtime_suwon_2025120112_2025123112.csv"  # 그때 나온 파일 이름으로 수정

if __name__ == "__main__":
    # 1) 예측 CSV 불러오기
    pred_df = pd.read_csv(PRED_CSV, parse_dates=["날짜/시간"])

    # 2) 예측 기간 구간 계산
    start = pred_df["날짜/시간"].min()
    end = pred_df["날짜/시간"].max() + timedelta(hours=1)  # 끝 시간은 [start, end) 방식이라 +1시간

    print(f"[INFO] 평가 기간: {start} ~ {end}")

    # 3) 해당 기간 ASOS 관측 가져오기
    stn_id = STATIONS[STATION_KEY]
    asos_eval = fetch_range_asos(stn_id, start, end, KMA_API_KEY, show_progress=True)

    # 숫자로 변환
    for col in ["temperature", "humidity", "wind_speed", "ca_tot"]:
        asos_eval[col] = pd.to_numeric(asos_eval[col], errors="coerce")

    # 4) 기존 evaluate_predictions() 재사용
    metrics, merged = evaluate_predictions(pred_df, asos_eval)

    # 5) 저장
    merged_name = PRED_CSV.replace(".csv", "_with_obs_eval.csv")
    merged.to_csv(merged_name, index=False, encoding="utf-8-sig")

    print("\n=== 리얼타임 예측 사후 평가 결과 ===")
    for k, v in metrics.items():
        print(f"- {k}: n={v['n']}, MAE={v['MAE']:.2f}, RMSE={v['RMSE']:.2f}, MBE={v['MBE']:.2f}")

    print("\n📄 예측+실측 병합 저장:", merged_name)
