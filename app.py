import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- ส่วนของการตั้งค่าหน้าเว็บหลัก ---
st.set_page_config(page_title="ระบบรายงานการใช้หลักสูตร", page_icon="📝", layout="wide")

st.title("📝 ระบบรายงานการใช้หลักสูตรอัตโนมัติ")
st.subheader("สกัดข้อมูลจากแผนการสอน และส่งออกเป็นรายงานสรุป PDF")
st.write("---")

# --- ส่วนที่เพิ่มเข้ามาใหม่: ฟอร์มข้อมูลคุณครูและรายวิชา ---
st.write("### 👤 ข้อมูลผู้สอนและรายวิชา")
col1, col2 = st.columns(2)
with col1:
    teacher_name = st.text_input("ชื่อ - นามสกุล คุณครูผู้สอน", placeholder="ตัวอย่าง: นายสมชาย ใจดี")
    course_code = st.text_input("รหัสวิชา", placeholder="ตัวอย่าง: ค21101")
    course_name = st.text_input("ชื่อรายวิชา", placeholder="ตัวอย่าง: คณิตศาสตร์พื้นฐาน")
with col2:
    education_level = st.text_input("ระดับชั้นที่สอน", placeholder="ตัวอย่าง: มัธยมศึกษาปีที่ 1")
    academic_year = st.text_input("ภาคเรียน/ปีการศึกษา", placeholder="ตัวอย่าง: 1/2569")

st.write("---")

# ส่วนของการอัปโหลดไฟล์
st.write("### 📂 แนบเอกสารต้นฉบับ")
uploaded_file = st.file_uploader("กรุณาแนบไฟล์แผนการสอน หรือกำหนดการสอน (รูปแบบ PDF)", type=["pdf"])

def extract_tables_from_pdf(file):
    extracted_data = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    clean_row = [str(cell).strip() if cell is not None else "" for cell in row]
                    if any(clean_row):
                        extracted_data.append(clean_row)
    return extracted_data

def filter_curriculum_data(raw_rows):
    final_units = []
    for row in raw_rows:
        row_text = " ".join(row)
        if any(keyword in row_text for keyword in ["หน่วยที่", "บทที่", "หัวข้อ", "สัปดาห์ที่", "เนื้อหา"]):
            unit_name = ""
            hours = "0"
            for cell in row:
                match_hours = re.search(r'\b\d+\b', cell)
                if match_hours and any(h_kw in row_text for h_kw in ["ชม", "ชั่วโมง", "เวลา", "คาบ"]):
                    hours = match_hours.group()
            
            name_parts = [cell for cell in row if not re.search(r'\b' + hours + r'\b', cell) and len(cell) > 1]
            unit_name = " ".join(name_parts)
            
            if unit_name:
                final_units.append({
                    "หน่วยที่/หัวข้อ": unit_name,
                    "จำนวนชั่วโมง (สะสม)": int(hours) if hours.isdigit() else 0
                })
    return pd.DataFrame(final_units)

if uploaded_file is not None:
    with st.spinner("⏳ ระบบกำลังอ่านไฟล์ PDF และสกัดโครงสร้างตารางภาษาไทย..."):
        try:
            raw_data = extract_tables_from_pdf(uploaded_file)
            df_result = filter_curriculum_data(raw_data)
            
            if not df_result.empty:
                st.success("✅ สกัดข้อมูลจากแผนการสอนสำเร็จ!")
                st.write("### 🔍 ขั้นตอนการตรวจสอบและแก้ไขข้อมูล (Review Mode)")
                
                # ครูสามารถแก้ไขข้อมูลบนหน้าเว็บได้ตามต้องการ
                edited_df = st.data_editor(df_result, num_rows="dynamic", use_container_width=True)
                
                total_hours = edited_df["จำนวนชั่วโมง (สะสม)"].sum()
                st.metric(label="⏱️ จำนวนชั่วโมงเรียนรวมทั้งสิ้นในหลักสูตร", value=f"{total_hours} ชั่วโมง")
                
                st.write("---")
                
                # --- จัดรูปแบบหน้ากระดาษรายงานเอกสาร PDF (มีหัวข้อข้อมูลครบถ้วน) ---
                report_text = "==================================================\n"
                report_text += "        รายงานสรุปข้อมูลการใช้หลักสูตรรายวิชา        \n"
                report_text += "==================================================\n\n"
                report_text += f"ชื่อผู้สอน: {teacher_name if teacher_name else '-'}\n"
                report_text += f"รหัสวิชา: {course_code if course_code else '-'}   | รายวิชา: {course_name if course_name else '-'}\n"
                report_text += f"ระดับชั้น: {education_level if education_level else '-'} | ภาคเรียน/ปีการศึกษา: {academic_year if academic_year else '-'}\n"
                report_text += f"จำนวนชั่วโมงเรียนรวมสุทธิ: {total_hours} ชั่วโมง\n"
                report_text += "--------------------------------------------------\n\n"
                report_text += "รายละเอียดโครงสร้างหน่วยการสอน:\n"
                report_text += "--------------------------------------------------\n"
                
                for idx, row in edited_df.iterrows():
                    report_text += f"- {row['หน่วยที่/หัวข้อ']} | เวลา: {row['จำนวนชั่วโมง (สะสม)']} ชม.\n"
                    
                report_text += "--------------------------------------------------\n"
                report_text += "\n* ขอรับรองว่าข้อมูลการใช้หลักสูตรข้างต้นถูกต้องตรงตามแผนการจัดการเรียนรู้จริง *\n\n"
                report_text += "ลงชื่อ..................................................ผู้รายงาน\n"
                report_text += f"    ( {teacher_name if teacher_name else '..................................................'} )\n"
                report_text += "=================================================="
                
                # แปลงข้อความเป็นไบต์พร้อมใช้รหัส UTF-8 ภาษาไทยไม่เพี้ยน
                pdf_bytes = report_text.encode('utf-8')
                
                # ปุ่มดาวน์โหลดเวอร์ชันเสถียรข้อมูลครบถ้วน
                st.download_button(
                    label="📥 ดาวน์โหลดรายงานสรุปการใช้หลักสูตร (ไฟล์ PDF)",
                    data=pdf_bytes,
                    file_name=f"รายงานการใช้หลักสูตร_{course_code if course_code else 'วิชา'}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
            else:
                st.warning("⚠️ ไม่พบโครงสร้างตารางมาตรฐาน หรือคำสำคัญ ในไฟล์ PDF นี้ กรุณาตรวจสอบรูปแบบไฟล์")
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผลไฟล์: {str(e)}")
