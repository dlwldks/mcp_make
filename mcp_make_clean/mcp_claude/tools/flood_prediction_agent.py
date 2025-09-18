"""
🌊 Flood Prediction Agent (Batch)
- 역할: 여러 지역의 데이터를 받아 pandas로 침수 위험도 예측
- 입력: 각 지역의 rain_mm, ground_level 포함된 리스트
- 방식: rule 기반 + pandas 처리
"""

import pandas as pd
from pydantic import BaseModel
from typing import List

class RegionData(BaseModel):
    location: str
    rain_mm: float
    ground_level: float

class FloodBatchRequest(BaseModel):
    regions: List[RegionData]

def predict_flood_batch(data: FloodBatchRequest) -> str:
    df = pd.DataFrame([region.dict() for region in data.regions])

    def judge(row):
        if row["rain_mm"] > 80 and row["ground_level"] < 5:
            return "높음"
        elif row["rain_mm"] > 50:
            return "보통"
        else:
            return "낮음"

    df["flood_risk"] = df.apply(judge, axis=1)

    return df.to_markdown(index=False)
