# SPEC Sản Phẩm: Tính năng Nhắc dùng thuốc (App Nhà thuốc Long Châu)

## 1. Bằng chứng

**Nỗi đau của người dùng:**
- **Trải nghiệm trực tiếp:** Khi nhận đơn thuốc từ bệnh viện hoặc mua thuốc tại nhà thuốc, người dùng thường phải tự nhớ lịch uống thuốc hoặc tự cài báo thức bằng tay. Việc nhập liệu thủ công từng loại thuốc, số lượng, và giờ uống (sáng/trưa/chiều/tối) rất mất thời gian và dễ dẫn đến sai sót hoặc lười biếng bỏ dở.
- **Quan sát bên ngoài:** Khách hàng người cao tuổi thường xuyên quên uống thuốc hoặc nhầm lẫn liều lượng (như chia liều, uống khi cần) do các đơn thuốc ghi chú phức tạp. Các ứng dụng nhắc thuốc hiện tại trên thị trường thường bắt người dùng nhập tay toàn bộ thông tin từ đầu, tạo rào cản lớn khi bắt đầu sử dụng.

## 2. Lát cắt để build

**Một người dùng (bệnh nhân/người nhà)** chụp ảnh đơn thuốc, **AI tự động trích xuất thông tin (OCR)** và **gợi ý lịch uống thuốc chi tiết**, sau đó người dùng kiểm tra lại và **lưu lịch nhắc nhở thẳng vào Calendar của điện thoại** một cách nhanh chóng.

## 3. AI Product Canvas

| Ô | Trả lời |
|---|---------|
| **Value (Giá trị)** | Giúp người bệnh (đặc biệt khách hàng của Long Châu) tiết kiệm thời gian tạo lịch nhắc uống thuốc, giảm thiểu việc quên thuốc hoặc uống sai liều. AI giải quyết khâu nhập liệu thủ công nhàm chán và phức tạp. |
| **Trust (Niềm tin)** | AI chỉ đóng vai trò "người nhập liệu hộ". Toàn bộ thông tin AI đọc được sẽ hiển thị rõ ràng trên UI màn hình "Tạo đơn" để người dùng đối chiếu với ảnh gốc và tự do chỉnh sửa trước khi xuất lịch hẹn. |
| **Feasibility (Tính khả thi)** | Rất khả thi. Sử dụng Google Gemini 2.5 Flash xử lý OCR cực kỳ nhanh và xuất dữ liệu định dạng JSON có cấu trúc rất tốt. Việc tạo file `.ics` cũng đơn giản và được hỗ trợ native trên iOS/Android. |
| **Tín hiệu học** | Bất cứ khi nào người dùng chỉnh sửa (sửa tên thuốc, liều lượng) thay vì chấp nhận kết quả OCR mặc định, dữ liệu đó có thể được lưu lại (feedback loop) để đánh giá độ chính xác của model và cải thiện prompt. |

## 4. Tăng năng lực hay tự động hóa

**Quyết định: Tăng năng lực (Augment).**
- **Lý do:** Y tế là lĩnh vực nhạy cảm, việc tự động hóa (automate) tạo báo thức mà không có sự kiểm duyệt của con người có thể gây hậu quả nghiêm trọng nếu AI đọc sai liều (ví dụ 1/2 viên thành 12 viên).
- **Phạm vi của AI:** AI chỉ "gợi ý và chuẩn bị" form dữ liệu. Con người luôn giữ quyền quyết định ở bước kiểm tra bảng nhắc và bấm nút "Lưu giờ nhắc".

## 5. Bốn đường đi của trải nghiệm

| Đường đi | Xử lý |
|----------|-------|
| **Đường thuận** | AI đọc chính xác 100% đơn thuốc rõ ràng -> UI hiển thị chuẩn các slot Sáng/Trưa/Chiều/Tối -> Người dùng chỉ việc kiểm tra và bấm "Lưu giờ nhắc". |
| **Khi AI không chắc** | Gặp thuốc có ghi chú đặc biệt ("uống khi sốt", "chia 2 lần") -> AI phân loại vào nhóm `as_needed` (khi cần) hoặc `divided_dose` và hiện cảnh báo để người dùng chú ý tinh chỉnh thêm. |
| **Khi AI sai** | AI nhận diện sai chữ viết tay -> Người dùng trực tiếp ấn vào ô dữ liệu trên giao diện màn "Tạo đơn" để gõ lại cho đúng. |
| **Khi người dùng sửa** | Dữ liệu người dùng sửa khác với file raw JSON ban đầu -> Log lại sự kiện này trên backend để tracking tỷ lệ lỗi của OCR, làm cơ sở cải thiện trong tương lai. |

## 6. Những kiểu lỗi đáng lo nhất

1. **Sai liều lượng nghiêm trọng:** 
   - *Khi nào:* AI nhầm lẫn các ký tự số (ví dụ 1/4 thành 14) do chữ viết tay bác sĩ xấu hoặc bị mờ.
   - *Hậu quả:* Người bệnh có thể uống quá liều gây ngộ độc.
   - *Xử lý (Prototype):* Backend có logic chuẩn hóa `PrescriptionNormalizer` để xử lý phân số. Giao diện luôn bắt buộc người dùng xem lại bảng tóm tắt lịch uống và có thể đưa ra cảnh báo nếu liều lượng một lần uống bất thường.
