import json
import os
import sys

sys.path.append(os.path.abspath(r"d:\code\VinAi Action\day6\Day06-C401-NhomC3\codebase"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.services.calendar_service import CalendarService
from app.services.normalizer_service import PrescriptionNormalizer


with open(
    r"d:\code\VinAi Action\day6\Day06-C401-NhomC3\codebase\samples\case_trantrung.json",
    "r",
    encoding="utf-8",
) as f:
    payload = json.load(f)

normalizer = PrescriptionNormalizer()
prescription = normalizer.normalize(
    payload["raw_json"],
    start_date=payload.get("start_date"),
)

print("--- NORMALIZED MEDICINES ---")
for med in prescription.medicines:
    print(
        f"{med.medicine_name}: schedule={med.schedule}, "
        f"duration_days={med.duration_days}"
    )

calendar_service = CalendarService()
ics = calendar_service.build_ics(prescription)

print(f"\n--- VEVENT COUNT: {ics.count('BEGIN:VEVENT')} ---")
print("\n--- ICS FILE ---")
print(ics)
