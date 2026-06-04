from typing import Any, Optional

from pydantic import BaseModel, Field


class HomeReminderView(BaseModel):
    selected_date: str
    week_strip: list[dict[str, Any]]
    has_reminders: bool
    empty_state: Optional[dict[str, str]] = None
    reminders: list[dict[str, Any]] = Field(default_factory=list)


class CreatePrescriptionView(BaseModel):
    prescription_id: str
    screen: str = "create_prescription"
    title: str
    hospital_name: Optional[str] = None
    patient_name: Optional[str] = None
    patient_gender: Optional[str] = None
    patient_address: Optional[str] = None
    diagnose: Optional[str] = None
    start_date: str
    days_label: str = "So ngay dung"
    prescription_days: Optional[int]
    end_date: Optional[str]
    medicines: list[dict[str, Any]]
    warnings: list[str] = Field(default_factory=list)
    can_continue_to_schedule: bool


class ScheduleReminderView(BaseModel):
    prescription_id: str
    screen: str = "schedule_reminder"
    title: str
    date_range_text: str
    reminder_times: dict[str, str]
    active_slots: list[dict[str, Any]]
    app_notification_enabled: bool = True
    device_calendar_enabled: bool = False
    calendar_url: str
    warnings: list[str] = Field(default_factory=list)
