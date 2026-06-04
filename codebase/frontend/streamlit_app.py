import json
import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
import socket
import qrcode
from io import BytesIO
from datetime import date, datetime, timedelta, time
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# CÔNG CỤ MẠNG (TÌM IP LAN CHO QR CODE)
# ==========================================


def get_lan_ip():
    """Tự động lấy địa chỉ IP của mạng Wi-Fi hiện tại để điện thoại có thể truy cập"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ==========================================
# CẤU HÌNH GIAO DIỆN & SETTINGS
# ==========================================
st.set_page_config(page_title="Long Châu AI - Smart Vision",
                   page_icon="💊", layout="wide")

st.markdown("""
    <style>
        .patient-card { background: linear-gradient(135deg, #004b93 0%, #0072ce 100%); color: white; padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; box-shadow: 0 4px 10px rgba(0,75,147,0.15);}
        .patient-title { font-size: 1.6rem; font-weight: 900; margin-bottom: 0.5rem; }
        div[data-testid="stMetricValue"] { font-size: 2rem !important; color: #004b93 !important; font-weight: 800 !important; }
        .streamlit-expanderHeader { font-size: 1.1rem; font-weight: bold; color: #004b93; }
        .stButton > button[kind="primary"] { border-radius: 8px; font-weight: 700; transition: all 0.3s; }
        
        /* Định dạng các nút lịch sử trong Sidebar trông giống Chat History */
        .history-btn { width: 100%; text-align: left !important; background-color: transparent; border: 1px solid #ddd; padding: 10px; border-radius: 8px; margin-bottom: 8px; transition: 0.2s; }
        .history-btn:hover { border-color: #004b93; background-color: #f1f8ff; }
    </style>
""", unsafe_allow_html=True)

DEFAULT_API_BASE = os.getenv("BACKEND_API_BASE", "http://127.0.0.1:8000")
PROJECT_ROOT = Path(__file__).resolve().parents[1]

SLOT_ORDER = [
    "morning_before_meal", "morning", "morning_after_meal",
    "noon_before_meal", "noon", "noon_after_meal",
    "afternoon_before_meal", "afternoon", "afternoon_after_meal",
    "evening_before_meal", "evening", "evening_after_meal",
]

SLOT_LABELS = {
    "morning": "Sáng", "noon": "Trưa", "afternoon": "Chiều", "evening": "Tối",
    "morning_before_meal": "Sáng trước ăn", "morning_after_meal": "Sáng sau ăn",
    "noon_before_meal": "Trưa trước ăn", "noon_after_meal": "Trưa sau ăn",
    "afternoon_before_meal": "Chiều trước ăn", "afternoon_after_meal": "Chiều sau ăn",
    "evening_before_meal": "Tối trước ăn", "evening_after_meal": "Tối sau ăn",
}

MODE_LABELS = {
    "fixed_schedule": "Lịch cố định",
    "divided_dose": "Chia liều",
    "as_needed": "Khi cần",
    "unknown": "Cần kiểm tra",
}


class ApiError(RuntimeError):
    pass


def init_state():
    st.session_state.setdefault("api_base", DEFAULT_API_BASE)
    st.session_state.setdefault("prescription_id", "")
    st.session_state.setdefault("create_result", None)
    st.session_state.setdefault("schedule_result", None)
    st.session_state.setdefault("history", [])


def api_url(path: str, params: dict[str, Any] | None = None) -> str:
    base = st.session_state.api_base.rstrip("/")
    url = f"{base}{path}"
    if params:
        clean_params = {key: value for key,
                        value in params.items() if value is not None}
        query = urllib.parse.urlencode(clean_params)
        if query:
            url = f"{url}?{query}"
    return url


def request_json(method: str, path: str, payload: dict[str, Any] | None = None, params: dict[str, Any] | None = None):
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        api_url(path, params=params), data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read()
            if "application/json" in response.headers.get("content-type", ""):
                return json.loads(body.decode("utf-8"))
            return body.decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise ApiError(format_http_error(exc)) from exc
    except urllib.error.URLError as exc:
        raise ApiError(f"Không kết nối được Backend: {exc.reason}") from exc


def upload_file(path: str, file_name: str, content: bytes, params: dict[str, Any]):
    boundary = f"----streamlit-{uuid.uuid4().hex}"
    content_type = mimetypes.guess_type(
        file_name)[0] or "application/octet-stream"
    disposition = f'Content-Disposition: form-data; name="file"; filename="{file_name}"'
    body = b"".join([
        f"--{boundary}\r\n".encode("utf-8"), f"{disposition}\r\n".encode("utf-8"),
        f"Content-Type: {content_type}\r\n\r\n".encode(
            "utf-8"), content, f"\r\n--{boundary}--\r\n".encode("utf-8"),
    ])
    request = urllib.request.Request(
        api_url(path, params=params), data=body,
        headers={"Accept": "application/json",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ApiError(format_http_error(exc)) from exc
    except urllib.error.URLError as exc:
        raise ApiError(f"Không kết nối được Backend: {exc.reason}") from exc


def format_http_error(exc: urllib.error.HTTPError) -> str:
    body = exc.read().decode("utf-8", errors="replace")
    try:
        parsed = json.loads(body)
        if detail := parsed.get("detail"):
            return f"{exc.code} {exc.reason}: {detail}"
    except json.JSONDecodeError:
        pass
    return f"{exc.code} {exc.reason}: {body}"


def remember_result(result: dict[str, Any]):
    """Lưu kết quả và cập nhật vào lịch sử Sidebar"""
    payload = result.get("ui_payload", result)
    prescription_id = payload.get("prescription_id")

    if prescription_id:
        st.session_state.prescription_id = prescription_id
        if not any(item["id"] == prescription_id for item in st.session_state.history):
            title = payload.get("title") or payload.get(
                "diagnose") or f"Đơn thuốc {date.today().strftime('%d/%m/%Y')}"
            st.session_state.history.append({
                "id": prescription_id,
                "title": title,
                "time": datetime.now().strftime("%H:%M - %d/%m/%Y")
            })

    st.session_state.create_result = result
    st.session_state.schedule_result = None


def load_history_item(prescription_id: str):
    """Gọi API để tải lại dữ liệu của 1 đơn thuốc cũ từ Lịch sử"""
    st.session_state.prescription_id = prescription_id
    try:
        st.session_state.create_result = request_json(
            "GET", f"/api/prescriptions/{prescription_id}/edit")
        st.session_state.schedule_result = request_json(
            "GET", f"/api/prescriptions/{prescription_id}/schedule")
    except Exception as exc:
        st.sidebar.error(f"Lỗi tải đơn cũ: {exc}")


def create_payload() -> dict[str, Any] | None:
    result = st.session_state.create_result
    return result.get("ui_payload", result) if result else None


def display(value: Any, fallback: str = "-") -> str:
    return fallback if value is None or value == "" else str(value)


def mode_label(mode: str | None) -> str:
    return MODE_LABELS.get(mode or "unknown", display(mode))


def slot_label(slot: str) -> str:
    return SLOT_LABELS.get(slot, slot.replace("_", " ").title())


def parse_time(value: str | None) -> time:
    if not value:
        return time(hour=8, minute=0)
    hour, minute = value.split(":")[:2]
    return time(hour=int(hour), minute=int(minute))

# ==========================================
# RENDER VIEWS
# ==========================================


def render_prescription_summary(payload: dict[str, Any]):
    st.markdown(f"""
        <div class="patient-card">
            <div class="patient-title">👤 BỆNH NHÂN: {display(payload.get('patient_name'), 'Ẩn danh').upper()}</div>
            <div style="font-size: 1.2rem; opacity: 0.95;"><b>🩺 Chẩn đoán:</b> {display(payload.get('diagnose') or payload.get('title'))}</div>
            <div style="font-size: 1.1rem; opacity: 0.85; margin-top:5px;">🏥 {display(payload.get('hospital_name'))}</div>
        </div>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    cols[0].metric("Ngày bắt đầu", display(payload.get("start_date")))
    cols[1].metric("Số ngày dùng", display(payload.get("prescription_days")))
    cols[2].metric("Ngày kết thúc", display(payload.get("end_date")))
    cols[3].metric("Số loại thuốc", len(payload.get("medicines", [])))


def render_medicine_details(payload: dict[str, Any]):
    for med in payload.get("medicines", []):
        title = f"#{display(med.get('no'))} - {display(med.get('medicine_name'), 'Thuốc')}"
        with st.expander(title, expanded=bool(med.get("needs_review"))):
            cols = st.columns(4)
            cols[0].metric("Kiểu lịch", mode_label(med.get("schedule_mode")))
            cols[1].metric("Tổng số", display(med.get("raw_total")))
            cols[2].metric("Mỗi ngày", display(med.get("daily_total")))
            cols[3].metric("Số ngày", display(med.get("duration_days")))

            st.write(
                f"**Hướng dẫn bác sĩ:** {display(med.get('raw_summary'))}")
            if med.get("display_note"):
                st.info(med["display_note"])
            if med.get("condition"):
                st.warning(f"Dùng khi cần: {med['condition']}")

            if schedule := med.get("schedule"):
                st.table([{slot_label(slot): dose for slot,
                         dose in schedule.items() if dose}])
            for warning in med.get("warnings") or []:
                st.warning(warning)


def render_create_view(payload: dict[str, Any] | None):
    if not payload:
        st.info("Chưa có đơn thuốc. Hãy tải ảnh ở tab Nhập Đơn.")
        return
    render_prescription_summary(payload)
    st.markdown("### Chi tiết thuốc")
    render_medicine_details(payload)


def render_schedule_view(payload: dict[str, Any] | None):
    if not payload:
        return st.info("Vui lòng ấn 'Tải lịch nhắc' để hệ thống tính toán.")
    st.subheader(display(payload.get("title"), "Lịch nhắc"))
    st.caption(display(payload.get("date_range_text"), ""))
    for warning in payload.get("warnings") or []:
        st.warning(warning)

    active_slots = payload.get("active_slots") or []
    if not active_slots:
        return st.info("Không có khung giờ cố định để tạo nhắc.")

    st.markdown("### Bảng nhắc trong ngày")
    table_rows = [{"Giờ": slot.get("time"), "Khung": slot_label(slot.get("slot", "")),
                   "Thuốc": med.get("medicine_name"), "Liều": med.get("dose"),
                   "Ghi chú": display(med.get("note"), "")}
                  for slot in active_slots for med in slot.get("medicines") or []]
    st.dataframe(table_rows, use_container_width=True, hide_index=True)


def schedule_editor(payload: dict[str, Any]) -> dict[str, str]:
    defaults = payload.get("reminder_times") or {}
    active_slots = payload.get("active_slots") or []
    slot_keys = [slot["slot"] for slot in active_slots if slot.get(
        "slot")] or ["morning", "noon", "afternoon", "evening"]

    st.markdown("### Chỉnh sửa giờ nhắc")
    times, cols = {}, st.columns(4)
    for i, slot_key in enumerate(slot_keys):
        default = defaults.get(slot_key, "08:00")
        chosen = cols[i % 4].time_input(slot_label(
            slot_key), value=parse_time(default), key=f"time_{slot_key}")
        times[slot_key] = chosen.strftime("%H:%M")
    return times

# ==========================================
# MACRO GOOGLE CALENDAR (CHỐNG POP-UP)
# ==========================================


def get_macro_html_button(schedule_payload):
    gcal_links = []
    med_names = []
    create_res = st.session_state.get("create_result") or {}
    ui_payload = create_res.get("ui_payload", create_res)
    patient_name = ui_payload.get("patient_name", "Bệnh nhân")

    active_slots = schedule_payload.get("active_slots", [])
    now = datetime.now()
    for slot in active_slots:
        time_str = slot.get("time", "08:00")
        hour, minute = map(int, time_str.split(":")[:2])
        dt_start = now.replace(hour=hour, minute=minute, second=0)
        dt_end = dt_start + timedelta(minutes=15)

        for med in slot.get("medicines", []):
            title = f"💊 {patient_name.title()} uống {med.get('medicine_name')}"
            details = f"Liều lượng: {med.get('dose')}\nLưu ý: {med.get('note', '')}"
            repeat_days = med.get('duration_days') or 7

            params = {
                "action": "TEMPLATE", "text": title,
                "dates": f"{dt_start.strftime('%Y%m%dT%H%M%S')}/{dt_end.strftime('%Y%m%dT%H%M%S')}",
                "details": details, "recur": f"RRULE:FREQ=DAILY;COUNT={repeat_days}"
            }
            gcal_links.append(
                "https://calendar.google.com/calendar/render?" + urllib.parse.urlencode(params))
            med_names.append(f"{time_str} - {med.get('medicine_name')}")

    js_links_array = json.dumps(gcal_links)

    fallback_html = "".join(
        [f'<a href="{url}" target="_blank" style="display:block; margin: 8px 0; color: #004b93; font-weight: 500; text-decoration: none;">🔗 Bấm để thêm: {name}</a>' for url, name in zip(gcal_links, med_names)])

    return f"""
    <button id="multi-sync-btn" style="
        width: 100%; background: linear-gradient(135deg, #fbbc05 0%, #ea4335 100%); 
        color: white; border: none; padding: 14px; border-radius: 8px; 
        font-weight: bold; font-size: 16px; cursor: pointer; box-shadow: 0 4px 10px rgba(234,67,53,0.25); margin-top: 15px; transition: 0.3s;
    ">🗓️ TỰ ĐỘNG THÊM TOÀN BỘ LỊCH BÁO THỨC VÀO GOOGLE CALENDAR</button>
    
    <div id="fallback-links" style="display:none; margin-top: 15px; padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
        <p style="color: #856404; font-weight: bold; margin-bottom: 5px;">⚠️ Nếu trình duyệt chặn mở nhiều Tab, hãy click thủ công vào các link dưới đây:</p>
        {fallback_html}
    </div>
    
    <script>
        document.getElementById('multi-sync-btn').addEventListener('click', function() {{
            const urls = {js_links_array};
            document.getElementById('fallback-links').style.display = 'block';
            urls.forEach((url, index) => {{ setTimeout(() => {{ window.open(url, '_blank'); }}, index * 800); }});
        }});
    </script>
    """


def show_api_error(exc: Exception):
    st.error(str(exc))


init_state()

# ==========================================
# CỘT TRÁI (SIDEBAR) - LỊCH SỬ ĐƠN KHÁM
# ==========================================
with st.sidebar:
    st.markdown("### 🕒 Lịch sử đơn khám")
    if not st.session_state.history:
        st.info("Chưa có đơn khám nào. Hãy quét đơn đầu tiên của bạn!")
    else:
        for item in reversed(st.session_state.history):
            if st.button(f"📄 {item['title']}\n\n⏰ {item['time']}", key=f"hist_{item['id']}", use_container_width=True):
                load_history_item(item["id"])

    st.divider()
    with st.expander("⚙️ Cấu hình hệ thống"):
        st.text_input("Backend URL", key="api_base")
        if st.button("Kiểm tra kết nối", use_container_width=True):
            try:
                st.json(request_json("GET", "/"))
            except Exception as exc:
                show_api_error(exc)

# ==========================================
# KHU VỰC TRUNG TÂM - TABS CHÍNH
# ==========================================
st.markdown("<h1 style='color: #004b93; font-weight: 900; margin-bottom:0;'>⚕️ HỆ THỐNG TRỢ LÝ AI LONG CHÂU</h1>", unsafe_allow_html=True)
st.markdown("---")

input_tab, create_tab, schedule_tab = st.tabs(
    ["📁 Nhập đơn mới", "📄 Phân tích chi tiết", "🔔 Hẹn giờ nhắc"])

# TAB 1: NHẬP ĐƠN
with input_tab:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("📸 Quét đơn thuốc mới")
        st.caption(
            "Trí tuệ nhân tạo sẽ tự động bóc tách và phân tích thông tin từ ảnh.")

        tab_upload, tab_cam = st.tabs(["📁 Tải ảnh lên", "📸 Quét bằng Camera"])
        camera_image = tab_cam.camera_input(
            "Chụp ảnh", label_visibility="collapsed")
        uploaded_file = tab_upload.file_uploader(
            "Tải ảnh lên", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

        start_date = st.date_input(
            "Ngày bắt đầu dùng thuốc", value=date.today(), key="ocr_date")
        image = uploaded_file or camera_image

        if image:
            st.image(image, caption="Đang xử lý: " +
                     image.name, use_container_width=True)

        if st.button("🚀 BẮT ĐẦU PHÂN TÍCH OCR", type="primary", disabled=image is None, use_container_width=True):
            try:
                with st.spinner("🧠 AI đang bóc tách và phân tích dữ liệu..."):
                    result = upload_file("/api/prescriptions/ocr", image.name,
                                         image.getvalue(), params={"start_date": start_date.isoformat()})
                remember_result(result)
                st.success(
                    "🎉 Phân tích thành công! Dữ liệu đã được lưu vào Lịch sử. Hãy chuyển sang tab 'Phân tích chi tiết'.")
            except Exception as exc:
                show_api_error(exc)

# TAB 2: CHI TIẾT ĐƠN THUỐC
with create_tab:
    payload = create_payload()
    render_create_view(payload)

# TAB 3: TẠO LỊCH BÁO THỨC VÀ QR CODE
with schedule_tab:
    if not st.session_state.prescription_id:
        st.info(
            "Vui lòng tải ảnh ở tab 'Nhập đơn mới' hoặc chọn một đơn thuốc từ Lịch sử bên trái.")
    else:
        cols = st.columns([1, 1, 4])
        if cols[0].button("Tải lịch nhắc", type="primary"):
            try:
                st.session_state.schedule_result = request_json(
                    "GET", f"/api/prescriptions/{st.session_state.prescription_id}/schedule")
            except Exception as exc:
                show_api_error(exc)

        schedule_payload = st.session_state.schedule_result
        render_schedule_view(schedule_payload)

        if schedule_payload:
            times = schedule_editor(schedule_payload)
            add_calendar = st.checkbox(
                "Yêu cầu tải file lịch tĩnh (.ics)", value=False)

            if st.button("💾 Lưu giờ nhắc & Tạo QR Code", type="primary"):
                try:
                    result = request_json("POST", f"/api/prescriptions/{st.session_state.prescription_id}/schedule", payload={
                                          "times": times, "add_to_device_calendar": add_calendar})
                    st.success(result.get("message", "Đã lưu thành công"))

                    if result.get("calendar_url"):
                        col_btn, col_qr = st.columns([1, 1])

                        # --- CỘT 1: NÚT TẢI CHO MÁY TÍNH ---
                        with col_btn:
                            st.markdown("### 💻 Tải về máy tính")
                            st.link_button("📥 Tải file lịch (.ics)", api_url(
                                result.get("calendar_url")), use_container_width=True)

                        # --- CỘT 2: QR CODE CHO ĐIỆN THOẠI (Xử lý URL Chuẩn xác) ---
                        with col_qr:
                            st.markdown("### 📱 Quét để tải vào điện thoại")
                            raw_api_base = st.session_state.api_base
                            lan_ip = get_lan_ip()

                            # Bóc tách URL giữ nguyên Port và Scheme
                            parsed_base = urllib.parse.urlparse(raw_api_base)
                            port = parsed_base.port or 8000
                            scheme = parsed_base.scheme or "http"

                            if "127.0.0.1" in raw_api_base or "localhost" in raw_api_base:
                                backend_url_for_phone = f"{scheme}://{lan_ip}:{port}"
                            else:
                                backend_url_for_phone = raw_api_base.rstrip(
                                    '/')

                            # Đảm bảo đường dẫn calendar luôn có dấu /
                            calendar_path = result.get("calendar_url", "")
                            if not calendar_path.startswith('/'):
                                calendar_path = '/' + calendar_path

                            qr_url = f"{backend_url_for_phone}{calendar_path}"

                            # Tạo ảnh QR Code
                            qr = qrcode.QRCode(version=1, box_size=8, border=2)
                            qr.add_data(qr_url)
                            qr.make(fit=True)
                            img_qr = qr.make_image(
                                fill_color="#004b93", back_color="white")

                            buf = BytesIO()
                            img_qr.save(buf, format="PNG")
                            st.image(buf.getvalue(), width=220)
                            st.caption(
                                f"Lưu ý: Camera quét xong hãy mở bằng trình duyệt Safari/Chrome.\n(Link: `{qr_url}`)")

                except Exception as exc:
                    show_api_error(exc)

            st.divider()
            components.html(get_macro_html_button(
                schedule_payload), height=220)
