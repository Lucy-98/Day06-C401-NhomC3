from typing import Any, Optional, Literal
from pydantic import BaseModel, Field


ScheduleMode = Literal["fixed_schedule", "divided_dose", "as_needed", "unknown"]


class Medicine(BaseModel):
    no: Optional[int] = None
    medicine_name: str = ""
    route: str = "Uống"
    unit: str = "Đơn vị"

    raw_total: Any = None
    total_amount: Optional[float | int] = None

    raw_summary: str = ""
    schedule_mode: ScheduleMode = "unknown"

    schedule: dict[str, float | int] = Field(default_factory=dict)
    daily_total: Optional[float | int] = None
    duration_days: Optional[int] = None

    meal_timing: Optional[str] = None
    display_note: Optional[str] = None
    display_dose: Optional[str] = None

    times_per_day: Optional[int] = None
    amount_per_intake: Optional[float | int] = None
    amount_text: Optional[str] = None
    suggested_slots: list[str] = Field(default_factory=list)
    bottle_volume_ml: Optional[float | int] = None

    condition: Optional[str] = None
    min_interval_hours: Optional[int] = None
    max_interval_hours: Optional[int] = None

    needs_review: bool = False
    warnings: list[str] = Field(default_factory=list)


class Prescription(BaseModel):
    id: str
    title: str
    hospital_name: Optional[str] = None
    patient_name: Optional[str] = None
    patient_gender: Optional[str] = None
    patient_address: Optional[str] = None
    diagnose: Optional[str] = None

    start_date: str
    prescription_days: Optional[int] = None
    end_date: Optional[str] = None

    medicines: list[Medicine] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
