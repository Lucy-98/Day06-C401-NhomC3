import streamlit as st
import pandas as pd
import plotly.express as px


# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="AI Prescription Viewer",
    page_icon="💊",
    layout="wide"
)


# ==================================================
# MOCK AI SERVICE
# ==================================================

def analyze_prescription(image):
    """
    Mock OCR + AI Extraction
    Sau này thay bằng:
    - OpenAI Vision
    - Gemini Vision
    - OCR API
    """

    return {
        "data": {
            "hospital_name": "Bệnh viện Đà Nẵng",
            "patient_name": "[HIDDEN]",
            "doctor_name": "Nguyễn Văn A",
            "visit_date": "2026-06-04",
            "diagnosis": "Viêm họng cấp"
        },

        "medications": [
            {
                "name": "Paracetamol 500mg",
                "dosage": "1 viên",
                "frequency": "3 lần/ngày",
                "duration": "5 ngày"
            },
            {
                "name": "Amoxicillin 500mg",
                "dosage": "1 viên",
                "frequency": "2 lần/ngày",
                "duration": "7 ngày"
            },
            {
                "name": "Vitamin C",
                "dosage": "1 viên",
                "frequency": "1 lần/ngày",
                "duration": "10 ngày"
            }
        ],

        "analysis": {
            "condition_summary":
                "Bệnh nhân có dấu hiệu viêm họng cấp. "
                "Đơn thuốc bao gồm thuốc giảm đau hạ sốt, "
                "kháng sinh và vitamin hỗ trợ.",

            "warnings": [
                "Không tự ý ngưng kháng sinh.",
                "Uống thuốc sau ăn.",
                "Nếu sốt kéo dài > 3 ngày cần tái khám."
            ]
        }
    }


# ==================================================
# SIDEBAR
# ==================================================

st.sidebar.title("⚙️ AI Prescription Viewer")

st.sidebar.info(
    """
    MVP Demo

    Features:
    - Upload toa thuốc
    - AI OCR (Mock)
    - Prescription Analysis
    - Medication Timeline
    """
)

st.sidebar.success("Version 1.0")


# ==================================================
# HEADER
# ==================================================

st.title("💊 AI Prescription Viewer")
st.caption(
    "Upload ảnh toa thuốc để AI phân tích thông tin điều trị"
)

st.divider()


# ==================================================
# IMAGE INPUT
# ==================================================

tab1, tab2 = st.tabs(["📤 Upload", "📷 Camera"])

uploaded_file = None

with tab1:
    uploaded_file = st.file_uploader(
        "Upload Prescription Image",
        type=["jpg", "jpeg", "png"]
    )

with tab2:
    camera_file = st.camera_input(
        "Take Prescription Photo"
    )

    if camera_file:
        uploaded_file = camera_file


# ==================================================
# MAIN LOGIC
# ==================================================

if uploaded_file:

    col1, col2 = st.columns([1, 2])

    # ==========================================
    # IMAGE PREVIEW
    # ==========================================

    with col1:
        st.subheader("📄 Prescription")

        st.image(
            uploaded_file,
            use_container_width=True
        )

    # ==========================================
    # AI ANALYSIS
    # ==========================================

    with st.spinner("🤖 AI is analyzing prescription..."):

        result = analyze_prescription(uploaded_file)

    with col2:

        st.subheader("🏥 Visit Information")

        info = result["data"]

        c1, c2 = st.columns(2)

        c1.metric(
            "Hospital",
            info["hospital_name"]
        )

        c2.metric(
            "Doctor",
            info["doctor_name"]
        )

        st.write("**Visit Date:**", info["visit_date"])
        st.write("**Diagnosis:**", info["diagnosis"])

    st.divider()

    # ==========================================
    # MEDICATION TABLE
    # ==========================================

    st.subheader("💊 Prescribed Medications")

    med_df = pd.DataFrame(
        result["medications"]
    )

    st.dataframe(
        med_df,
        use_container_width=True
    )

    st.divider()

    # ==========================================
    # AI SUMMARY
    # ==========================================

    st.subheader("🧠 AI Treatment Summary")

    st.info(
        result["analysis"]["condition_summary"]
    )

    st.subheader("⚠️ Warnings")

    for warning in result["analysis"]["warnings"]:
        st.warning(warning)

    st.divider()

    # ==========================================
    # MEDICATION TIMELINE
    # ==========================================

    st.subheader("⏰ Medication Schedule")

    schedule = []

    for med in result["medications"]:

        freq = med["frequency"]

        if "3" in freq:
            times = [
                "08:00",
                "13:00",
                "20:00"
            ]

        elif "2" in freq:
            times = [
                "08:00",
                "20:00"
            ]

        else:
            times = [
                "08:00"
            ]

        for t in times:
            schedule.append(
                {
                    "Medicine": med["name"],
                    "Time": t
                }
            )

    schedule_df = pd.DataFrame(schedule)

    st.dataframe(
        schedule_df,
        use_container_width=True
    )

    st.divider()

    # ==========================================
    # DASHBOARD
    # ==========================================

    st.subheader("📊 Prescription Dashboard")

    chart_df = pd.DataFrame(
        {
            "Medicine": [
                med["name"]
                for med in result["medications"]
            ],
            "Count": [1, 1, 1]
        }
    )

    fig = px.bar(
        chart_df,
        x="Medicine",
        y="Count",
        title="Medication Overview"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:

    st.info(
        "Upload hoặc chụp ảnh toa thuốc để bắt đầu."
    )

    st.image(
        "https://images.unsplash.com/photo-1587854692152-cbe660dbde88",
        width=400
    )
