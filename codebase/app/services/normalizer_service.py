import math
import re
import uuid
from datetime import datetime
from app.models.domain import Prescription, Medicine
from app.utils.parse_utils import (
    strip_accents,
    normalize_spaces,
    parse_decimal_or_fraction,
    to_int_if_possible,
    amount_to_text,
    extract_volume_ml,
)
from app.utils.date_utils import today_iso, add_days


SLOT_LABELS = {
    "morning": "Sáng",
    "noon": "Trưa",
    "afternoon": "Chiều",
    "evening": "Tối",
}


class PrescriptionNormalizer:
    def normalize(self, raw_json: dict, start_date: str | None = None, prescription_id: str | None = None) -> Prescription:
        data = raw_json.get("data", raw_json)

        prescription_id = prescription_id or str(uuid.uuid4())
        start_date = start_date or today_iso()

        medicines = [
            self._normalize_medicine(item)
            for item in data.get("table_information", [])
        ]

        valid_durations = [
            med.duration_days
            for med in medicines
            if med.duration_days and med.schedule_mode not in ["as_needed", "unknown"]
        ]

        prescription_days = max(valid_durations) if valid_durations else None
        end_date = add_days(start_date, prescription_days) if prescription_days else None

        warnings = []
        if any(m.needs_review for m in medicines):
            warnings.append("Một số thuốc cần người dùng hoặc dược sĩ kiểm tra lại trước khi tạo lịch.")
        if not prescription_days:
            warnings.append("Không tự tính được số ngày dùng chung cho đơn.")

        return Prescription(
            id=prescription_id,
            title=normalize_spaces(data.get("diagnose") or "Đơn thuốc"),
            hospital_name=data.get("hospital_name"),
            patient_name=data.get("patient_name"),
            patient_gender=data.get("patient_gender"),
            patient_address=data.get("patient_address"),
            diagnose=data.get("diagnose"),
            start_date=start_date,
            prescription_days=prescription_days,
            end_date=end_date,
            medicines=medicines,
            warnings=warnings,
        )

    def _normalize_medicine(self, item: dict) -> Medicine:
        guide = item.get("medicine_guide") or {}
        summary = guide.get("summary") or ""
        medicine_name = normalize_spaces(item.get("medicine_name") or "")
        total_amount = parse_decimal_or_fraction(item.get("medicine_count"))

        route = self._infer_route(guide)
        unit = self._infer_unit(guide, item.get("medicine_count"), medicine_name)
        schedule = self._normalize_fixed_schedule(guide)

        base = Medicine(
            no=item.get("no"),
            medicine_name=medicine_name,
            route=route,
            unit=unit,
            raw_total=item.get("medicine_count"),
            total_amount=to_int_if_possible(total_amount),
            raw_summary=summary,
            meal_timing=self._infer_meal_timing(summary),
            display_note=self._extract_display_note(summary),
        )

        if self._is_as_needed(summary):
            return self._build_as_needed(base, summary)

        if any(schedule.values()):
            return self._build_fixed_schedule(base, schedule, total_amount)

        if self._should_use_divided_dose(summary, schedule):
            return self._build_divided_dose(base, summary, total_amount)

        base.schedule_mode = "unknown"
        base.display_dose = normalize_spaces(summary)
        base.needs_review = True
        base.warnings.append("Không nhận diện được lịch dùng thuốc.")
        return base

    def _build_as_needed(self, base: Medicine, summary: str) -> Medicine:
        info = self._extract_as_needed_info(summary)

        base.schedule_mode = "as_needed"
        base.amount_per_intake = info["amount_per_intake"]
        base.amount_text = info["amount_text"]
        base.condition = info["condition"]
        base.min_interval_hours = info["min_interval_hours"]
        base.max_interval_hours = info["max_interval_hours"]
        base.duration_days = None
        base.display_dose = normalize_spaces(summary)
        base.needs_review = True
        base.warnings.append("Thuốc dùng khi cần, không tạo lịch nhắc cố định.")
        return base

    def _build_fixed_schedule(self, base: Medicine, schedule: dict, total_amount: float) -> Medicine:
        daily_total = sum(schedule.values())
        duration_days = math.ceil(total_amount / daily_total) if total_amount and daily_total else None

        base.schedule_mode = "fixed_schedule"
        base.schedule = {k: to_int_if_possible(v) for k, v in schedule.items()}
        base.daily_total = to_int_if_possible(daily_total)
        base.duration_days = duration_days
        base.display_dose = self._display_dose_from_schedule(schedule, base.unit)

        if not duration_days:
            base.needs_review = True
            base.warnings.append("Không tính được số ngày dùng vì thiếu tổng số lượng hoặc liều/ngày.")

        return base

    def _build_divided_dose(self, base: Medicine, summary: str, total_amount: float) -> Medicine:
        daily_total = self._extract_daily_total(summary)
        times_per_day = self._infer_times_per_day(summary)

        amount_per_intake = None
        if daily_total and times_per_day:
            amount_per_intake = daily_total / times_per_day

        bottle_volume_ml = extract_volume_ml(base.medicine_name)

        duration_days = None
        if bottle_volume_ml and daily_total:
            duration_days = math.ceil(bottle_volume_ml / daily_total)
        elif total_amount and daily_total:
            duration_days = math.ceil(total_amount / daily_total)

        suggested_slots = self._infer_suggested_slots(times_per_day)
        schedule = {
            slot: to_int_if_possible(amount_per_intake)
            for slot in suggested_slots
            if amount_per_intake
        }

        base.schedule_mode = "divided_dose"
        base.schedule = schedule
        base.daily_total = to_int_if_possible(daily_total)
        base.times_per_day = times_per_day
        base.amount_per_intake = to_int_if_possible(amount_per_intake)
        base.amount_text = amount_to_text(amount_per_intake)
        base.bottle_volume_ml = to_int_if_possible(bottle_volume_ml)
        base.suggested_slots = suggested_slots
        base.duration_days = duration_days
        base.display_dose = self._display_dose_from_schedule(schedule, base.unit) if schedule else normalize_spaces(summary)

        if not daily_total or not times_per_day or not duration_days:
            base.needs_review = True
            base.warnings.append("Cần kiểm tra lại liều chia lần hoặc dung tích thuốc.")

        if re.search(r"\b(7|8|9|10|11|12)\s+lan\b", strip_accents(summary)):
            base.needs_review = True
            base.warnings.append("Số lần/ngày bất thường, có thể OCR đọc sai.")

        return base

    def _infer_unit(self, guide: dict, medicine_count, medicine_name: str) -> str:
        raw = " ".join([
            str(guide.get("type") or ""),
            str(medicine_count or ""),
            str(guide.get("summary") or ""),
            str(medicine_name or "")
        ])
        text = strip_accents(raw)

        if "ml" in text:
            return "ml"
        if "vien" in text:
            return "Viên"
        if "goi" in text:
            return "Gói"
        if "tui" in text:
            return "Túi"
        if "chai" in text:
            return "Chai"
        if "ong" in text:
            return "Ống"
        if "lo" in text:
            return "Lọ"
        return normalize_spaces(guide.get("type") or "") or "Đơn vị"

    def _infer_route(self, guide: dict) -> str:
        raw = " ".join([
            str(guide.get("use") or ""),
            str(guide.get("summary") or ""),
            str(guide.get("note") or ""),
        ])
        text = strip_accents(raw)

        if "dat am dao" in text:
            return "Đặt âm đạo"
        if "boi" in text:
            return "Bôi"
        if "nho" in text:
            return "Nhỏ"
        if "ngam" in text:
            return "Ngậm"
        return normalize_spaces(guide.get("use")) or "Uống"

    def _infer_meal_timing(self, summary: str):
        text = strip_accents(summary)
        if "truoc an" in text:
            return "before_meal"
        if "sau an" in text:
            return "after_meal"
        if "trong khi an" in text or "cung bua an" in text:
            return "with_meal"
        return None

    def _extract_display_note(self, summary: str):
        text = strip_accents(summary)
        notes = []

        if "truoc an" in text:
            notes.append("Trước ăn")
        if "sau an" in text:
            notes.append("Sau ăn")
        if "chong mat" in text:
            notes.append("Có thể chóng mặt khi mới dùng")
        if "sot" in text and "38.5" in text:
            notes.append("Khi sốt ≥ 38.5°C")
        if "cach" in text and ("4" in text or "6" in text):
            notes.append("Cách 4–6 giờ nếu cần")

        return ", ".join(notes) if notes else None

    def _normalize_fixed_schedule(self, guide: dict) -> dict:
        summary = guide.get("summary") or ""

        schedule = {
            "morning": parse_decimal_or_fraction(guide.get("guide_morning")),
            "noon": parse_decimal_or_fraction(guide.get("guide_noon")),
            "afternoon": parse_decimal_or_fraction(guide.get("guide_afternoon")),
            "evening": parse_decimal_or_fraction(guide.get("guide_evening")),
        }

        for slot in schedule:
            if not schedule[slot]:
                schedule[slot] = self._find_slot_amount(summary, slot)

        return schedule

    def _find_slot_amount(self, summary: str, slot: str) -> float:
        text = strip_accents(summary)
        slot_words = {
            "morning": "sang",
            "noon": "trua",
            "afternoon": "chieu",
            "evening": "toi",
        }
        word = slot_words[slot]

        patterns = [
            rf"{word}\s*[:\-]?\s*(\d+(?:[.,]\d+)?|\d+\s*/\s*\d+|i|l)\s*(vien|goi|tui|ml|ong|chai|lo)?",
            rf"buoi\s+{word}\s*[:\-]?\s*(\d+(?:[.,]\d+)?|\d+\s*/\s*\d+|i|l)\s*(vien|goi|tui|ml|ong|chai|lo)?",
            rf"(\d+(?:[.,]\d+)?|\d+\s*/\s*\d+|i|l)\s*(vien|goi|tui|ml|ong|chai|lo)?\s*buoi\s+{word}",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return parse_decimal_or_fraction(match.group(1))

        return 0.0

    def _display_dose_from_schedule(self, schedule: dict, unit: str) -> str:
        parts = []
        for slot in ["morning", "noon", "afternoon", "evening"]:
            amount = schedule.get(slot) or 0
            if amount:
                parts.append(f"{SLOT_LABELS[slot]} {amount_to_text(amount)} {unit}")
        return ", ".join(parts)

    def _should_use_divided_dose(self, summary: str, schedule: dict) -> bool:
        text = strip_accents(summary)
        has_no_slots = all(not v for v in schedule.values())
        return has_no_slots and ("chia" in text or self._extract_daily_total(summary) is not None)

    def _extract_daily_total(self, summary: str):
        text = strip_accents(summary)
        match = re.search(r"ngay\s+uong\s+(\d+(?:[.,]\d+)?|\d+\s*/\s*\d+)\s*(ml|goi|tui|vien|ong|chai|lo)", text)
        if match:
            return parse_decimal_or_fraction(match.group(1))
        return None

    def _infer_times_per_day(self, summary: str):
        text = strip_accents(summary)

        match = re.search(r"chia\s+(\d+)\s+lan", text)
        if match:
            return int(match.group(1))

        match = re.search(r"ngay\s+uong\s+(\d+)\s+lan", text)
        if match:
            return int(match.group(1))

        match = re.search(r"(\d+)\s+lan", text)
        if match:
            n = int(match.group(1))
            if 1 <= n <= 6:
                return n

        return None

    def _infer_suggested_slots(self, times_per_day):
        if times_per_day == 1:
            return ["morning"]
        if times_per_day == 2:
            return ["morning", "evening"]
        if times_per_day == 3:
            return ["morning", "noon", "afternoon"]
        if times_per_day == 4:
            return ["morning", "noon", "afternoon", "evening"]
        return []

    def _is_as_needed(self, summary: str) -> bool:
        text = strip_accents(summary)
        keywords = [
            "khi sot",
            "khi dau",
            "khi can",
            "neu sot",
            "neu dau",
            "cach 4",
            "cach 6",
            "4-6h",
            "4 - 6 h",
            "38.5",
        ]
        return any(k in text for k in keywords)

    def _extract_as_needed_info(self, summary: str) -> dict:
        text = strip_accents(summary)

        info = {
            "condition": None,
            "amount_per_intake": None,
            "amount_text": None,
            "min_interval_hours": None,
            "max_interval_hours": None,
        }

        dose_match = re.search(r"uong\s+(\d+(?:[.,]\d+)?|\d+\s*/\s*\d+)\s*(ml|vien|goi|tui|ong)", text)
        if dose_match:
            amount = parse_decimal_or_fraction(dose_match.group(1))
            info["amount_per_intake"] = to_int_if_possible(amount)
            info["amount_text"] = amount_to_text(amount)

        if "sot" in text and "38.5" in text:
            info["condition"] = "Khi sốt ≥ 38.5°C"
        elif "khi sot" in text:
            info["condition"] = "Khi sốt"
        elif "khi dau" in text:
            info["condition"] = "Khi đau"
        elif "khi can" in text:
            info["condition"] = "Khi cần"

        interval_match = re.search(r"cach\s+(\d+)\s*[-–]\s*(\d+)\s*h", text)
        if interval_match:
            info["min_interval_hours"] = int(interval_match.group(1))
            info["max_interval_hours"] = int(interval_match.group(2))

        return info
