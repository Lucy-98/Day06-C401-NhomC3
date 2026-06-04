# Long Chau Medicine Reminder Mockup

Backend và Streamlit UI mockup cho tính năng nhắc dùng thuốc trong app Nhà thuốc Long Châu.

Luồng chính:

1. Người dùng chụp hoặc tải ảnh đơn thuốc.
2. Backend gọi Gemini OCR để bóc tách thông tin đơn.
3. Raw JSON được lưu vào `data/raw`.
4. Backend normalize dữ liệu thuốc thành payload UI.
5. UI tự fill màn Tạo đơn, tính số ngày dùng từng thuốc.
6. Người dùng kiểm tra, chỉnh giờ nhắc.
7. Backend xuất lịch `.ics` để app mobile có thể thêm vào lịch mặc định.

## Cấu trúc

```text
app/
├─ main.py                         # FastAPI app
├─ controllers/                    # API routes
├─ models/                         # Domain models: Prescription, Medicine
├─ repositories/                   # Lưu upload, raw JSON, normalized JSON, calendar
├─ schemas/                        # DTO/view payload cho UI
├─ services/                       # OCR, normalize, build view, calendar
└─ utils/                          # Parse số, phân số, ngày

frontend/
└─ streamlit_app.py                # Streamlit UI mockup

samples/
├─ case1.json                      # Demo đơn thuốc đơn giản
└─ case6.json                      # Demo thuốc nước, chia liều, thuốc khi cần

data/
├─ uploads/                        # Ảnh đơn thuốc upload
├─ raw/                            # Raw OCR JSON
├─ normalized/                     # JSON sau normalize
└─ calendar/                       # File .ics đã xuất
```

## Yêu cầu

- Python 3.12
- FastAPI backend dependencies trong `requirements.txt`
- Streamlit cho frontend
- Gemini API key nếu dùng OCR ảnh thật

## Cấu hình Gemini

Tạo file `.env` từ `.env.example`:

```powershell
Copy-Item .env.example .env
```

Mở `.env` và điền key:

```env
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.5-flash
APP_TZ=Asia/Ho_Chi_Minh
```

Nếu chưa có API key, vẫn có thể dùng tab `Demo bang JSON` trong frontend với các file trong `samples/`.

## Cài đặt môi trường

Nếu project đã có `.venv_api` và `.venv_ui`, có thể bỏ qua phần tạo venv và chạy thẳng ở mục tiếp theo.

### Backend

```powershell
python -m venv .venv_api
.\.venv_api\Scripts\python.exe -m pip install -r requirements.txt
```

### Frontend

```powershell
python -m venv .venv_ui
.\.venv_ui\Scripts\python.exe -m pip install streamlit
```

## Chạy project

Mở 2 terminal PowerShell tại thư mục project.

### Terminal 1: chạy backend

```powershell
.\.venv_api\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app --host 127.0.0.1 --port 8000
```

Kiểm tra backend:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8000/
```

Kết quả đúng:

```json
{"status":"ok","service":"Long Chau Medicine Reminder MVC Backend"}
```

### Terminal 2: chạy frontend

```powershell
.\.venv_ui\Scripts\python.exe -m streamlit run frontend/streamlit_app.py
```

Mở trình duyệt:

```text
http://localhost:8501
```

## Cách dùng frontend

### 1. Nhập đơn

Tab `Nhap don` có 2 cách:

- `OCR anh don thuoc`: chụp ảnh hoặc upload ảnh đơn thuốc. Cách này cần `GEMINI_API_KEY`.
- `Demo bang JSON`: chọn `case1.json`, `case6.json`, hoặc paste raw OCR JSON để test normalize mà không cần Gemini.

Sau khi bấm `Chay OCR` hoặc `Normalize JSON`, backend sẽ trả về payload UI và lưu dữ liệu vào `data/`.

### 2. Tạo đơn

Tab `Tao don` hiển thị:

- thông tin bệnh viện, bệnh nhân, chẩn đoán
- ngày bắt đầu, số ngày dùng, ngày kết thúc
- danh sách thuốc đã normalize
- liều sáng/trưa/chiều/tối
- kiểu lịch: `fixed_schedule`, `divided_dose`, `as_needed`, `unknown`
- các cảnh báo cần người dùng kiểm tra

Tab con `Phan tich lich` hiển thị bảng nhắc gợi ý và timeline trong ngày.

### 3. Hẹn giờ nhắc

Tab `Hen gio nhac` dùng `Prescription ID` ở sidebar.

Các bước:

1. Bấm `Tai lich nhac`.
2. Kiểm tra bảng nhắc và timeline.
3. Chỉnh giờ nhắc theo từng khung.
4. Bấm `Luu gio nhac`.
5. Mở link `.ics` nếu muốn tải file lịch.

### 4. Raw JSON

Tab `Raw JSON` dùng để kiểm tra dữ liệu gốc và response backend trong quá trình demo/debug.

## API chính

### Healthcheck

```http
GET /
```

### Home nhắc thuốc

```http
GET /api/reminders/home?date=2026-06-04
```

### OCR ảnh đơn thuốc

```http
POST /api/prescriptions/ocr?start_date=2026-06-04
Content-Type: multipart/form-data

