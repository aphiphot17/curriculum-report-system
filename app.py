import streamlit as st
from docx import Document
import pandas as pd
import re
from io import BytesIO

# --- ตั้งค่าหน้าเว็บหลัก ---
st.set_page_config(page_title="ระบบรายงานการใช้หลักสูตร (Word)", page_icon="📝", layout="wide")

st.title("📝 ระบบรายงานการใช้หลักสูตรอัตโนมัติ")
st.subheader("สกัดข้อมูลจากไฟล์แผนการสอน Word และส่งออกเป็นรายงานสรุปเอกสาร Word (.docx)")
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

# แผงควบคุมการอัปโหลดเอกสาร Word (.docx)
st.write("### 📂 แนบเอกสารต้นฉบับ (ไฟล์ Word)")
uploaded_file = st.file_uploader("กรุณาแนบไฟล์แผนการสอน หรือกำหนดการสอน (รูปแบบ .docx เท่านั้น)", type=["docx"])

# ฟังก์ชันอ่านโครงสร้างตารางจากไฟล์ Word ขาเข้า
def extract_tables_from_word(file):
    extracted_rows = []
    doc = Document(file)
    for table in doc.tables:
        for row in table.rows:
            clean_row = [cell.text.strip() for cell in row.cells]
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
        if any(keyword in row_text for keyword in ["หน่วยที่", "บทที่", "หัวข้อ", "สัปดาห์ที่", "เนื้อหา", "สาระ"]):
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
    return final_units

# ปุ่มสั่งสแกนไฟล์ Word ขาเข้า
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

# --- [ฟังก์ชันสร้างไฟล์ Word ขาออก] สรุปข้อมูลรายงานส่งออกเป็นเอกสารมาตรฐาน ---
def create_word_report(df, t_name, c_code, c_name, e_level, a_year, t_hours):
    doc = Document()
    
    # สร้างหัวข้อเอกสารรายงาน
    doc.add_heading('รายงานสรุปข้อมูลการใช้หลักสูตรรายวิชา', level=1)
    
    # ใส่ข้อมูลรายละเอียดผู้สอน
    doc.add_paragraph(f"ชื่อผู้สอน: {t_name if t_name else '-'}")
    doc.add_paragraph(f"รหัสวิชา: {c_code if c_code else '-'}   | รายวิชา: {c_name if c_name else '-'}")
    doc.add_paragraph(f"ระดับชั้น: {e_level if e_level else '-'} | ภาคเรียน/ปีการศึกษา: {a_year if a_year else '-'}")
    doc.add_paragraph(f"จำนวนชั่วโมงเรียนรวมสุทธิ: {t_hours} ชั่วโมง")
    doc.add_paragraph("-" * 60)
    
    doc.add_heading('รายละเอียดโครงสร้างหน่วยการสอนที่สกัดได้', level=2)
    
    # สร้างตารางข้อมูลในไฟล์ Word ผลลัพธ์
    table = doc.add_table(rows=1, cols=2)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'หน่วยที่/หัวข้อ'
    hdr_cells[1].text = 'จำนวนชั่วโมง (สะสม)'
    
    for idx, row in df.iterrows():
        row_cells = table.add_row().cells
        row_cells[0].text = str(row["หน่วยที่/หัวข้อ"])
        row_cells[1].text = f"{str(row['จำนวนชั่วโมง (สะสม)'])} ชม."
        
    doc.add_paragraph("")
    doc.add_paragraph("-" * 60)
    doc.add_paragraph("\nลงชื่อ..................................................ผู้รายงาน")
    doc.add_paragraph(f"    ( {t_name if t_name else '..................................................'} )")
    
    # บันทึกเอกสารลงหน่วยความจำชั่วคราวเพื่อส่งให้ปุ่มดาวน์โหลด
    target_stream = BytesIO()
    doc.save(target_stream)
    target_stream.seek(0)
    return target_stream

# ประมวลผลและสร้างไฟล์ Word ขาออก ณ วินาทีที่คลิกดาวน์โหลด
word_file_stream = create_word_report(
    edited_df, teacher_name, course_code, course_name, education_level, academic_year, total_hours
)

# เปลี่ยนสถานะปุ่มดาวน์โหลดเป็นไฟล์ Word (.docx) ภาษาไทยไม่เพี้ยน แก้ไขต่อได้
st.download_button(
    label="📥 ดาวน์โหลดรายงานสรุปการใช้หลักสูตร (ไฟล์ Word .docx)",
    data=word_file_stream,
    file_name=f"รายงานการใช้หลักสูตร_{course_code if course_code else 'วิชา'}.docx",
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    use_container_width=True
)
