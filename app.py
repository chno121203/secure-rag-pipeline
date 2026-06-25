from fastapi import FastAPI, Header, HTTPException, Depends
from rag_engine import get_top_k_results, generate_answer_from_llm

app = FastAPI()

# 🔑 ตั้งรหัสผ่าน API ของเราเอง (ป้องกันคนนอกแอบใช้)
SECRET_API_KEY = "super-secret-rag-2026"

# --- 1. Security Gate: รปภ. ตรวจบัตรเข้าตึก ---
async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != SECRET_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: รหัสผ่าน API ไม่ถูกต้อง หรือไม่ได้แนบตั๋วมา!")
    return x_api_key

# --- 2. LLM Guardrail: ระบบตรวจจับ Prompt Injection ---
def check_malicious_prompt(question: str) -> bool:
    # คำต้องห้ามที่แฮกเกอร์ชอบใช้หลอก AI
    bad_words = ["ลืมคำสั่ง", "รหัสผ่าน", "ignore previous", "system prompt", "พาสเวิร์ด", "ความลับ"]
    for word in bad_words:
        if word in question.lower():
            return True
    return False

# เพิ่ม Depends(verify_api_key) บังคับว่าต้องมีกุญแจถึงจะเรียกใช้ฟังก์ชันนี้ได้
@app.get("/ask")
async def ask_ai(question: str, x_api_key: str = Depends(verify_api_key)):
    print(f"\n🤖 User ถามว่า: {question}")
    
    if check_malicious_prompt(question):
        return {"question": question, "answer": "🚨 [Security Alert] Request Blocked..."}
    
    # 1. ดึงข้อมูล
    results = get_top_k_results(question)
    
    # 🔍 [เพิ่มบรรทัดนี้ลงไป!!] เพื่อดูว่ามันหาหน้า 36 เจอไหม?
    print(f"📦 [DEBUG] ข้อมูลที่ Retriever หามาได้: {results}") 
    
    # 2. ส่งให้ LLM
    answer = generate_answer_from_llm(question, results)
    
    return {"question": question, "answer": answer}