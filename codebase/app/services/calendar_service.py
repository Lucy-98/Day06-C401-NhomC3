import uuid
from datetime import datetime, time, timedelta

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

SLOT_LABELS = {
    "morning": "morning",
    "noon": "noon",
    "afternoon": "afternoon",
    "evening": "evening",
    "morning_before_meal": "before breakfast",
    "morning_after_meal": "after breakfast",
    "noon_before_meal": "before lunch",
    "noon_after_meal": "after lunch",
    "afternoon_before_meal": "before afternoon meal",
    "afternoon_after_meal": "after afternoon meal",
    "evening_before_meal": "before dinner",
    "evening_after_meal": "after dinner",
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
            "X-WR-TIMEZONE:Asia/Ho_Chi_Minh",
        ]

        slots: dict[str, list[dict]] = {}
        for med in prescription.medicines:
            if med.schedule_mode in ["as_needed", "unknown"]:
                continue
            if not med.duration_days:
                continue

            for slot, dose in med.schedule.items():
                if not dose:
                    continue

                calendar_slot = self._choose_calendar_slot(slot, med.meal_timing)
                if calendar_slot not in slots:
                    slots[calendar_slot] = []

                slots[calendar_slot].append({
                    "med": med,
                    "dose": dose,
                })

        for calendar_slot, med_items in slots.items():
            if not med_items:
                continue

            reminder_time = (
                reminder_times.get(calendar_slot)
                or reminder_times.get(calendar_slot.split("_")[0])
                or "08:00"
            )
            hour, minute = map(int, reminder_time.split(":"))
            max_duration = max(item["med"].duration_days for item in med_items)

            for day_offset in range(max_duration):
                active_items = [
                    item
                    for item in med_items
                    if item["med"].duration_days and day_offset < item["med"].duration_days
                ]
                if not active_items:
                    continue

                event_date = start_date + timedelta(days=day_offset)
                dt = datetime.combine(event_date, time(hour=hour, minute=minute))
                dt_end = dt + timedelta(minutes=15)
                dt_utc = dt - timedelta(hours=7)
                dt_end_utc = dt_end - timedelta(hours=7)

                patient_name = prescription.patient_name or "Patient"
                slot_label = SLOT_LABELS.get(calendar_slot, calendar_slot)
                summary = (
                    f"Medicine reminder: {patient_name.title()} - "
                    f"{slot_label} {reminder_time}"
                )

                description_lines = [
                    f"Prescription: {prescription.title}",
                    f"Date: {event_date.isoformat()}",
                    "Medicines:",
                ]
                for item in active_items:
                    med = item["med"]
                    dose = item["dose"]
                    dose_text = amount_to_text(dose)
                    line = f"- {med.medicine_name}: {dose_text} {med.unit}"
                    if med.display_note:
                        line += f" ({med.display_note})"
                    description_lines.append(line)

                description = "\\n".join(description_lines)

                lines.extend([
                    "BEGIN:VEVENT",
                    f"UID:{uuid.uuid4()}@longchau-mock",
                    f"DTSTAMP:{now}",
                    f"DTSTART:{dt_utc.strftime('%Y%m%dT%H%M%SZ')}",
                    f"DTEND:{dt_end_utc.strftime('%Y%m%dT%H%M%SZ')}",
                    "STATUS:CONFIRMED",
                    "TRANSP:OPAQUE",
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

    def _escape_ics(self, text: str) -> str:
        text = str(text or "")
        return (
            text.replace("\\", "\\\\")
            .replace(",", "\\,")
            .replace(";", "\\;")
            .replace("\n", "\\n")
        )
