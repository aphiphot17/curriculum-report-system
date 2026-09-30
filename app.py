import streamlit as st
import pdfplumber
import pandas as pd
import re
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image

# --- ตั้งค่าหน้าเว็บหลัก ---
st.set_page_config(page_title="ระบบรายงานการใช้หลักสูตร AI OCR", page_icon="📝", layout="wide")

st.title("📝 ระบบรายงานการใช้หลักสูตรอัตโนมัติ (เวอร์ชัน AI OCR)")
st.subheader("ระบบสแกนข้อความอัจฉริยะ รองรับไฟล์ตารางและไฟล์รูปภาพสแกนภาษาไทย")
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
st.write("### 📂 แนบเอกสารต้นฉบับ")
uploaded_file = st.file_uploader("กรุณาแนบไฟล์แผนการสอน หรือกำหนดการสอน (รูปแบบ PDF)", type=["pdf"])

# ฟังก์ชันที่ 1: ดึงข้อความดิจิทัลทั่วไป
def extract_text_digital(file):
    raw_lines = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                for line in text.split('\n'):
                    if line.strip():
                        raw_lines.append(line.strip())
    return raw_lines

# ฟังก์ชันที่ 2: แปลง PDF เป็นภาพแล้วสแกนตัวหนังสือภาษาไทยด้วย AI OCR (กรณีรูปสแกน 100%)
def extract_text_via_ocr(file_bytes):
    raw_lines = []
    # แปลงไฟล์ PDF เป็นภาพทีละหน้ากระดาษ
    pages = convert_from_bytes(file_bytes)
    for page in pages:
        # สั่งให้ AI รูดอ่านตัวหนังสือภาษาไทยและอังกฤษจากภาพถ่าย
        text = pytesseract.image_to_string(page, lang='tha+eng')
        if text:
            for line in text.split('\n'):
                if line.strip():
                    raw_lines.append(line.strip())
    return raw_lines

# ฟังก์ชันกรองหาหน่วยและชั่วโมงจากข้อความทั้งหมด
def filter_curriculum_data(raw_rows):
    final_units = []
    for line in raw_rows:
        # ตรวจสอบบรรทัดที่มีคีย์เวิร์ดสำคัญของแผนการสอน
        if any(keyword in line for keyword in ["หน่วยที่", "บทที่", "หัวข้อ", "สัปดาห์ที่", "เนื้อหา", "สาระ"]):
            # ค้นหาแพทเทิร์นชั่วโมงเรียน
            match_hours = re.search(r'(\d+)\s*(ชม|ชั่วโมง|คาบ|เวลา)', line)
            hours = match_hours.group(1) if match_hours else "0"
            
            if hours == "0":
                all_nums = re.findall(r'\d+', line)
                if athletics_nums := [n for n in all_nums if int(n) < 40]:
                    hours = athletics_nums[-1]
            
            clean_name = re.sub(r'(\d+)\s*(ชม|ชั่วโมง|คาบ|เวลา)', '', line).strip()
            # ล้างสัญลักษณ์แปลกๆ ที่อาจเกิดจากการเอียงของภาพสแกน
            clean_name = re.sub(r'[|\[\]_\\—-]', '', clean_name).strip()
            
            if clean_name and len(clean_name) > 3:
                final_units.append({
                    "หน่วยที่/หัวข้อ": clean_name,
                    "จำนวนชั่วโมง (สะสม)": int(hours) if hours.isdigit() else 0
                })
    return pd.DataFrame(final_units)

# ทำงานเมื่อครูส่งไฟล์เข้าอินเทอร์เน็ต
if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    
    with st.spinner("⏳ ระบบ AI กำลังวิเคราะห์โครงสร้างและสแกนอ่านรูปภาพข้อความภาษาไทย..."):
        try:
            # ลองอ่านแบบดิจิทัลก่อน
            raw_lines = extract_text_digital(uploaded_file)
            df_result = filter_curriculum_data(raw_lines)
            
            # หากดึงออกมาแล้วว่างเปล่า แสดงว่าเป็นรูปภาพสแกน -> สลับไปใช้โหมด AI OCR ส่องภาพทันที
            if df_result.empty:
                st.info("📸 ตรวจพบไฟล์รูปแบบภาพสแกน ระบบกำลังเปิดระบบ AI OCR ส่องคำภาษาไทยจากรูปภาพ...")
                raw_lines_ocr = extract_text_via_ocr(file_bytes)
                df_result = filter_curriculum_data(raw_lines_ocr)
            
            if not df_result.empty:
                st.success("✅ AI สแกนอ่านรูปภาพและสกัดข้อความสำเร็จ!")
                st.write("### 🔍 ขั้นตอนการตรวจสอบและแก้ไขข้อมูล (Review Mode)")
                
                edited_df = st.data_editor(df_result, num_rows="dynamic", use_container_width=True)
                total_hours = edited_df["จำนวนชั่วโมง (สะสม)"].sum()
                st.metric(label="⏱️ จำนวนชั่วโมงเรียนรวมทั้งสิ้นในหลักสูตร", value=f"{total_hours} ชั่วโมง")
                
                st.write("---")
                
                # โครงสร้างเนื้อหารายงานสำหรับการดาวน์โหลด
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
                report_text += "\nลงชื่อ..................................................ผู้รายงาน\n"
                report_text += f"    ( {teacher_name if teacher_name else '..................................................'} )\n"
                report_text += "================================================--"
                
                pdf_bytes = report_text.encode('utf-8')
                
                st.download_button(
                    label="📥 ดาวน์โหลดรายงานสรุปการใช้หลักสูตร (ไฟล์ PDF)",
                    data=pdf_bytes,
                    file_name=f"รายงานการใช้หลักสูตร_{course_code if course_code else 'วิชา'}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ ไม่สามารถสกัดข้อความได้เนื่องจากภาพต้นฉบับมีความเลือนลางเกินไป หรือไม่พบคำสำคัญในเอกสาร กรุณาพิมพ์เติมข้อมูลด้วยตนเองในตาราง หรือแนบไฟล์ที่ชัดเจนขึ้น")
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในระบบ AI OCR: {str(e)}")
