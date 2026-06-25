import streamlit as st
import requests

# 🎨 ตั้งค่าหน้าจอ
st.set_page_config(page_title="Enterprise RAG AI", page_icon="🤖")
st.title("🤖 PTTEP Knowledge Assistant")
st.caption("แชทบอทถามตอบข้อมูลรายงานประจำปี (มีระบบ RAG + Guardrail)")

# 🔑 ตั้งค่าการเชื่อมต่อกับ Backend ของเรา
API_URL = "http://127.0.0.1:8000/ask"
API_KEY = "super-secret-rag-2026"

# 🧠 สร้างความทรงจำให้แชท (เพื่อแสดงประวัติการคุย)
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "สวัสดีครับ! ผมคือ AI อ่านรายงาน ปตท.สผ. มีอะไรให้ผมช่วยค้นหาไหมครับ?"}]

# แสดงประวัติการแชทบนหน้าจอ
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 💬 รอรับข้อความจากผู้ใช้
if prompt := st.chat_input("พิมพ์คำถามของคุณที่นี่... (เช่น แหล่งน้ำมันสิริกิติ์เปิดเมื่อไหร่?)"):
    
    # 1. แสดงคำถามของผู้ใช้บนจอ
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. ส่งคำถามไปให้ Backend (FastAPI) ของเราทำงาน
    with st.chat_message("assistant"):
        with st.spinner("กำลังค้นหาข้อมูลในเอกสาร 5,810 ย่อหน้า..."):
            try:
                headers = {"x-api-key": API_KEY}
                params = {"question": prompt} # ใช้ params เพื่อแก้ปัญหาภาษาไทยใน URL
                
                # ยิงไปที่ Backend
                response = requests.get(API_URL, headers=headers, params=params)
                
                if response.status_code == 200:
                    answer = response.json().get("answer", "เกิดข้อผิดพลาดในการอ่านข้อมูล")
                else:
                    answer = f"🚨 Backend Error: {response.status_code} - คุณอาจจะลืมเปิด FastAPI หรือกุญแจผิด!"
            except requests.exceptions.ConnectionError:
                answer = "🚨 เชื่อมต่อ Backend ไม่ได้! คุณเปิดรัน `uvicorn app:app` ไว้หรือยัง?"

            st.markdown(answer)
            # บันทึกคำตอบลงประวัติ
            st.session_state.messages.append({"role": "assistant", "content": answer})