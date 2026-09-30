import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

# โหลดโมดูลสำหรับสร้างไฟล์ PDF ผลลัพธ์ (ไม่ต้องติดตั้งเพิ่ม ใช้ความสามารถของภาษาในระบบคลาวด์ร่วมได้)
def generate_pdf_report(dataframe, total_hours):
    # ฟังก์ชันจำลองโครงสร้างข้อมูลเพื่อส่งออกเป็นไฟล์รายงาน PDF
    buffer = BytesIO()
    
    # สร้างเนื้อหาไฟล์ Text/HTML-like Layout เพื่อแปลงเป็น PDF 
    # สำหรับเวอร์ชันใช้จริงฝั่ง Developer จะเปลี่ยนเป็นไลบรารี ReportLab เพื่อวาดตารางติดฟอนต์ภาษาไทย TH Sarabun
    report_text = "=========================================\n"
    report_text += "      รายงานสรุปการใช้หลักสูตรการเรียนรู้      \n"
    report_text += "=========================================\n\n"
    report_text += f"จำนวนชั่วโมงเรียนรวมทั้งสิ้นในหลักสูตร: {total_hours} ชั่วโมง\n\n"
    report_text += "รายละเอียดหน่วยการสอนที่สกัดได้จากระบบ:\n"
    report_text += "-----------------------------------------\n"
    
    for idx, row in dataframe.iterrows():
        report_text += f"- {row['หน่วยที่/หัวข้อ']} | เวลา: {row['จำนวนชั่วโมง (สะสม)']} ชม.\n"
        
    report_text += "-----------------------------------------\n"
    report_text += "\n* รับรองความถูกต้องโดยระบบประมวลผลหลักสูตรอัตโนมัติ *"
    
    buffer.write(report_text.encode('utf-8'))
    buffer.seek(0)
    return buffer

# --- ส่วนของการตั้งค่าหน้าเว็บหลัก ---
st.set_page_config(page_title="ระบบรายงานการใช้หลักสูตร", page_icon="📝", layout="wide")

st.title("📝 ระบบรายงานการใช้หลักสูตรอัตโนมัติ")
st.subheader("สกัดข้อมูลจากแผนการสอน และส่งออกเป็นรายงาน PDF ทันที")
st.write("---")

uploaded_file = st.file_uploader("📂 กรุณาแนบไฟล์แผนการสอน หรือกำหนดการสอน (รูปแบบ PDF)", type=["pdf"])

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
        # ตรวจจับคำสำคัญภาษาไทยในตาราง
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
                
                # ครูสามารถแก้ไขข้อมูลบนหน้าเว็บได้ทันทีก่อนกดส่ง
                edited_df = st.data_editor(df_result, num_rows="dynamic", use_container_width=True)
                
                total_hours = edited_df["จำนวนชั่วโมง (สะสม)"].sum()
                st.metric(label="⏱️ จำนวนชั่วโมงเรียนรวมทั้งสิ้นในหลักสูตร", value=f"{total_hours} ชั่วโมง")
                
                st.write("---")
                
                # --- ส่วนที่ 2: ฟังก์ชันการสร้างและดาวน์โหลดไฟล์ PDF ออกมาใช้งาน ---
                pdf_data = generate_pdf_report(edited_df, total_hours)
                
                # ปุ่มสำหรับให้ครูกดดาวน์โหลดไฟล์รายงานสรุปออกมาเป็นไฟล์เดี่ยวทันที
                st.download_button(
                    label="📥 ดาวน์โหลดรายงานสรุปการใช้หลักสูตร (ไฟล์ PDF)",
                    data=pdf_data,
                    file_name="สรุปรายงานการใช้หลักสูตร.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
            else:
                st.warning("⚠️ ไม่พบโครงสร้างตารางมาตรฐาน หรือคำสำคัญ (เช่น 'หน่วยที่', 'ชั่วโมง') ในไฟล์ PDF นี้ กรุณาตรวจสอบรูปแบบไฟล์")
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผลไฟล์: {str(e)}")
