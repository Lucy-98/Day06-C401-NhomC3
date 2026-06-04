from datetime import datetime
from app.models.domain import Prescription
from app.schemas.view_schema import HomeReminderView, CreatePrescriptionView, ScheduleReminderView
from app.utils.date_utils import build_week_strip, format_vn_date_range
from app.utils.parse_utils import amount_to_text


DEFAULT_REMINDER_TIMES = {
    "morning": "07:30",
    "noon": "12:00",
    "afternoon": "15:00",
    "evening": "21:00",

    "morning_before_meal": "07:00",
    "morning_after_meal": "07:45",
    "noon_before_meal": "11:30",
    "noon_after_meal": "12:30",
    "afternoon_before_meal": "15:00",
    "afternoon_after_meal": "15:30",
    "evening_before_meal": "18:00",
    "evening_after_meal": "19:30",
}

SLOT_LABELS = {
    "morning": "Sáng",
    "noon": "Trưa",
    "afternoon": "Chiều",
    "evening": "Tối",
}


class ViewBuilderService:
    def build_home_view(self, selected_date: str, reminders: list[dict] | None = None) -> HomeReminderView:
        reminders = reminders or []

        return HomeReminderView(
            selected_date=selected_date,
            week_strip=build_week_strip(selected_date),
            has_reminders=bool(reminders),
            empty_state=None if reminders else {
                "title": "Hôm nay bạn chưa có lịch nhắc uống thuốc",
                "subtitle": "Hãy tạo lịch nhắc uống thuốc mới",
                "primary_action": "Tạo lịch nhắc",
            },
            reminders=reminders,
        )

    def build_create_prescription_view(self, prescription: Prescription) -> CreatePrescriptionView:
        medicines = []
        for med in prescription.medicines:
            medicines.append({
                "no": med.no,
                "medicine_name": med.medicine_name,
                "unit": med.unit,
                "route": med.route,
                "raw_total": med.raw_total,
                "total_amount": med.total_amount,
                "raw_summary": med.raw_summary,
                "schedule_mode": med.schedule_mode,
                "schedule": med.schedule,
                "daily_total": med.daily_total,
                "display_dose": med.display_dose,
                "display_note": med.display_note,
                "duration_days": med.duration_days,
                "meal_timing": med.meal_timing,
                "times_per_day": med.times_per_day,
                "amount_per_intake": med.amount_per_intake,
                "amount_text": med.amount_text,
                "suggested_slots": med.suggested_slots,
                "bottle_volume_ml": med.bottle_volume_ml,
                "condition": med.condition,
                "min_interval_hours": med.min_interval_hours,
                "max_interval_hours": med.max_interval_hours,
                "needs_review": med.needs_review,
                "warnings": med.warnings,
                "editable": True,
            })

        return CreatePrescriptionView(
            prescription_id=prescription.id,
            title=prescription.title,
            hospital_name=prescription.hospital_name,
            patient_name=prescription.patient_name,
            patient_gender=prescription.patient_gender,
            patient_address=prescription.patient_address,
            diagnose=prescription.diagnose,
            start_date=prescription.start_date,
            prescription_days=prescription.prescription_days,
            end_date=prescription.end_date,
            medicines=medicines,
            warnings=prescription.warnings,
            can_continue_to_schedule=bool(prescription.prescription_days),
        )

    def build_schedule_view(self, prescription: Prescription) -> ScheduleReminderView:
        active_slots = self._extract_active_slots(prescription)

        return ScheduleReminderView(
            prescription_id=prescription.id,
            title=prescription.title,
            date_range_text=format_vn_date_range(prescription.start_date, prescription.end_date),
            reminder_times=DEFAULT_REMINDER_TIMES,
            active_slots=active_slots,
            calendar_url=f"/api/prescriptions/{prescription.id}/calendar.ics",
            warnings=prescription.warnings,
        )

    def _extract_active_slots(self, prescription: Prescription) -> list[dict]:
        slots = {}

        for med in prescription.medicines:
            if med.schedule_mode in ["as_needed", "unknown"]:
                continue

            for slot, dose in med.schedule.items():
                if not dose:
                    continue

                calendar_slot = self._choose_calendar_slot(slot, med.meal_timing)
                if calendar_slot not in slots:
                    slots[calendar_slot] = {
                        "slot": calendar_slot,
                        "label": self._slot_label(slot, med.meal_timing),
                        "time": DEFAULT_REMINDER_TIMES.get(calendar_slot, DEFAULT_REMINDER_TIMES.get(slot, "08:00")),
                        "medicines": []
                    }

                slots[calendar_slot]["medicines"].append({
                    "medicine_name": med.medicine_name,
                    "route": med.route,
                    "schedule_mode": med.schedule_mode,
                    "dose": f"{amount_to_text(dose)} {med.unit}",
                    "note": med.display_note,
                    "duration_days": med.duration_days,
                })

        order = [
            "morning_before_meal", "morning", "morning_after_meal",
            "noon_before_meal", "noon", "noon_after_meal",
            "afternoon_before_meal", "afternoon", "afternoon_after_meal",
            "evening_before_meal", "evening", "evening_after_meal",
        ]

        return sorted(slots.values(), key=lambda x: order.index(x["slot"]) if x["slot"] in order else 999)

    def _choose_calendar_slot(self, slot: str, meal_timing: str | None) -> str:
        if meal_timing == "before_meal":
            return f"{slot}_before_meal"
        if meal_timing == "after_meal":
            return f"{slot}_after_meal"
        return slot

    def _slot_label(self, slot: str, meal_timing: str | None) -> str:
        base = SLOT_LABELS.get(slot, slot)
        if meal_timing == "before_meal":
            return f"{base} trước ăn"
        if meal_timing == "after_meal":
            return f"{base} sau ăn"
        return base
