# models/responses.py

from pydantic import BaseModel

class WeatherResponse(BaseModel):
    summary: str

class RainfallResponse(BaseModel):
    rainfall_mm: float

class FloodRiskResponse(BaseModel):
    risk_level: str  # '낮음', '보통', '높음'

class ElevationResponse(BaseModel):
    lat: float
    lng: float
    elevation_m: float

class EvacuationResponse(BaseModel):
    route_summary: str

class FloodInfoResponse(BaseModel):
    city: str
    lat: float
    lng: float
    rainfall_mm: float
    risk_level: str  # '낮음', '보통', '높음'
