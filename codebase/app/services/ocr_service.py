import os
import json
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


class OcrConfigurationError(RuntimeError):
    pass


class OcrProviderError(RuntimeError):
    pass


OCR_PROMPT = """
Bạn là hệ thống OCR đơn thuốc tiếng Việt.

Yêu cầu:
- Chỉ trả về JSON, không markdown.
- Không tự suy diễn chỉ định y khoa.
- Nếu không chắc chắn, giữ text đọc được và thêm *_prob nếu cần.
- Bóc đủ: bệnh viện, tên bệnh nhân, giới tính, chẩn đoán, danh sách thuốc, số lượng, cách dùng.
- Phân biệt Sáng / Trưa / Chiều / Tối.
- Giữ lại các cụm quan trọng: trước ăn, sau ăn, khi sốt, khi đau, khi cần, cách 4-6h, chia 2 lần, đặt âm đạo, bôi, nhỏ mắt.

Schema:
{
  "data": {
    "hospital_name": "",
    "patient_name": "",
    "patient_dob": "",
    "patient_gender": "",
    "patient_address": "",
    "diagnose": "",
    "table_information": [
      {
        "no": 1,
        "medicine_name": "",
        "medicine_count": "",
        "medicine_guide": {
          "summary": "",
          "use": "",
          "note": "",
          "times": "",
          "type": "",
          "guide_morning": "",
          "guide_noon": "",
          "guide_afternoon": "",
          "guide_evening": "",
          "use_count": ""
        }
      }
    ]
  },
  "errorCode": null,
  "errorMessage": null
}
"""


class OcrService:
    def extract_prescription(self, image_path: Path) -> dict:
        from google import genai
        from google.genai import types

        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key or api_key == "your_gemini_key_here":
            raise OcrConfigurationError(
                "GEMINI_API_KEY is missing. Set it in .env or as an environment variable."
            )

        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        mime_type = "image/jpeg" if image_path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"

        try:
            response = client.models.generate_content(
                model=model,
                contents=[
                    OCR_PROMPT,
                    types.Part.from_bytes(data=image_path.read_bytes(), mime_type=mime_type),
                ],
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
        except Exception as exc:
            raise OcrProviderError(f"Gemini OCR request failed: {exc}") from exc

        try:
            return json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise OcrProviderError("Gemini returned invalid JSON.") from exc
