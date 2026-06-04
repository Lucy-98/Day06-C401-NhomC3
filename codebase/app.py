import pandas as pd
import streamlit as st


# ==================================================
# AI SERVICE (MOCK)
# ==================================================

def analyze_prescription(image):
    """
    Giả lập OCR + AI Extraction
    Sau này thay bằng API thật.
    """

    return {
        "data": {
            "hospital_name": "Bệnh viện Đà Nẵng",
            "patient_name": "[HIDDEN]",
            "patient_dob_prob": None,
            "patient_gender": "Nam",
            "patient_dob": "",
            "patient_address":
                "Phường An Hải Đông, Quận Sơn Trà, Thành phố Đà Nẵng",
            "patient_address_prob": None,
            "patient_gender_prob": None,
            "patient_name_prob": None,
            "hospital_name_prob": None,
            "diagnose":
                "Thấp không ảnh hưởng đến tim",
            "diagnose_prob": None,
            "cropped_image_url": "",

            "table_information": [
                {
                    "no": 1,
                    "medicine_name":
                        "Penicilin 400.000 UI",

                    "medicine_count": 30,

                    "medicine_name_prob": None,
                    "medicine_count_prob": None,
                    "medicine_guide_prob": None,

                    "medicine_guide": {
                        "summary":
                            "Uống: Sáng 2 viên, Trưa 2 viên, Chiều 2 viên",

                        "frequency": 0,
                        "use": "Uống",
                        "note": None,
                        "times":
                            "Sáng, Trưa, Chiều",

                        "guide_morning":
                            "2 viên",

                        "guide_noon":
                            "2 viên",

                        "guide_afternoon":
                            "2 viên",

                        "guide_evening":
                            "",

                        "use_count": 6,
                        "type": "Viên"
                    }
                },

                {
                    "no": 2,
                    "medicine_name":
                        "Paracetamol 500mg",

                    "medicine_count": 10,

                    "medicine_name_prob": None,
                    "medicine_count_prob": None,
                    "medicine_guide_prob": None,

                    "medicine_guide": {
                        "summary":
                            "Uống: Sáng 1 viên, Chiều 1 viên",

                        "frequency": 0,
                        "use": "Uống",
                        "note": None,
                        "times":
                            "Sáng, Chiều",

                        "guide_morning":
                            "1 viên",

                        "guide_noon":
                            "",

                        "guide_afternoon":
                            "1 viên",

                        "guide_evening":
                            "",

                        "use_count": 2,
                        "type": "Viên"
                    }
                }
            ],

            "table_information_prob": None
        },

        "errorCode": None,
        "errorMessage": None
    }


# ==================================================
# HELPER
# ==================================================

def hien_thi(value):
    if value is None or value == "":
        return "Không có dữ liệu"
    return value


# ==================================================
# RENDER KẾT QUẢ
# ==================================================

