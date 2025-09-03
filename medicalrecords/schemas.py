from structured.pydantic.models import BaseModel
from datetime import date, time

class ValueRate(BaseModel):
    value: float
    rate: str
    
class VitalSigns(BaseModel):
    blood_pressure: str
    temp: float
    resp_rate: float
    height: float
    weight: float
    heart_rate: float
    
class DateAndTime(BaseModel):
    date: date
    time: time