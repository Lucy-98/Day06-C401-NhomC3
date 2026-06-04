import json
from pathlib import Path
from typing import Any


class JsonRepository:
    def __init__(self, base_dir: str = "data"):
        self.base_dir = Path(base_dir)
        self.upload_dir = self.base_dir / "uploads"
        self.raw_dir = self.base_dir / "raw"
        self.normalized_dir = self.base_dir / "normalized"
        self.calendar_dir = self.base_dir / "calendar"

        for d in [self.upload_dir, self.raw_dir, self.normalized_dir, self.calendar_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def save_upload(self, prescription_id: str, filename: str, content: bytes) -> Path:
        suffix = Path(filename or "upload.png").suffix or ".png"
        path = self.upload_dir / f"{prescription_id}{suffix}"
        path.write_bytes(content)
        return path

    def save_raw(self, prescription_id: str, raw_json: dict[str, Any]) -> Path:
        path = self.raw_dir / f"{prescription_id}.json"
        path.write_text(json.dumps(raw_json, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def save_normalized(self, prescription_id: str, normalized_json: dict[str, Any]) -> Path:
        path = self.normalized_dir / f"{prescription_id}.json"
        path.write_text(json.dumps(normalized_json, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def get_normalized(self, prescription_id: str) -> dict[str, Any] | None:
        path = self.normalized_dir / f"{prescription_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save_calendar(self, prescription_id: str, ics: str) -> Path:
        path = self.calendar_dir / f"{prescription_id}.ics"
        path.write_text(ics, encoding="utf-8")
        return path