def render_result(response):

    data = response["data"]

    st.success("Phân tích thành công")

    # ==================================
    # BỆNH VIỆN
    # ==================================

    st.header("🏥 Thông Tin Bệnh Viện")

    st.write(
        "**Tên bệnh viện:**",
        hien_thi(data["hospital_name"])
    )

    # ==================================
    # BỆNH NHÂN
    # ==================================

    st.header("👤 Thông Tin Bệnh Nhân")

    col1, col2 = st.columns(2)

    with col1:
        st.text_input(
            "Họ và tên",
            value=hien_thi(data["patient_name"]),
            disabled=True
        )

        st.text_input(
            "Ngày sinh",
            value=hien_thi(data["patient_dob"]),
            disabled=True
        )

    with col2:
        st.text_input(
            "Giới tính",
            value=hien_thi(data["patient_gender"]),
            disabled=True
        )

        st.text_area(
            "Địa chỉ",
            value=hien_thi(data["patient_address"]),
            disabled=True
        )

    # ==================================
    # CHẨN ĐOÁN
    # ==================================

    st.header("🩺 Chẩn Đoán")

    st.info(
        hien_thi(data["diagnose"])
    )

    # ==================================
    # DANH SÁCH THUỐC
    # ==================================

    st.header("💊 Danh Sách Thuốc")

    rows = []

    for med in data["table_information"]:

        rows.append({
            "STT": med["no"],
            "Tên thuốc": med["medicine_name"],
            "Số lượng": med["medicine_count"],
            "Hướng dẫn":
                med["medicine_guide"]["summary"]
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True
    )

    # ==================================
    # CHI TIẾT THUỐC
    # ==================================

    st.header("📋 Chi Tiết Thuốc")

    for med in data["table_information"]:

        with st.expander(
            f"Thuốc #{med['no']} - {med['medicine_name']}"
        ):

            st.write(
                "**Tên thuốc:**",
                med["medicine_name"]
            )

            st.write(
                "**Số lượng:**",
                med["medicine_count"]
            )

            guide = med["medicine_guide"]

            st.subheader(
                "Hướng Dẫn Sử Dụng"
            )

            st.write(
                guide["summary"]
            )

            schedule_df = pd.DataFrame([
                {
                    "Sáng":
                        guide["guide_morning"],
                    "Trưa":
                        guide["guide_noon"],
                    "Chiều":
                        guide["guide_afternoon"],
                    "Tối":
                        guide["guide_evening"]
                }
            ])

            st.table(schedule_df)

    # ==================================
    # DEBUG
    # ==================================

    st.header("🐞 JSON Gốc")

    with st.expander(
        "Xem dữ liệu JSON"
    ):
        st.json(response)

# ==================================================
# MAIN
# ==================================================


def render_analysis(response):

    data = response["data"]
    medicines = data["table_information"]

    st.header("🤖 Phân Tích Điều Trị")

    # ==================================
    # TỔNG QUAN
    # ==================================

    total_medicines = len(medicines)

    total_use_count = sum(
        med["medicine_guide"]["use_count"]
        for med in medicines
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "💊 Số loại thuốc",
            total_medicines
        )

    with col2:
        st.metric(
            "🕒 Tổng số lần dùng/ngày",
            total_use_count
        )

    st.divider()

    # ==================================
    # SINH LỊCH NHẮC UỐNG THUỐC
    # ==================================

    reminders = []

    for med in medicines:

        guide = med["medicine_guide"]

        if guide["guide_morning"]:
            reminders.append({
                "Giờ": "08:00",
                "Thuốc": med["medicine_name"],
                "Liều lượng":
                    guide["guide_morning"]
            })

        if guide["guide_noon"]:
            reminders.append({
                "Giờ": "12:00",
                "Thuốc": med["medicine_name"],
                "Liều lượng":
                    guide["guide_noon"]
            })

        if guide["guide_afternoon"]:
            reminders.append({
                "Giờ": "17:00",
                "Thuốc": med["medicine_name"],
                "Liều lượng":
                    guide["guide_afternoon"]
            })

        if guide["guide_evening"]:
            reminders.append({
                "Giờ": "21:00",
                "Thuốc": med["medicine_name"],
                "Liều lượng":
                    guide["guide_evening"]
            })

    reminders.sort(key=lambda x: x["Giờ"])

    # ==================================
    # BẢNG NHẮC UỐNG THUỐC
    # ==================================

    st.subheader("📅 Bảng Nhắc Uống Thuốc")

    reminder_df = pd.DataFrame(reminders)

    st.dataframe(
        reminder_df,
        use_container_width=True
    )

    st.divider()

    # ==================================
    # TIMELINE
    # ==================================

    st.subheader("⏰ Timeline Trong Ngày")

    for item in reminders:

        st.info(
            f"""
⏰ {item['Giờ']}

💊 {item['Thuốc']}

📦 {item['Liều lượng']}
"""
        )

    st.divider()

    # ==================================
    # AI SUMMARY
    # ==================================

    st.subheader("🧠 Tóm Tắt Điều Trị")

    medicine_names = [
        med["medicine_name"]
        for med in medicines
    ]

    unique_times = sorted(
        list(
            set(
                item["Giờ"]
                for item in reminders
            )
        )
    )

    st.success(
        f"""
Bệnh nhân hiện đang sử dụng {total_medicines} loại thuốc.

Các thuốc gồm:

{', '.join(medicine_names)}

Tổng số lần sử dụng trong ngày:
{total_use_count} lần.

Các khung giờ cần uống thuốc:

{', '.join(unique_times)}
"""
    )

    st.divider()

    # ==================================
    # CẢNH BÁO
    # ==================================

    st.subheader("⚠️ Cảnh Báo")

    if total_use_count >= 6:

        st.warning(
            """
Lịch dùng thuốc tương đối dày.

Khuyến nghị:

• Bật thông báo nhắc uống thuốc

• Không bỏ liều

• Uống đúng khung giờ
"""
        )

    else:

        st.success(
            """
Lịch dùng thuốc đơn giản.

Người dùng có thể dễ dàng tuân thủ.
"""
        )

    st.divider()

    # ==================================
    # THỐNG KÊ THUỐC
    # ==================================

    st.subheader("📊 Thống Kê Thuốc")

    stat_rows = []

    for med in medicines:

        stat_rows.append({
            "Thuốc": med["medicine_name"],
            "Số lượng":
                med["medicine_count"],
            "Số lần/ngày":
                med["medicine_guide"]["use_count"]
        })

    stat_df = pd.DataFrame(stat_rows)

    st.dataframe(
        stat_df,
        use_container_width=True
    )


def main():

    st.set_page_config(
        page_title="AI Prescription Viewer",
        layout="wide"
    )

    st.title(
        "📄 AI Prescription Viewer"
    )

    st.markdown(
        """
        Chụp hoặc tải ảnh đơn thuốc,
        sau đó nhấn nút phân tích.
        """
    )

    # ==================================
    # CAMERA
    # ==================================

    st.header("📸 Chụp Ảnh Đơn Thuốc")

    camera_image = st.camera_input(
        "Chụp ảnh"
    )

    # ==================================
    # UPLOAD
    # ==================================

    uploaded_file = st.file_uploader(
        "Hoặc tải ảnh lên",
        type=[
            "jpg",
            "jpeg",
            "png"
        ]
    )

    image = None

    if camera_image:
        image = camera_image

    elif uploaded_file:
        image = uploaded_file

    # ==================================
    # PREVIEW
    # ==================================

    if image:

        st.image(
            image,
            caption="Ảnh đơn thuốc",
            use_container_width=True
        )

        if st.button(
            "🔍 Phân Tích Đơn Thuốc"
        ):

            with st.spinner(
                "Đang xử lý..."
            ):

                response = (
                    analyze_prescription(
                        image
                    )
                )

                st.session_state[
                    "result"
                ] = response

    # ==================================
    # RESULT
    # ==================================

    if "result" in st.session_state:

        response = st.session_state["result"]

        tab1, tab2 = st.tabs([
            "📄 Đơn Thuốc",
            "🤖 Phân Tích Điều Trị"
        ])

        with tab1:
            render_result(response)

        with tab2:
            render_analysis(response)


if __name__ == "__main__":
    main()
