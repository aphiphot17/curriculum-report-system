import streamlit as st
from docx import Document
import pandas as pd
import re
from io import BytesIO

# --- ตั้งค่าหน้าเว็บหลัก ---
st.set_page_config(page_title="ระบบรายงานการใช้หลักสูตร (วิชาการ)", page_icon="📝", layout="wide")

st.title("📝 ระบบรายงานการใช้หลักสูตรอัตโนมัติ")
st.subheader("แปลงไฟล์แผนการสอน Word เป็นฟอร์มรายงานสรุปข้อมูลการใช้หลักสูตรรายวิชามาตรฐาน")
st.write("---")

# ส่วนที่ 1: ล็อกกล่องข้อความกรอกข้อมูลครูและรายวิชาตามแบบฟอร์มจริง
st.write("### 👤 ข้อมูลผู้สอนและรายวิชา (กรุณากรอกข้อมูลให้ครบถ้วน)")
col1, col2 = st.columns(2)
with col1:
    teacher_name = st.text_input("ชื่อผู้สอน", value="นายอภิภช เจริญกิจ")
    course_code = st.text_input("รหัสวิชา", value="30104-2026")
    course_name = st.text_input("รายวิชา", value="การติดตตั้งไฟฟ้า2")
with col2:
    education_level = st.text_input("ระดับชั้น", value="ปวส.")
    academic_year = st.text_input("ภาคเรียน/ปีการศึกษา", value="1/2569")

st.write("---")

# ล็อกตารางเริ่มต้นเพื่อเปิดโอกาสให้พิมพ์แก้ไขหรือทำตารางมือได้ตลอดเวลา
if "curriculum_data" not in st.session_state:
    st.session_state.curriculum_data = [
        {"หน่วยที่/หัวข้อ": "หน่วยที่ 1 ความปลอดภัยในการปฏิบัติงานและการตรวจสอบเครื่องมือไฟฟ้า", "จำนวนชั่วโมง (สะสม)": 4},
        {"หน่วยที่/หัวข้อ": "หน่วยที่ 2 ตรวจสอบสภาพความปลอดภัยของเครื่องมือไฟฟ้า", "จำนวนชั่วโมง (สะสม)": 6},
        {"หน่วยที่/หัวข้อ": "หน่วยที่ 3 ทดลองและวิเคราะห์ปักเสาไฟฟ้าคอนกรีตอัดแรง", "จำนวนชั่วโมง (สะสม)": 3},
        {"หน่วยที่/หัวข้อ": "หน่วยที่ 4 ติดตั้งชุดยึดโยงเสาไฟฟ้าป้องกันแรงดึงรั้ง", "จำนวนชั่วโมง (สะสม)": 3},
        {"หน่วยที่/หัวข้อ": "หน่วยที่ 5 ติดตั้งอุปกรณ์ควบคุมและป้องกันกระแสเกินบนเสาไฟฟ้า", "จำนวนชั่วโมง (สะสม)": 6},
        {"หน่วยที่/หัวข้อ": "หน่วยที่ 6 ระบบการต่อลงดินของอุปกรณ์ไฟฟ้าแรงสูง", "จำนวนชั่วโมง (สะสม)": 2},
        {"หน่วยที่/หัวข้อ": "หน่วยที่ 7 ติดตั้งหม้อแปลงไฟฟ้าชนิดจำหน่ายบนเสาไฟฟ้า", "จำนวนชั่วโมง (สะสม)": 3},
        {"หน่วยที่/หัวข้อ": "หน่วยที่ 8 ทดสอบระบบการทำงานของหม้อแปลงไฟฟ้าก่อนการจ่ายไฟ", "จำนวนชั่วโมง (สะสม)": 3},
        {"หน่วยที่/หัวข้อ": "หน่วยที่ 9 การติดตั้งและบำรุงรักษาระบบสายประธานและสายป้อน", "จำนวนชั่วโมง (สะสม)": 4},
        {"หน่วยที่/หัวข้อ": "หน่วยที่ 10 บำรุงรักษาระบบไฟฟ้าและหม้อแปลงไฟฟ้าประจำรอบ", "จำนวนชั่วโมง (สะสม)": 6}
    ]

# แผงควบคุมการอัปโหลดไฟล์เอกสารขาเข้า (.docx)
st.write("### 📂 แนบเอกสารต้นฉบับเพื่อสกัดคำ (ถ้ามี)")
uploaded_file = st.file_uploader("กรุณาแนบไฟล์แผนการสอน หรือกำหนดการสอน (.docx)", type=["docx"])

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

def filter_curriculum_data(raw_rows):
    final_units = []
    for row in raw_rows:
        row_text = " ".join(row)
        # ตรวจดักจับเฉพาะคำสำคัญระดับโครงสร้างรายวิชาจริง เลี่ยงข้อความซ้ำซ้อนในหัวข้อแผนการเรียนรู้ย่อย
        if any(keyword in row_text for keyword in ["หน่วยที่", "บทที่", "หัวข้อ"]) and not any(k in row_text for k in ["ใบความรู้", "ใบงาน", "ใบกิจกรรม", "ข้อสอบ"]):
            unit_name = ""
            hours = "0"
            for cell in row:
                match_hours = re.search(r'\b\d+\b', cell)
                if match_hours and any(h_kw in row_text for h_kw in ["ชม", "ชั่วโมง", "เวลา", "รวม"]):
                    hours = match_hours.group()
            
            name_parts = [cell for cell in row if not re.search(r'\b' + hours + r'\b', cell) and len(cell) > 1]
            unit_name = " ".join(name_parts)
            
            # กรองล้างชื่อหน่วยที่ติดตัวเลขเศษส่วนออกมา
            unit_name = re.sub(r'\b\d+/\d+\b', '', unit_name).strip()
            
            if unit_name and len(unit_name) > 5:
                final_units.append({
                    "หน่วยที่/หัวข้อ": unit_name,
                    "จำนวนชั่วโมง (สะสม)": int(hours) if hours.isdigit() else 0
                })
    return final_units

