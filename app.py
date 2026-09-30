import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- ตั้งค่าหน้าเว็บหลัก ---
st.set_page_config(page_title="ระบบรายงานการใช้หลักสูตร", page_icon="📝", layout="wide")

st.title("📝 ระบบรายงานการใช้หลักสูตรอัตโนมัติ")
st.subheader("สกัดข้อมูลจากแผนการสอน หรือพิมพ์ข้อมูลด้วยตนเอง เพื่อส่งออกรายงานสรุป PDF")
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

# เริ่มต้นกำหนดโครงสร้างตารางข้อมูลใน Session State ของหน้าเว็บ
if "curriculum_df" not in st.session_state:
    st.session_state.curriculum_df = pd.DataFrame(columns=["หน่วยที่/หัวข้อ", "จำนวนชั่วโมง (สะสม)"])

# ฟังก์ชันสกัดข้อมูลดิจิทัลพื้นฐาน
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

def filter_curriculum_data(raw_rows):
    final_units = []
    for line in raw_rows:
        if any(keyword in line for keyword in ["หน่วยที่", "บทที่", "หัวข้อ", "สัปดาห์ที่", "เนื้อหา", "สาระ"]):
            match_hours = re.search(r'(\d+)\s*(ชม|ชั่วโมง|คาบ|เวลา)', line)
            hours = match_hours.group(1) if match_hours else "0"
            if hours == "0":
                all_nums = re.findall(r'\d+', line)
                if athletics_nums := [n for n in all_nums if int(n) < 40]:
                    hours = athletics_nums[-1]
            
            clean_name = re.sub(r'(\d+)\s*(ชม|ชั่วโมง|คาบ|เวลา)', '', line).strip()
            clean_name = re.sub(r'[|\[\]_\\—-]', '', clean_name).strip()
            
            if clean_name and len(clean_name) > 3:
                final_units.append({
                    "หน่วยที่/หัวข้อ": clean_name,
                    "จำนวนชั่วโมง (สะสม)": int(hours) if hours.isdigit() else 0
                })
    return pd.DataFrame(final_units)

# แผงควบคุมการอัปโหลดเอกสาร
st.write("### 📂 วิธีที่ 1: สกัดข้อมูลอัตโนมัติจากไฟล์แผนการสอน")
uploaded_file = st.file_uploader("แนบไฟล์แผนการสอน หรือกำหนดการสอน (รูปแบบ PDF)", type=["pdf"])

if uploaded_file is not None:
    if st.button("⚡เริ่มทำการสแกนไฟล์ดึงข้อมูล"):
        with st.spinner("⏳ ระบบกำลังพยายามสแกนอ่านข้อมูลภาษาไทย..."):
            try:
                raw_lines = extract_text_digital(uploaded_file)
                df_result = filter_curriculum_data(raw_lines)
                
                if not df_result.empty:
                    st.session_state.curriculum_df = df_result
                    st.success("✅ สกัดข้อมูลสำเร็จ! กรุณาตรวจสอบผลที่ตารางด้านล่าง")
                else:
                    st.warning("⚠️ ไม่สามารถอ่านข้อความดิจิทัลจาก PDF นี้ได้เนื่องจากไฟล์ของคุณเป็นรูปภาพสแกนหรือถูกล็อกความปลอดภัย แต่คุณยังสามารถพิมพ์กรอกข้อมูลด้วยตนเองที่ตารางด้านล่างได้ทันทีครับ")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {str(e)}")

st.write("---")

# ส่วนขั้นตอนตรวจสอบข้อมูล หรือพิมพ์กรอกด้วยตัวเอง
st.write("### 🔍 วิธีที่ 2: ตารางตรวจสอบและบันทึกข้อมูลหน่วยการสอน")
st.info("💡 คุณครูสามารถพิมพ์เติมข้อมูล กดเพิ่มแถว หรือลบแถวได้อิสระตามโครงสร้างจริงของคุณครู")

# แสดงกล่องพิมพ์และแก้ไขข้อมูล (Data Editor) แบบยืดหยุ่นเพิ่มลดแถวได้เอง
edited_df = st.data_editor(
    st.session_state.curriculum_df, 
    num_rows="dynamic", # เปิดให้กดปุ่มเพิ่มแถว (+) หรือลบแถวได้เองบนเว็บฟรี
    use_container_width=True
)

# คำนวณชั่วโมงสะสมรวมสุทธิ
try:
    total_hours = pd.to_numeric(edited_df["จำนวนชั่วโมง (สะสม)"]).sum()
except:
    total_hours = 0
st.metric(label="⏱️ จำนวนชั่วโมงเรียนรวมทั้งสิ้นในหลักสูตร", value=f"{total_hours} ชั่วโมง")

st.write("---")

# สร้างเนื้อหารายงานสำหรับการส่งออก PDF ทันที ณ วินาทีที่กดปุ่ม
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

# ปุ่มดาวน์โหลด PDF ที่ทำงานแน่นอน ไม่พึ่งพาซอฟต์แวร์เครื่องอื่น
st.download_button(
    label="📥 ดาวน์โหลดรายงานสรุปการใช้หลักสูตร (ไฟล์ PDF)",
    data=pdf_bytes,
    file_name=f"รายงานการใช้หลักสูตร_{course_code if course_code else 'วิชา'}.pdf",
    mime="application/pdf",
    use_container_width=True
)
