import streamlit as st
from docx import Document
import pandas as pd
import re

# --- ตั้งค่าหน้าเว็บหลัก ---
st.set_page_config(page_title="ระบบรายงานการใช้หลักสูตร (Word)", page_icon="📝", layout="wide")

st.title("📝 ระบบรายงานการใช้หลักสูตรอัตโนมัติ")
st.subheader("สกัดข้อมูลจากไฟล์แผนการสอน Word (.docx) เพื่อส่งออกรายงานสรุป PDF")
st.write("---")

# ฟอร์มข้อมูลคุณครูและรายวิชา
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

# ล็อกตารางเริ่มต้นไว้ในระบบไม่ให้หายไปไหน
if "curriculum_data" not in st.session_state:
    st.session_state.curriculum_data = [
        {"หน่วยที่/หัวข้อ": "หน่วยที่ 1 (ตัวอย่างคลิกพิมพ์แก้ไขได้)", "จำนวนชั่วโมง (สะสม)": 0}
    ]

# แผงควบคุมการอัปโหลดเอกสารเปลี่ยนเป็น Word (.docx)
st.write("### 📂 แนบเอกสารต้นฉบับ (ไฟล์ Word)")
uploaded_file = st.file_uploader("กรุณาแนบไฟล์แผนการสอน หรือกำหนดการสอน (รูปแบบ .docx เท่านั้น)", type=["docx"])

# ฟังก์ชันอ่านโครงสร้างตารางจากไฟล์ Word
def extract_tables_from_word(file):
    extracted_rows = []
    # เปิดอ่านไฟล์ Word
    doc = Document(file)
    # วิ่งไล่อ่านทุกตารางในไฟล์ Word
    for table in doc.tables:
        for row in table.rows:
            # ดึงข้อความในแต่ละช่อง (Cell) ออกมาทำความสะอาด
            clean_row = [cell.text.strip() for cell in row.cells]
            # กรองค่าซ้ำที่เกิดจากกรณีตารางผสานเซลล์ (Merged Cells)
            unique_row = []
            for item in clean_row:
                if not unique_row or item != unique_row[-1]:
                    unique_row.append(item)
            if any(unique_row):
                extracted_rows.append(unique_row)
    return extracted_rows

# ฟังก์ชันคัดกรองหน่วยการสอนและชั่วโมง
def filter_curriculum_data(raw_rows):
    final_units = []
    for row in raw_rows:
        row_text = " ".join(row)
        # ตรวจจับคำสำคัญภาษาไทยในแถวตาราง Word
        if any(keyword in row_text for keyword in ["หน่วยที่", "บทที่", "หัวข้อ", "สัปดาห์ที่", "เนื้อหา", "สาระ"]):
            unit_name = ""
            hours = "0"
            for cell in row:
                # หาตัวเลขในช่องที่คาดว่าเป็นชั่วโมงเรียน
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
    return final_units

# ปุ่มสั่งสแกนไฟล์ Word
if uploaded_file is not None:
    if st.button("⚡ ดึงข้อมูลจากไฟล์ Word ลงตารางด้านล่าง"):
        with st.spinner("⏳ ระบบกำลังอ่านตารางจากไฟล์ Word..."):
            try:
                raw_rows = extract_tables_from_word(uploaded_file)
                parsed_list = filter_curriculum_data(raw_rows)
                
                if parsed_list:
                    st.session_state.curriculum_data = parsed_list
                    st.success("✅ ดึงข้อมูลจากไฟล์ Word สำเร็จ! ตรวจทานข้อมูลในตารางด้านล่างได้เลยครับ")
                else:
                    st.warning("⚠️ ไม่พบคำสำคัญ (เช่น 'หน่วยที่', 'ชั่วโมง') ในตารางไฟล์ Word นี้ แต่ท่านสามารถพิมพ์ข้อมูลเองในตารางด้านล่างได้ทันที")
            except Exception as e:
                st.error(f"ระบบขัดข้องในการอ่านไฟล์ Word: {str(e)}")

st.write("---")

# --- ตารางข้อมูลหลัก (พิมพ์มือแก้ไขได้ตลอดเวลา) ---
st.write("### 🔍 ตารางจัดทำข้อมูลหน่วยการสอน")
st.info("💡 คุณครูสามารถพิมพ์แก้ไข หรือกดปุ่ม ➕ Add row ด้านล่างตารางเพื่อเพิ่มแถวเองได้")

current_df = pd.DataFrame(st.session_state.curriculum_data)

edited_df = st.data_editor(
    current_df, 
    num_rows="dynamic", 
    use_container_width=True,
    key="my_word_data_editor"
)

# เซฟค่ากลับเข้าหน่วยความจำป้องกันตารางรีเซ็ต
if st.session_state.my_word_data_editor:
    st.session_state.curriculum_data = edited_df.to_dict('records')

# คำนวณผลรวมจำนวนชั่วโมงเรียน
try:
    total_hours = pd.to_numeric(edited_df["จำนวนชั่วโมง (สะสม)"]).sum()
except:
    total_hours = 0
st.metric(label="⏱️ จำนวนชั่วโมงเรียนรวมทั้งสิ้นในหลักสูตร", value=f"{total_hours} ชั่วโมง")

st.write("---")

# --- โครงสร้างกระบวนการออกรายงานไฟล์สรุป PDF ---
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
    u_name = row["หน่วยที่/หัวข้อ"] if pd.notnull(row["หน่วยที่/หัวข้อ"]) else ""
    u_hour = row["จำนวนชั่วโมง (สะสม)"] if pd.notnull(row["จำนวนชั่วโมง (สะสม)"]) else 0
    report_text += f"- {u_name} | เวลา: {u_hour} ชม.\n"
    
report_text += "--------------------------------------------------\n"
report_text += "\nลงชื่อ..................................................ผู้รายงาน\n"
report_text += f"    ( {teacher_name if teacher_name else '..................................................'} )\n"
report_text += "================================================--"

pdf_bytes = report_text.encode('utf-8')

# ปุ่มดาวน์โหลดไฟล์รายงาน PDF
st.download_button(
    label="📥 ดาวน์โหลดรายงานสรุปการใช้หลักสูตร (ไฟล์ PDF)",
    data=pdf_bytes,
    file_name=f"รายงานการใช้หลักสูตร_{course_code if course_code else 'วิชา'}.pdf",
    mime="application/pdf",
    use_container_width=True
)