file=@don_thuoc.jpg
```

### Normalize từ raw JSON

```http
POST /api/prescriptions/normalize-demo
Content-Type: application/json
```

Body:

```json
{
  "start_date": "2026-06-04",
  "raw_json": {
    "data": {
      "hospital_name": "",
      "patient_name": "",
      "patient_gender": "",
      "patient_address": "",
      "diagnose": "",
      "table_information": []
    }
  }
}
```

### Lấy payload màn Tạo đơn

```http
GET /api/prescriptions/{prescription_id}/edit
```

### Lấy payload màn Hẹn giờ nhắc

```http
GET /api/prescriptions/{prescription_id}/schedule
```

### Lưu giờ nhắc

```http
POST /api/prescriptions/{prescription_id}/schedule
Content-Type: application/json
```

Body:

```json
{
  "times": {
    "morning": "07:30",
    "noon": "12:00",
    "afternoon": "15:00",
    "evening": "21:00"
  },
  "add_to_device_calendar": false
}
```

### Xuất file lịch `.ics`

```http
GET /api/prescriptions/{prescription_id}/calendar.ics
```

## Logic normalize chính

Backend không fill raw OCR trực tiếp lên UI. Raw OCR luôn đi qua `PrescriptionNormalizer`.

Các rule chính:

- `"30 Viên"` thành `total_amount = 30`
- `"1/3 Chai"` thành `0.3333`, nhưng UI vẫn có thể hiển thị `"1/3"`
- `"Sáng 1 viên"` thành `schedule.morning = 1`
- `"Ngày uống 7ml chia 2 lần"` thành `divided_dose`, gợi ý sáng/tối
- `"Khi sốt >= 38.5 độ"` thành `as_needed`, không tạo lịch cố định
- thuốc trước ăn/sau ăn được tách slot giờ riêng
- mỗi thuốc có `duration_days` riêng
- `prescription_days` là số ngày lớn nhất của các thuốc có lịch cố định

Các `schedule_mode`:

```text
fixed_schedule  # Có liều theo sáng/trưa/chiều/tối
divided_dose    # Tổng liều/ngày chia N lần
as_needed       # Dùng khi cần, không tạo lịch cố định
unknown         # Không đủ dữ liệu, cần người dùng sửa
```

## Lỗi thường gặp

### Streamlit báo file không tồn tại

Chạy đúng từ thư mục project:

```powershell
.\.venv_ui\Scripts\python.exe -m streamlit run frontend/streamlit_app.py
```

### OCR trả lỗi thiếu API key

Kiểm tra `.env` có dòng:

```env
GEMINI_API_KEY=...
```

Sau khi sửa `.env`, restart backend.

### Backend reload liên tục

Luôn chạy backend với `--reload-dir app`:

```powershell
.\.venv_api\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app
```

Lệnh này tránh để `uvicorn` watch cả `.venv_ui` hoặc các thư mục môi trường ảo.
