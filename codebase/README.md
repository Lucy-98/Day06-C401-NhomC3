# Long Chau Medicine Reminder Mockup

Backend và Streamlit UI mockup cho tính năng nhắc dùng thuốc trong app Nhà thuốc Long Châu.

Luồng chính:

1. Người dùng chụp hoặc tải ảnh đơn thuốc.
2. Backend gọi Gemini OCR để bóc tách thông tin đơn.
3. Raw JSON được lưu vào `data/raw`.
4. Backend normalize dữ liệu thuốc thành payload UI.
5. UI tự fill màn Tạo đơn, tính số ngày dùng từng thuốc.
6. Người dùng kiểm tra lại thông tin, chỉnh sửa (Human-in-the-loop) và hẹn giờ nhắc.
7. Backend xuất lịch `.ics` cùng QR code để app mobile quét, hoặc đồng bộ thẳng vào Google Calendar.

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
- **Gemini API key** bắt buộc để dùng tính năng OCR ảnh đơn thuốc.

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

## Cài đặt môi trường

Chạy các lệnh sau trong thư mục `codebase/`:

### Backend

```powershell
python -m venv .venv_api
.\.venv_api\Scripts\python.exe -m pip install -r requirements.txt
```

### Frontend

```powershell
python -m venv .venv_ui
.\.venv_ui\Scripts\python.exe -m pip install streamlit qrcode pillow
```

## Chạy project

Mở 2 terminal PowerShell tại thư mục `codebase/`.

### Terminal 1: chạy backend

```powershell
.\.venv_api\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app --host 127.0.0.1 --port 8000
```

Kiểm tra backend:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/
```

Kết quả đúng:

```json
{"status":"ok","service":"Long Chau Medicine Reminder MVC Backend"}
```

### Terminal 2: chạy frontend

```powershell
.\.venv_ui\Scripts\python.exe -m streamlit run frontend/streamlit_app.py
```

Mở trình duyệt tại: `http://localhost:8501`

## Cách dùng frontend

Giao diện được chia thành 3 tab chính:

### 1. Nhập đơn mới

- Tải ảnh lên hoặc Quét bằng Camera trực tiếp từ thiết bị.
- Chọn "Ngày bắt đầu dùng thuốc".
- Bấm `BẮT ĐẦU PHÂN TÍCH OCR`.
- Hệ thống sẽ hiển thị loading. Nếu có lỗi (ví dụ: ảnh mờ, không đúng đơn thuốc), sẽ hiện giao diện báo cáo lỗi chi tiết để người dùng nắm rõ nguyên nhân và chụp lại.

### 2. Phân tích chi tiết

Hiển thị thông tin đã được AI bóc tách và chuẩn hóa:
- Thông tin bệnh viện, chẩn đoán, bệnh nhân.
- Thống kê ngày uống, tổng số loại thuốc.
- Chi tiết từng loại thuốc: kiểu lịch, tổng số lượng, số liều mỗi ngày, hướng dẫn chi tiết từ bác sĩ.
- Các cảnh báo đặc biệt (ví dụ: dùng khi cần, chia nhỏ liều).

### 3. Hẹn giờ nhắc

- Bảng nhắc trong ngày hiển thị Timeline chi tiết các cữ uống (Sáng/Trưa/Chiều/Tối).
- Cho phép chỉnh sửa khung giờ nhắc cụ thể (ví dụ: đổi Sáng từ 08:00 thành 07:30).
- Khi hoàn tất, bấm `Lưu giờ nhắc & Tạo QR Code`. Hệ thống sẽ cung cấp:
  - Nút **Tải file lịch (.ics)** để tải xuống máy tính.
  - Mã **QR Code** để quét bằng camera điện thoại, lấy file `.ics` đưa trực tiếp vào Apple Calendar / Google Calendar di động.
  - Chức năng **Đồng bộ Google Calendar** (Macro Links): tự động sinh các sự kiện tương ứng với từng cữ uống thẳng vào tài khoản Google, giúp đồng bộ dễ dàng chỉ với 1 click chuột.

## Lịch sử đơn khám

Thanh Sidebar bên trái tự động lưu lại tất cả các đơn thuốc đã quét thành công. Người dùng có thể click lại vào tên bệnh/đơn thuốc để load lại thông tin, chỉnh sửa lịch uống hoặc lấy lại QR Code bất cứ lúc nào.

## Logic normalize chính

Backend không truyền raw OCR trực tiếp lên UI. Raw OCR luôn đi qua `PrescriptionNormalizer`.

Các rule chính:

- `"30 Viên"` thành `total_amount = 30`
- `"1/3 Chai"` thành `0.3333`, nhưng UI vẫn có thể hiển thị dạng phân số `"1/3"`
- `"Sáng 1 viên"` thành `schedule.morning = 1`
- `"Ngày uống 7ml chia 2 lần"` thành `divided_dose`, gợi ý khung Sáng/Tối
- `"Khi sốt >= 38.5 độ"` thành `as_needed` (Khi cần), không tạo lịch cố định
- Lịch trước ăn/sau ăn được tách vào slot giờ riêng biệt (VD: `morning_before_meal`)
- Mỗi loại thuốc được tự động tính `duration_days` riêng
- `prescription_days` (Tổng số ngày điều trị) là số ngày lớn nhất của các thuốc có lịch cố định

Các `schedule_mode` (Kiểu lịch):

```text
fixed_schedule  # Thuốc có liều cố định theo Sáng/Trưa/Chiều/Tối
divided_dose    # Tổng liều dùng trong ngày chia làm N lần
as_needed       # Uống khi có triệu chứng, không lập lịch nhắc cố định
unknown         # Dữ liệu bất thường/thiếu, cần người dùng tự kiểm tra lại
```

## API chính

Tham khảo các endpoints chính nếu muốn tích hợp hoặc debug:
- `GET /` - Healthcheck
- `POST /api/prescriptions/ocr` - Xử lý ảnh đơn thuốc
- `GET /api/prescriptions/{id}/edit` - Lấy Payload giao diện (Tab 2)
- `GET /api/prescriptions/{id}/schedule` - Lấy Payload tính toán khung giờ (Tab 3)
- `POST /api/prescriptions/{id}/schedule` - Lưu cấu hình giờ & tạo URL Lịch
- `GET /api/prescriptions/{id}/calendar.ics` - Download lịch ICS

## Lỗi thường gặp

### Streamlit báo file không tồn tại
Đảm bảo bạn đang mở terminal tại thư mục **`codebase/`** thay vì thư mục gốc của project.
```powershell
cd codebase
.\.venv_ui\Scripts\python.exe -m streamlit run frontend/streamlit_app.py
```

### OCR trả lỗi thiếu API key
Đảm bảo đã thiết lập biến `GEMINI_API_KEY` trong file `.env`. Sau khi sửa, cần phải khởi động lại Backend.

### Backend reload liên tục (lỗi vòng lặp)
Luôn chạy uvicorn kèm cờ `--reload-dir app` để tránh việc engine theo dõi nhầm các thay đổi bên trong thư mục môi trường ảo (`.venv_api`).
