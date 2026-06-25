# Enterprise RAG AI - PTTEP Knowledge Assistant

โปรเจกต์นี้เป็นระบบถาม-ตอบข้อมูลจากรายงานประจำปี (PTTEP) ด้วยเทคโนโลยี **RAG (Retrieval-Augmented Generation)** ซึ่งออกแบบมาสำหรับระดับองค์กร (Enterprise) โดยมีระบบรักษาความปลอดภัยและการป้องกัน Prompt Injection (Guardrail)

## 🏗️ โครงสร้างสถาปัตยกรรม (Architecture)

โปรเจกต์นี้ประกอบไปด้วย 2 ส่วนหลัก:
1. **Frontend (UI)**: พัฒนาด้วย `Streamlit` เพื่อเป็นหน้าแชทบอทให้ผู้ใช้งานสามารถสอบถามข้อมูลได้อย่างสะดวก
2. **Backend (API)**: พัฒนาด้วย `FastAPI` เพื่อจัดการการเชื่อมต่อ, การค้นหาข้อมูล (Retrieval) และการสร้างคำตอบ (Generation)

### 🧠 แกนหลักของการประมวลผล (RAG Engine)
*   **Vector Database**: เก็บข้อมูลใน PostgreSQL ร่วมกับ `pgvector`
*   **Hybrid Search**: 
    *   *Semantic Search* (ค้นหาความหมาย) ด้วย `SentenceTransformer` (`paraphrase-multilingual-MiniLM-L12-v2`)
    *   *Keyword Search* (ค้นหาคำตรงตัว) ด้วย `BM25Okapi`
*   **Reranker**: ใช้ `CrossEncoder` (`BAAI/bge-reranker-v2-m3`) เพื่อจัดเรียงลำดับความแม่นยำของข้อมูลก่อนส่งให้ LLM สรุป
*   **LLM Generator**: ใช้โมเดล `llama-3.1-8b-instant` ผ่าน Groq API เพื่อความรวดเร็วในการวิเคราะห์และสร้างคำตอบ

## 🛡️ ระบบรักษาความปลอดภัย (Security Features)

*   **API Authentication**: การเรียกใช้ Backend (FastAPI) จะต้องมีการส่งค่า `x-api-key` ที่ถูกต้องมาใน Headers ทุกครั้ง
*   **LLM Guardrail**: มีระบบตรวจจับและบล็อกคำสั่งที่ไม่ประสงค์ดี (Prompt Injection) เช่น คำว่า "ลืมคำสั่ง", "รหัสผ่าน", "ignore previous" ก่อนที่จะส่งคำถามไปหา LLM

## 📂 โครงสร้างไฟล์ที่สำคัญ (File Structure)

*   `app.py`: Backend API (FastAPI)
*   `chat_ui.py`: Frontend แชทบอท (Streamlit)
*   `rag_engine.py`: โค้ดส่วน RAG (ดึงข้อมูลแบบ Hybrid, Reranking และเชื่อมต่อ Groq LLM)
*   `etl_pipeline.py` / `run_full_etl.py`: สคริปต์สำหรับกระบวนการเตรียมข้อมูล (โหลดไฟล์ PDF, แบ่ง Chunk, สร้าง Embeddings และเซฟลง DB)
*   `docker-compose.yml`: การตั้งค่า Docker สำหรับการจำลองฐานข้อมูล PostgreSQL ขึ้นมาใช้งาน
*   ไฟล์ `test_*.py`: สคริปต์สำหรับทดสอบการทำงานของระบบในส่วนต่างๆ 

## 🚀 วิธีการใช้งานและการรันโปรเจกต์

### 1. เตรียมความพร้อมเบื้องต้น
สร้างไฟล์ `.env` ที่โฟลเดอร์หลัก และกำหนดค่า API Key สำหรับ Groq
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 2. รัน Database และ Backend
เปิด Terminal ใหม่แล้วรันคำสั่งเพื่อให้ FastAPI ทำงาน:
```bash
uvicorn app:app --reload
```
*(หมายเหตุ: ต้องแน่ใจว่าได้สตาร์ท PostgreSQL เอาไว้เรียบร้อยแล้ว ผ่าน Docker Compose หรือติดตั้งเอง)*

### 3. รัน Frontend (หน้าจอแชท)
เปิด Terminal แยกอีกอันแล้วรันคำสั่ง:
```bash
streamlit run chat_ui.py
```
ระบบจะเปิดหน้าต่างเบราว์เซอร์อัตโนมัติ ให้คุณสามารถพิมพ์พูดคุยกับ **PTTEP Knowledge Assistant** ได้ทันที!
