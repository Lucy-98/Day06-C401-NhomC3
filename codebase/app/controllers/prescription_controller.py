import uuid
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from fastapi.responses import JSONResponse, Response
from app.repositories.json_repository import JsonRepository
from app.services.ocr_service import (
    OcrConfigurationError,
    OcrProviderError,
    OcrService,
)
from app.services.normalizer_service import PrescriptionNormalizer
from app.services.view_builder_service import ViewBuilderService
from app.services.calendar_service import CalendarService
from app.schemas.prescription_schema import NormalizeDemoRequest, ReminderTimeUpdateRequest

router = APIRouter()

repo = JsonRepository()
ocr_service = OcrService()
normalizer = PrescriptionNormalizer()
view_builder = ViewBuilderService()
calendar_service = CalendarService()


def _build_ocr_error_response(
    *,
    status_code: int,
    error_code: str,
    message: str,
    retryable: bool,
    prescription_id: str | None = None,
):
    ui_payload = {
        "screen": "ocr_error",
        "title": "Khong the xu ly anh don thuoc",
        "message": message,
        "retryable": retryable,
        "error_code": error_code,
        "suggestions": [
            "Thu lai voi anh ro hon, du anh sang va khong bi mo.",
            "Dat don thuoc thang khung hinh, tranh mat goc va bong den.",
            "Neu van loi, chuyen sang Demo bang JSON de tiep tuc test UI.",
        ],
    }
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "prescription_id": prescription_id,
            "error": {
                "code": error_code,
                "message": message,
                "retryable": retryable,
            },
            "ui_payload": ui_payload,
        },
    )


@router.post("/ocr")
async def ocr_prescription(
    file: UploadFile = File(...),
    start_date: str | None = Query(default=None),
):
    """
    UI màn 2 -> màn 3:
    Upload ảnh đơn thuốc, gọi Gemini OCR, normalize, trả payload màn Tạo đơn.
    """
    prescription_id = str(uuid.uuid4())

    image_path = repo.save_upload(
        prescription_id=prescription_id,
        filename=file.filename or "upload.png",
        content=await file.read(),
    )

    try:
        raw_json = ocr_service.extract_prescription(image_path)
    except OcrConfigurationError as exc:
        return _build_ocr_error_response(
            status_code=503,
            error_code="OCR_CONFIGURATION_ERROR",
            message=str(exc),
            retryable=False,
            prescription_id=prescription_id,
        )
    except OcrProviderError as exc:
        return _build_ocr_error_response(
            status_code=502,
            error_code="OCR_PROVIDER_ERROR",
            message=str(exc),
            retryable=True,
            prescription_id=prescription_id,
        )

    prescription = normalizer.normalize(
        raw_json=raw_json,
        start_date=start_date,
        prescription_id=prescription_id,
    )

    if not prescription.medicines:
        return _build_ocr_error_response(
            status_code=422,
            error_code="OCR_EMPTY_RESULT",
            message="Khong doc duoc thong tin thuoc tu anh nay. Vui long thu anh ro hon hoac doi anh khac.",
            retryable=True,
            prescription_id=prescription_id,
        )

    repo.save_raw(prescription_id, raw_json)
    repo.save_normalized(prescription_id, prescription.model_dump())

    return {
        "prescription_id": prescription_id,
        "ui_payload": view_builder.build_create_prescription_view(prescription),
        "next": {
            "edit_url": f"/api/prescriptions/{prescription_id}/edit",
            "schedule_url": f"/api/prescriptions/{prescription_id}/schedule",
        }
    }


@router.post("/normalize-demo")
def normalize_demo(payload: NormalizeDemoRequest):
    """
    Dùng khi đã có raw JSON OCR giả lập.
    Không gọi Gemini.
    """
    prescription_id = str(uuid.uuid4())

    prescription = normalizer.normalize(
        raw_json=payload.raw_json,
        start_date=payload.start_date,
        prescription_id=prescription_id,
    )

    repo.save_raw(prescription_id, payload.raw_json)
    repo.save_normalized(prescription_id, prescription.model_dump())

    return {
        "prescription_id": prescription_id,
        "ui_payload": view_builder.build_create_prescription_view(prescription),
        "next": {
            "edit_url": f"/api/prescriptions/{prescription_id}/edit",
            "schedule_url": f"/api/prescriptions/{prescription_id}/schedule",
        }
    }


@router.get("/{prescription_id}/edit")
def get_create_prescription_view(prescription_id: str):
    """
    UI màn 3: Tạo đơn.
    """
    data = repo.get_normalized(prescription_id)
    if not data:
        raise HTTPException(status_code=404, detail="Prescription not found")

    from app.models.domain import Prescription
    prescription = Prescription(**data)

    return view_builder.build_create_prescription_view(prescription)


@router.get("/{prescription_id}/schedule")
def get_schedule_view(prescription_id: str):
    """
    UI màn 4: Hẹn giờ nhắc.
    """
    data = repo.get_normalized(prescription_id)
    if not data:
        raise HTTPException(status_code=404, detail="Prescription not found")

    from app.models.domain import Prescription
    prescription = Prescription(**data)

    return view_builder.build_schedule_view(prescription)


@router.post("/{prescription_id}/schedule")
def save_schedule_times(prescription_id: str, payload: ReminderTimeUpdateRequest):
    """
    Lưu giờ nhắc user chọn ở màn 4.
    Mockup hiện tại trả lại calendar_url.
    Mobile app sẽ dùng URL này hoặc tự add vào EventKit/Calendar Provider.
    """
    data = repo.get_normalized(prescription_id)
    if not data:
        raise HTTPException(status_code=404, detail="Prescription not found")

    data["custom_reminder_times"] = payload.times
    data["device_calendar_requested"] = payload.add_to_device_calendar
    repo.save_normalized(prescription_id, data)

    return {
        "message": "Saved reminder times",
        "calendar_url": f"/api/prescriptions/{prescription_id}/calendar.ics",
        "add_to_device_calendar": payload.add_to_device_calendar,
    }


@router.get("/{prescription_id}/calendar.ics")
def get_calendar_ics(prescription_id: str):
    """
    Xuất lịch .ics.
    Không tạo lịch trực tiếp trên máy; mobile app mới xin quyền và add vào lịch mặc định.
    """
    data = repo.get_normalized(prescription_id)
    if not data:
        raise HTTPException(status_code=404, detail="Prescription not found")

    from app.models.domain import Prescription
    prescription = Prescription(**data)

    ics = calendar_service.build_ics(
        prescription,
        custom_times=data.get("custom_reminder_times"),
    )

    repo.save_calendar(prescription_id, ics)

    return Response(
        content=ics,
        media_type="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="{prescription_id}.ics"'},
    )