2. **Nhận diện sai loại lịch uống (Schedule Mode):** 
   - *Khi nào:* Lời dặn "Uống cách ngày" nhưng AI lại cho vào lịch uống hàng ngày.
   - *Hậu quả:* Uống sai phác đồ điều trị.
   - *Xử lý:* Cung cấp tùy chọn cho phép người dùng tự đổi loại lịch (Cố định, Khi cần, v.v.).

## 7. Kế hoạch kiểm thử và bằng chứng demo

Để chứng minh được tính khả thi và cách AI giải quyết các ca khó, nhóm chuẩn bị sẵn 2 kịch bản test (test cases) đi kèm với luồng demo chi tiết:

### 7.1. Kịch bản 1: Đầu vào đường thuận (Happy Case - `samples/case1.json`)
- **Mục tiêu:** Chứng minh AI có khả năng bóc tách nhanh và chính xác 100% đối với đơn thuốc tiêu chuẩn.
- **Dữ liệu đầu vào:** Đơn thuốc in máy rõ nét, ghi rõ tên thuốc, số lượng (VD: 30 viên) và liều dùng theo buổi (Sáng 1 viên, Tối 1 viên).
- **Kỳ vọng hiển thị (Expected Output):**
  - Màn hình "Tạo đơn" tự động điền đầy đủ các thông tin: Tên bệnh nhân, ngày bắt đầu, thời gian dùng (số ngày uống).
  - Bảng danh sách thuốc tự động mapping chính xác số lượng vào các cột: Sáng (1) - Tối (1), loại lịch (Schedule Mode) là `fixed_schedule`.
  - Người dùng hầu như không cần chỉnh sửa gì thêm, chỉ việc bấm nút để sinh ra file lịch `.ics`.

### 7.2. Kịch bản 2: Đầu vào gây nhiễu và phức tạp (Edge Case - `samples/case6.json`)
- **Mục tiêu:** Thể hiện khả năng phục hồi và xử lý thông minh của sản phẩm (AI + Logic chuẩn hóa) khi gặp đơn thuốc có chỉ định phức tạp mà các hệ thống nhập tay thông thường không xử lý được.
- **Dữ liệu đầu vào:** Đơn thuốc chứa các chỉ định khó như: thuốc dạng nước (ml), dặn dò "uống chia 2 lần", và đặc biệt là "uống khi sốt >= 38.5 độ".
- **Kỳ vọng xử lý của Backend & AI:**
  - **Nhận diện `as_needed` (Khi cần):** Với thuốc "uống khi sốt", hệ thống tự động gán loại lịch uống là `as_needed`. Thuốc này sẽ **không** được đưa vào lịch báo thức cố định Sáng/Trưa/Chiều/Tối để tránh làm phiền người bệnh khi họ không sốt.
  - **Nhận diện `divided_dose` (Chia liều):** Với thuốc dặn uống "chia 2 lần", hệ thống sẽ tính toán tổng liều lượng và hiện cảnh báo (Warning) màu vàng trên giao diện UI để nhắc nhở người bệnh chú ý chia nhỏ liều lượng.
  - Hệ thống cho phép người dùng linh hoạt đổi loại lịch trên UI nếu cần.

### 7.3. Kịch bản Demo trực tiếp và Thu thập bằng chứng
Khi đứng demo trước hội đồng, nhóm sẽ trình bày qua các bước:
1. **Trình bày Nỗi đau:** Nêu bật khó khăn khi tự nhập lịch uống thuốc bằng tay qua 1 slide ngắn.
2. **Demo tính năng (Luồng thực tế):** 
   - Mở giao diện web Streamlit, chọn tính năng đọc `case1.json` và `case6.json` (hoặc upload ảnh thật nếu mạng ổn định).
   - Biểu diễn tính năng **Human-in-the-loop (Người dùng duyệt)**: Trực tiếp click vào một trường thông tin trên màn "Tạo đơn" và sửa đổi (mô phỏng AI có thể sai số lượng) để chứng minh hệ thống cho phép hoàn tác và chỉnh sửa dễ dàng.
   - Chuyển sang tab "Hẹn giờ nhắc", bấm "Lưu giờ nhắc" và xuất file `.ics`. Mở file `.ics` bằng ứng dụng Lịch (Apple/Google Calendar) để chứng minh luồng **chạy thật end-to-end**.
3. **Bằng chứng kỹ thuật (Technical Evidence):**
   - Mở terminal chạy backend để show các log requests được gửi/nhận với mô hình Gemini.
   - Mở tab "Raw JSON" để trình chiếu sự khác biệt giữa dữ liệu thô (do AI trả về) và dữ liệu Normalized (sau khi đi qua logic chuẩn hóa `PrescriptionNormalizer` của backend) để giám khảo thấy rõ cách nhóm xử lý rác/nhiễu.

## 8. Phân công

1. Lê Quang Minh - 2A202600801         : Build BE
2. Nông Đức Hoàng - 2A202600580        : QA + Test
3. Nguyễn Đức Minh - 2A202600604       : Build FE
4. Lưu Xuân Thế - 2A202600983          : Build AI logic
5. Nguyễn Quang Anh - 2A202600608      : Report + Slide
6. Lương Thị Hồng Nhung - 2A202600811  : Build BE