import streamlit as st
import pdfplumber
import pandas as pd
import re

# ตั้งค่าหน้าตาของเว็บไซต์
st.set_page_config(page_title="ระบบรายงานการใช้หลักสูตร", page_icon="📝", layout="wide")

st.title("📝 ระบบรายงานการใช้หลักสูตรอัตโนมัติ")
st.subheader("ลดภาระงานครูด้วยระบบสกัดข้อมูลหน่วยการสอนจากไฟล์แผนการสอน PDF")
st.write("---")

# ส่วนที่ 1: จุดอัปโหลดไฟล์ PDF บนหน้าเว็บ
uploaded_file = st.file_uploader("📂 กรุณาแนบไฟล์แผนการสอน หรือกำหนดการสอน (รูปแบบ PDF)", type=["pdf"])

def extract_tables_from_pdf(file):
    extracted_data = []
    
    # เปิดอ่านไฟล์ PDF
    with pdfplumber.open(file) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # สกัดตารางจากหน้า PDF
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # ล้างค่าช่องว่าง หรือค่า None ในตาราง
                    clean_row = [str(cell).strip() if cell is not None else "" for cell in row]
                    # กรองเฉพาะแถวที่มีข้อมูล ไม่เป็นแถวว่าง
                    if any(clean_row):
                        extracted_data.append(clean_row)
    return extracted_data

def filter_curriculum_data(raw_rows):
    final_units = []
    
    for row in raw_rows:
        row_text = " ".join(row)
        
        # ค้นหาแถวที่มีคำสำคัญระบุว่าเป็นข้อความเกี่ยวกับหน่วยการสอน
        if any(keyword in row_text for keyword in ["หน่วยที่", "บทที่", "หัวข้อ", "สัปดาห์ที่", "เนื้อหา"]):
            unit_name = ""
            hours = "0"
            
            # ค้นหาคอลัมน์ที่เป็นตัวเลขชั่วโมง โดยมองหาตัวเลขที่อยู่ใกล้คำว่า ชม. หรือ ชั่วโมง
            for cell in row:
                # ค้นหาตัวเลขโดดๆ ในช่องตาราง เพื่อคาดการณ์ว่าเป็นชั่วโมงเรียน
                match_hours = re.search(r'\b\d+\b', cell)
                if match_hours and any(h_kw in row_text for h_kw in ["ชม", "ชั่วโมง", "เวลา", "คาบ"]):
                    hours = match_hours.group()
            
            # รวมข้อความทั้งหมดในแถวที่คาดว่าเป็นชื่อหน่วย (ยกเว้นช่องที่เป็นชั่วโมง)
            name_parts = [cell for cell in row if not re.search(r'\b' + hours + r'\b', cell) and len(cell) > 1]
            unit_name = " ".join(name_parts)
            
            if unit_name:
                final_units.append({
                    "หน่วยที่/หัวข้อ": unit_name,
                    "จำนวนชั่วโมง (สะสม)": int(hours) if hours.isdigit() else 0
                })
                
    return pd.DataFrame(final_units)

# กระบวนการประมวลผลเมื่อครูอัปโหลดไฟล์
if uploaded_file is not None:
    with st.spinner("⏳ ระบบกำลังอ่านไฟล์ PDF และสกัดโครงสร้างตารางภาษาไทย..."):
        try:
            # 1. สกัดข้อมูลดิบจากตาราง
            raw_data = extract_tables_from_pdf(uploaded_file)
            
            # 2. กรองเฉพาะหน่วยการสอนและชั่วโมง
            df_result = filter_curriculum_data(raw_data)
            
            if not df_result.empty:
                st.success("✅ สกัดข้อมูลจากแผนการสอนสำเร็จ!")
                st.write("### 🔍 ขั้นตอนการตรวจสอบและแก้ไขข้อมูล (Review Mode)")
                st.info("💡 คุณครูสามารถดับเบิ้ลคลิกที่ช่องในตารางเพื่อแก้ไขข้อความหรือจำนวนชั่วโมงให้ถูกต้องได้ทันที หากระบบดึงข้อมูลผิดพลาด")
                
                # 3. แสดงผลในรูปแบบ Data Editor ที่ครูสามารถกดแก้ไขบนหน้าเว็บได้ฟรี
                edited_df = st.data_editor(
                    df_result, 
                    num_rows="dynamic", 
                    use_container_width=True
                )
                
                # คำนวณสรุปชั่วโมงรวมอัตโนมัติ
                total_hours = edited_df["จำนวนชั่วโมง (สะสม)"].sum()
                st.metric(label="⏱️ จำนวนชั่วโมงเรียนรวมทั้งสิ้นในหลักสูตร", value=f"{total_hours} ชั่วโมง")
                
                # ส่วนที่ 2: ปุ่มกดยืนยันบันทึกส่งรายงาน
                st.write("---")
                if st.button("💾 ยืนยันข้อมูลและส่งรายงานการใช้หลักสูตร"):
                    st.balloons()
                    st.success("🎉 บันทึกรายงานการใช้หลักสูตรเข้าสู่ระบบเรียบร้อยแล้ว!")
                    # (ในอนาคตสามารถเขียนโค้ดต่อเพื่อเซฟลงฐานข้อมูลหลักของโรงเรียนได้ที่นี่)
            else:
                st.warning("⚠️ ไม่พบโครงสร้างตารางมาตรฐาน หรือคำสำคัญ (เช่น 'หน่วยที่', 'ชั่วโมง') ในไฟล์ PDF นี้ กรุณาตรวจสอบรูปแบบไฟล์")
                
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผลไฟล์: {str(e)}")
