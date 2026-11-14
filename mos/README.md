# MOS — 수치예보 지점 편향 보정 및 재현 평가

Open-Meteo 수치예보를 기상청 ASOS 관측소 지점값으로 보정하는 Gradient Boosting 모델과, 과거 시점의 실시간 예측을 재현해 실측과 대조하는 평가 코드.

## 파일

| 파일 | 내용 |
|---|---|
| `mos_all.py` | 보정 모델 학습·예측 (backtest / realtime 모드) |
| `realtime_make_obs.py` | realtime 예측 결과에 사후 관측값 병합 |
| `accuracy_percentage.py` | 전체·일별·리드타임별 MAE, RMSE, MBE, 적중률 산출 |
| `eval_asof.py` | 과거 기준 시각으로 돌아가 실시간 예측을 재현하고 실측과 대조 |
| `results/` | `eval_asof.py` 실행 결과 |

## 보정 모델

- 모델: scikit-learn `GradientBoostingRegressor` (기본 하이퍼파라미터), 기온·습도·풍속·전운량 4개 타깃을 `MultiOutputRegressor`로 각각 학습
- 입력 피처: 기온, 상대습도, 풍속, 운량, 지상기압 + 각 변수의 1·3·6시간 lag + 시각·월·시각 sin/cos
- 학습 데이터: 예측 구간과 같은 날짜의 과거 10년 + 예측 직전 7일. 피처는 ERA5 재분석(Open-Meteo Archive), 라벨은 ASOS 시간 관측
- 성격: 학습 입력이 재분석, 예측 입력이 예보이므로 예보 오차가 아니라 격자값과 관측소 지점값의 차이(지점 편향)를 보정함

## 재현 평가 방법 (`eval_asof.py`)

1. 기준 시각을 정하고 그 이전 데이터로만 모델을 학습
2. 기준 시각에 발표된 예보를 입력으로 사용 (Open-Meteo Previous Runs API, k일차 = k일 전 발표 예보)
3. 같은 기간 ASOS 관측값과 대조. 관측값은 채점에만 사용
4. 원본 예보와 보정 결과를 같은 조건에서 비교

```bash
# .env 에 KMA_API_KEY=<기상청 API허브 키>
pip install pandas numpy scikit-learn requests python-dotenv
python eval_asof.py --start 2026-11-07 --days 7 --station suwon
```

## 결과: 수원(119), 기준 시각 2026-11-07 00시, 7일(168시간)

마지막 학습 시각: 2026-11-06 23시

| 항목 | 원본 예보 MAE | 보정 MAE | MAE 변화 | 원본 적중률 | 보정 적중률 | 허용 오차 |
|---|---|---|---|---|---|---|
| 기온 | 2.04 °C | 1.12 °C | −45% | 48.2% | 83.9% | ±2 °C |
| 풍속 | 0.84 m/s | 0.47 m/s | −44% | 85.7% | 100% | ±1.5 m/s |
| 습도 | 13.5 %p | 14.7 %p | +9% | 51.2% | 52.4% | ±10 %p |
| 전운량 | 2.19 | 2.61 | +19% | 60.7% | 52.4% | ±2 |

일차별 기온 MAE (원본 → 보정): 1~2일차 3.07 → 1.47 °C, 3~4일차 1.92 → 0.80 °C, 5~7일차 1.44 → 1.09 °C

상세: `results/asof_suwon_20261107_7d_summary.csv`, 시간별 값: `results/asof_suwon_20261107_7d_hourly.csv`

## 한계

- 평가 기간 1주, 관측소 1곳
- 습도·전운량은 보정 효과 없음. 1~2일차 습도는 원본 예보부터 편향이 크며(+25 %p) 보정 후 증가함
- 학습 입력(ERA5)과 예측 입력(발표 예보)이 다름. 과거 발표 예보로 학습하면 예보 오차까지 보정 가능
- `accuracy_percentage.py`의 기온·습도 `Accuracy(%)`는 실측값 대비 비율로 계산하므로 기온이 0 °C 부근일 때 값이 왜곡됨. 기온 평가는 MAE와 적중률 사용
