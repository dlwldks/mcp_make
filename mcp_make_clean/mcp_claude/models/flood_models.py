from pydantic import BaseModel

class CityRequest(BaseModel):
    city: str

class FloodRequest(BaseModel):
    lat: float
    lng: float
    rainfall: float
