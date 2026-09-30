import streamlit as st
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import pandas as pd
import re
from io import BytesIO

# --- ตั้งค่าหน้าเว็บหลัก ---
st.set_page_config(page_title="ระบบรายงานการใช้หลักสูตรวิชาการ", page_icon="📝", layout="wide")

st.title("📝 ระบบรายงานการใช้หลักสูตรอัตโนมัติ")
st.subheader("จัดรูปแบบโครงสร้างตารางและเอกสาร Word (.docx) ตามแบบฟอร์มสถาบันการศึกษา")
st.write("---")

# ฟอร์มข้อมูลคุณครูและรายวิชา
st.write("### 👤 ข้อมูลผู้สอนและรายวิชา")
col1, col2 = st.columns(2)
with col1:
    teacher_name = st.text_input("ชื่อผู้สอน", value="นายอภิภช เจริญกิจ")
    course_code = st.text_input("รหัสวิชา", value="30104-2026")
    course_name = st.text_input("รายวิชา", value="การติดตตั้งไฟฟ้า2")
with col2:
    education_level = st.text_input("ระดับชั้น", value="ปวส.")
    academic_year = st.text_input("ภาคเรียน/ปีการศึกษา", value="1/2569")

st.write("---")

# โครงสร้างตารางข้อมูลมาตรฐาน
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

st.write("### 🔍 ตารางจัดทำข้อมูลหน่วยการสอน")
current_df = pd.DataFrame(st.session_state.curriculum_data)
edited_df = st.data_editor(current_df, num_rows="dynamic", use_container_width=True, key="strict_editor")

if st.session_state.strict_editor:
    st.session_state.curriculum_data = edited_df.to_dict('records')

try:
    total_hours = pd.to_numeric(edited_df["จำนวนชั่วโมง (สะสม)"]).sum()
except:
    total_hours = 0
st.metric(label="⏱️ จำนวนชั่วโมงเรียนรวมสุทธิ", value=f"{total_hours} ชั่วโมง")

st.write("---")

# --- ฟังก์ชันประกอบโครงสร้างให้ตรงตามแบบฟอร์มจริง (Exact Template Builder) ---
def generate_perfect_form(df, t_name, c_code, c_name, e_level, a_year, t_hours):
    doc = Document()
    
    # 1. หัวเรื่องใหญ่ จัดกึ่งกลาง ตัวหนา
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("รายงานสรุปข้อมูลการใช้หลักสูตรรายวิชา")
    run_title.bold = True
    run_title.font.size = Pt(16)
    run_title.font.name = 'TH Sarabun PSK'
    
    # 2. ข้อมูลรายละเอียดครูและวิชา
    p_info = doc.add_paragraph()
    p_info.alignment = WD_ALIGN_PARAGRAPH.LEFT
    info_text = f"ชื่อผู้สอน: {t_name}\n"
    info_text += f"รหัสวิชา: {c_code}   | รายวิชา: {c_name}\n"
    info_text += f"ระดับชั้น: {e_level} | ภาคเรียน/ปีการศึกษา: {a_year}\n"
    info_text += f"จำนวนชั่วโมงเรียนรวมสุทธิ: {t_hours} ชั่วโมง"
    run_info = p_info.add_run(info_text)
    run_info.font.size = Pt(14)
    run_info.font.name = 'TH Sarabun PSK'
    
    # เส้นคั่นขีดขวางยาว 60 ตัวอักษรตามแบบฟอร์ม
    p_line1 = doc.add_paragraph()
    p_line1.add_run("-" * 60).font.name = 'TH Sarabun PSK'
    
    # หัวข้อตาราง
    p_sub = doc.add_paragraph()
    p_sub.add_run("รายละเอียดโครงสร้างหน่วยการสอนที่สกัดได้").bold = True
    p_sub.runs[0].font.name = 'TH Sarabun PSK'
    p_sub.runs[0].font.size = Pt(14)
    
    # 3. ตารางโครงสร้างแบบฟอร์มจริง (มีเส้นขอบชัดเจนตามแพทเทิร์นต้นฉบับ)
    table = doc.add_table(rows=1, cols=2)
    table.style = 'Table Grid'
    
    # กำหนดหัวตาราง
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'หน่วยที่/หัวข้อ'
    hdr_cells[1].text = 'จำนวนชั่วโมง (สะสม)'
    
    # ตั้งค่าตัวหนาให้หัวตาราง
    for cell in hdr_cells:
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.bold = True
                run.font.name = 'TH Sarabun PSK'
                run.font.size = Pt(14)

    # ใส่ข้อมูลแต่ละแถว
    for idx, row in df.iterrows():
        row_cells = table.add_row().cells
        row_cells[0].text = str(row["หน่วยที่/หัวข้อ"])
        row_cells[1].text = f"{str(row['จำนวนชั่วโมง (สะสม)'])} ชม."
        
        # จัดตำแหน่งข้อความในช่องตาราง (ชั่วโมงอยู่ตรงกลาง ข้อความอยู่ชิดซ้าย)
        row_cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
        row_cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # ล็อกฟอนต์ภาษาไทย
        for cell in row_cells:
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.name = 'TH Sarabun PSK'
                    run.font.size = Pt(14)
                    
    # เส้นคั่นท้ายตาราง
    p_line2 = doc.add_paragraph()
    p_line2.add_run("\n" + "-" * 60).font.name = 'TH Sarabun PSK'
    
    # 4. ส่วนท้ายลงชื่อรายงาน (ย่อหน้าชิดขวาเพื่อให้ตำแหน่งตรงตามฟอร์มจริง)
    p_sign = doc.add_paragraph()
    p_sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    sign_text = "ลงชื่อ..................................................ผู้รายงาน  \n"
    sign_text += f"    ( {t_name} )  "
    run_sign = p_sign.add_run(sign_text)
    run_sign.font.name = 'TH Sarabun PSK'
    run_sign.font.size = Pt(14)
    
    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output

# จัดเตรียมไฟล์สำหรับปุ่มดาวน์โหลดบนอินเทอร์เน็ต
final_word_file = generate_perfect_form(
    edited_df, teacher_name, course_code, course_name, education_level, academic_year, total_hours
)

st.download_button(
    label="📥 ดาวน์โหลดรายงานการใช้หลักสูตรตามแบบฟอร์มจริง (ไฟล์ Word .docx)",
    data=final_word_file,
    file_name=f"รายงานสรุปการใช้หลักสูตร_{course_code}.docx",
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    use_container_width=True
)
