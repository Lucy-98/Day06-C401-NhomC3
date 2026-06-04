from fastapi import APIRouter, Query
from app.services.view_builder_service import ViewBuilderService
from app.utils.date_utils import today_iso

router = APIRouter()
view_builder = ViewBuilderService()


@router.get("/home")
def get_home(date: str | None = Query(default=None)):
    """
    UI màn 1: Home nhắc uống thuốc.
    Hiện lịch trong ngày hoặc empty state.
    """
    selected_date = date or today_iso()

    # Mock DB chưa có reminder theo ngày, nên trả empty state.
    # Khi nối DB thật: query reminders theo selected_date.
    return view_builder.build_home_view(selected_date=selected_date, reminders=[])
