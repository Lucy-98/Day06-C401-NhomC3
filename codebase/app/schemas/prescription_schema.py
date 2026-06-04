from typing import Any, Optional
from pydantic import BaseModel, Field


class NormalizeDemoRequest(BaseModel):
    raw_json: dict[str, Any]
    start_date: Optional[str] = None


class ReminderTimeUpdateRequest(BaseModel):
    times: dict[str, str] = Field(
        default_factory=dict,
        examples=[{
            "morning": "07:30",
            "noon": "12:00",
            "afternoon": "15:00",
            "evening": "21:00",
            "morning_before_meal": "07:00",
            "morning_after_meal": "07:45"
        }]
    )
    add_to_device_calendar: bool = False


class MedicineEditRequest(BaseModel):
    medicine_name: Optional[str] = None
    schedule: Optional[dict[str, float]] = None
    duration_days: Optional[int] = None
    display_note: Optional[str] = None


class PrescriptionEditRequest(BaseModel):
    title: Optional[str] = None
    start_date: Optional[str] = None
    prescription_days: Optional[int] = None
    medicines: Optional[list[MedicineEditRequest]] = None