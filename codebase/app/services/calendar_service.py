import uuid
from datetime import datetime, time
from app.models.domain import Prescription
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


class CalendarService:
    def build_ics(self, prescription: Prescription, custom_times: dict[str, str] | None = None) -> str:
        reminder_times = {**DEFAULT_REMINDER_TIMES, **(custom_times or {})}

        start_date = datetime.fromisoformat(prescription.start_date).date()
        now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//LongChau Mock//Medicine Reminder//VN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
        ]

        for med in prescription.medicines:
            if med.schedule_mode in ["as_needed", "unknown"]:
                continue
            if not med.duration_days:
                continue

            for slot, dose in med.schedule.items():
                if not dose:
                    continue

                calendar_slot = self._choose_calendar_slot(slot, med.meal_timing)
                reminder_time = reminder_times.get(calendar_slot) or reminder_times.get(slot) or "08:00"
                hour, minute = map(int, reminder_time.split(":"))

                dt = datetime.combine(start_date, time(hour=hour, minute=minute))

                dose_text = amount_to_text(dose)
                summary = f"{med.route} {dose_text} {med.unit} - {med.medicine_name}"

                if med.display_note:
                    summary += f" ({med.display_note})"

                description = (
                    f"Đơn: {prescription.title}\\n"
                    f"Thuốc: {med.medicine_name}\\n"
                    f"Hướng dẫn: {med.raw_summary}\\n"
                    f"Số ngày thuốc này: {med.duration_days}\\n"
                )

                lines.extend([
                    "BEGIN:VEVENT",
                    f"UID:{uuid.uuid4()}@longchau-mock",
                    f"DTSTAMP:{now}",
                    f"DTSTART:{dt.strftime('%Y%m%dT%H%M%S')}",
                    "DURATION:PT10M",
                    f"RRULE:FREQ=DAILY;COUNT={med.duration_days}",
                    f"SUMMARY:{self._escape_ics(summary)}",
                    f"DESCRIPTION:{self._escape_ics(description)}",
                    "END:VEVENT",
                ])

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines)

    def _choose_calendar_slot(self, slot: str, meal_timing: str | None) -> str:
        if meal_timing == "before_meal":
            return f"{slot}_before_meal"
        if meal_timing == "after_meal":
            return f"{slot}_after_meal"
        return slot

    def _escape_ics(self, text) -> str:
        text = str(text or "")
        return (
            text.replace("\\", "\\\\")
            .replace(",", "\\,")
            .replace(";", "\\;")
            .replace("\n", "\\n")
        )