if uploaded_file is not None:
    if st.button("⚡ ดึงข้อมูลจากไฟล์ Word และจัดตารางตามแบบฟอร์ม"):
        with st.spinner("⏳ ระบบวิชาการกำลังประมวลผลตารางรายวิชา..."):
            try:
                raw_rows = extract_tables_from_word(uploaded_file)
                parsed_list = filter_curriculum_data(raw_rows)
                if parsed_list:
                    st.session_state.curriculum_data = parsed_list
                    st.success("✅ สกัดข้อมูลและประมวลผลจัดกลุ่มตามแบบฟอร์มวิชาการสำเร็จ!")
                else:
                    st.warning("⚠️ ไม่พบตารางโครงสร้างข้อมููลหลักในไฟล์ แต่ท่านสามารถแก้ไขตารางรายงานด้านล่างได้ทันทีครับ")
            except Exception as e:
                st.error(f"ระบบขัดข้องในการแกะตาราง: {str(e)}")

st.write("---")

# ส่วนที่ 2: หน้าจอแก้ไขข้อมูล (Review Table) ปรับแต่งได้ตลอดเวลา
st.write("### 🔍 รายละเอียดโครงสร้างหน่วยการสอนที่สกัดได้")
st.info("💡 ท่านสามารถแก้ไขตัวเลขชั่วโมง พิมพ์ข้อความเพิ่ม หรือกดปุ่ม ➕ Add row ใต้ตารางเพื่อปรับยอดก่อนส่งออกได้")

current_df = pd.DataFrame(st.session_state.curriculum_data)
edited_df = st.data_editor(
    current_df, 
    num_rows="dynamic", 
    use_container_width=True,
    key="academic_data_editor"
)

if st.session_state.academic_data_editor:
    st.session_state.curriculum_data = edited_df.to_dict('records')

# ประมวลผลจำนวนชั่วโมงเรียนรวมสุทธิแบบ Real-time
try:
    total_hours = pd.to_numeric(edited_df["จำนวนชั่วโมง (สะสม)"]).sum()
except:
    total_hours = 0

st.metric(label="⏱️ จำนวนชั่วโมงเรียนรวมสุทธิ (คำนวณยอดปัจจุบัน)", value=f"{total_hours} ชั่วโมง")

st.write("---")

# --- ส่วนที่ 3: ระบบสร้างไฟล์เอกสาร Word ขาออก (.docx) ล็อกหน้าตาตามฟอร์มรายงานจริง ---
def generate_exact_word_report(df, t_name, c_code, c_name, e_level, a_year, t_hours):
    doc = Document()
    
    # พิมพ์หัวข้อเรื่องและข้อมูลรายละเอียดตามแพทเทิร์นต้นฉบับสถาบัน
    doc.add_paragraph("รายงานสรุปข้อมูลการใช้หลักสูตรรายวิชา")
    doc.add_paragraph(f"ชื่อผู้สอน: {t_name}")
    doc.add_paragraph(f"รหัสวิชา: {c_code}   | รายวิชา: {c_name}")
    doc.add_paragraph(f"ระดับชั้น: {e_level} | ภาคเรียน/ปีการศึกษา: {a_year}")
    doc.add_paragraph(f"จำนวนชั่วโมงเรียนรวมสุทธิ: {t_hours} ชั่วโมง")
    doc.add_paragraph("-" * 60)
    doc.add_paragraph("รายละเอียดโครงสร้างหน่วยการสอนที่สกัดได้")
    
    # สร้างโครงสร้างตารางข้อมูล 2 คอลัมน์ เส้นขอบ Grid
    table = doc.add_table(rows=1, cols=2)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'หน่วยที่/หัวข้อ'
    hdr_cells[1].text = 'จำนวนชั่วโมง (สะสม)'
    
    for idx, row in df.iterrows():
        row_cells = table.add_row().cells
        row_cells[0].text = str(row["หน่วยที่/หัวข้อ"])
        row_cells[1].text = f"{str(row['จำนวนชั่วโมง (สะสม)'])} ชม."
        
    doc.add_paragraph("-" * 60)
    doc.add_paragraph("ลงชื่อ..................................................ผู้รายงาน")
    doc.add_paragraph(f"    ( {t_name} )")
    
    # แปลงโครงสร้างลง Memory Stream ป้องกันไฟล์ค้างบน Server
    output_stream = BytesIO()
    doc.save(output_stream)
    output_stream.seek(0)
    return output_stream

# เตรียมสตรีมไฟล์เพื่อปุ่มกดดาวน์โหลดอินเทอร์เน็ต
word_file = generate_exact_word_report(
    edited_df, teacher_name, course_code, course_name, education_level, academic_year, total_hours
)

# ปุ่มดาวน์โหลดไฟล์ Word (.docx) แนบรายงานหลักสูตร
st.download_button(
    label="📥 ดาวน์โหลดรายงานการใช้หลักสูตรตามแบบฟอร์ม (ไฟล์ Word .docx)",
    data=word_file,
    file_name=f"รายงานสรุปการใช้หลักสูตร_{course_code}.docx",
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    use_container_width=True
)
