from datetime import date, datetime, timedelta


def today_iso() -> str:
    return date.today().isoformat()


def add_days(start_date: str, days: int) -> str:
    return (datetime.fromisoformat(start_date).date() + timedelta(days=days - 1)).isoformat()


def format_vn_date_range(start_date: str, end_date: str | None) -> str:
    if not end_date:
        return start_date
    s = datetime.fromisoformat(start_date).strftime("%d/%m/%Y")
    e = datetime.fromisoformat(end_date).strftime("%d/%m/%Y")
    return f"{s} - {e}"


def build_week_strip(selected_date: str):
    current = datetime.fromisoformat(selected_date).date()
    monday = current - timedelta(days=current.weekday())

    labels = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    result = []

    for i, label in enumerate(labels):
        d = monday + timedelta(days=i)
        result.append({
            "label": label,
            "day": d.day,
            "date": d.isoformat(),
            "selected": d == current
        })

    return result
