import re
import unicodedata
from fractions import Fraction
from typing import Any, Optional


def strip_accents(text: Any) -> str:
    if text is None:
        return ""
    text = str(text)
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.lower().strip()


def normalize_spaces(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def to_int_if_possible(value):
    if value is None:
        return None
    try:
        f = float(value)
    except Exception:
        return value
    return int(f) if f.is_integer() else round(f, 4)


def parse_decimal_or_fraction(value: Any) -> float:
    if value is None:
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    text = normalize_spaces(value)
    text = re.sub(r"\b[IiLl]\b", "1", text)

    fraction_match = re.search(r"(\d+)\s*/\s*(\d+)", text)
    if fraction_match:
        numerator = int(fraction_match.group(1))
        denominator = int(fraction_match.group(2))
        return float(Fraction(numerator, denominator)) if denominator else 0.0

    number_match = re.search(r"(\d+(?:[.,]\d+)?)", text)
    if number_match:
        return float(number_match.group(1).replace(",", "."))

    return 0.0


def amount_to_text(value) -> str:
    if value is None:
        return ""
    try:
        f = float(value)
    except Exception:
        return str(value)

    common = {
        0.25: "1/4",
        0.3333: "1/3",
        0.5: "1/2",
        0.6667: "2/3",
        0.75: "3/4",
    }

    rounded = round(f, 4)
    for k, v in common.items():
        if abs(rounded - k) < 0.01:
            return v

    if f.is_integer():
        return str(int(f))

    return str(round(f, 2)).rstrip("0").rstrip(".")


def extract_volume_ml(medicine_name: str) -> Optional[float]:
    text = strip_accents(medicine_name)
    matches = re.findall(r"(\d+(?:[.,]\d+)?)\s*ml", text)
    if not matches:
        return None

    values = [float(x.replace(",", ".")) for x in matches]
    return max(values)
