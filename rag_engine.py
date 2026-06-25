import os
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
import psycopg2
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv
from openai import OpenAI  # <--- [แก้บั๊กที่ 1] ต้อง Import ตรงนี้!

load_dotenv()

# =====================================================================
# 1. GLOBAL CACHE (โหลดของหนักๆ ไว้บน RAM แค่ "ครั้งเดียว")
# =====================================================================
print("📦 [PRO ENGINE] กำลังโหลดสมองกล Vector และ Reranker...")
vector_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")

def tokenize_thai_bigrams(text):
    t = text.replace(" ", "")
    return [t[i : i + 2] for i in range(len(t) - 1)]

print("📦 [PRO ENGINE] กำลังแคชข้อมูล 5,810 ย่อหน้าเพื่อสร้าง BM25 Index...")
try:
    _conn = psycopg2.connect(dbname="rag_db", user="admin", password="securepassword123", host="localhost", port="5432")
    _cur = _conn.cursor()
    _cur.execute("SELECT id, page_number, content FROM document_chunks;")
    ALL_DOCS_CACHE = _cur.fetchall()
    _cur.close()
    _conn.close()
    
    BM25_INDEX = BM25Okapi([tokenize_thai_bigrams(doc[2]) for doc in ALL_DOCS_CACHE])
    print("✅ [PRO ENGINE] เครื่องยนต์ลูกผสม (Hybrid RAG) พร้อมรบ 100%!")
except Exception as e:
    print(f"❌ [CRITICAL ERROR] ดึงข้อมูลทำ Cache ล้มเหลว: {e}")
    exit(1)


# =====================================================================
# 2. THE RUNTIME FUNCTION (ดึงข้อมูล)
# =====================================================================
def get_top_k_results(question: str, k: int = 10):
    conn = None
    try:
        conn = psycopg2.connect(dbname="rag_db", user="admin", password="securepassword123", host="localhost", port="5432")
        cur = conn.cursor()
        register_vector(conn)
        
        query_vec = vector_model.encode(question)
        cur.execute("SELECT id, page_number, content FROM document_chunks ORDER BY embedding <=> %s::vector LIMIT 50;", (query_vec.tolist(),))
        vector_rows = cur.fetchall()
        
        bm25_rows = BM25_INDEX.get_top_n(tokenize_thai_bigrams(question), ALL_DOCS_CACHE, n=50)
        
        candidates = {r[0]: {"text": r[2], "page": r[1]} for r in vector_rows + bm25_rows}
        candidate_list = list(candidates.values())
        
        scores = reranker.predict([(question, c["text"]) for c in candidate_list])
        for idx, sc in enumerate(scores):
            candidate_list[idx]["score"] = float(sc)
            
        return sorted(candidate_list, key=lambda x: x["score"], reverse=True)[:k]

    finally:
        if conn:
            conn.close()


# =====================================================================
# 3. LLM GENERATOR (เชื่อมต่อ Groq)
# =====================================================================
# ตั้งค่า Client ให้อยู่ข้างนอก เพื่อไม่ให้มันต่อเน็ตใหม่ทุกครั้งที่ถาม
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)

def generate_answer_from_llm(question: str, context_results: list) -> str:
    """ [แก้บั๊กที่ 2] โค้ดสั่งงาน LLM ต้องถูกหุ้มอยู่ในฟังก์ชันนี้ """
    
    if not context_results:
        return "ขออภัยครับ ไม่พบข้อมูลในระบบที่สามารถตอบคำถามนี้ได้"

    context_text = "\n\n".join([
        f"[ข้อมูลอ้างอิงจากหน้า {item['page']}]: {item['text']}" 
        for item in context_results
    ])

    system_prompt = """
    คุณคือผู้ช่วยอัจฉริยะขององค์กร หน้าที่ของคุณคือการตอบคำถามโดยอ้างอิงจากข้อมูล [Context] ที่ให้มาเท่านั้น
    - ห้ามใช้ความรู้ภายนอกเด็ดขาด
    - หากข้อมูลใน [Context] ไม่สามารถตอบคำถามได้ ให้ตอบว่า "ไม่พบข้อมูลในเอกสารครับ"
    - อ้างอิง 'หน้าเอกสาร' ในคำตอบของคุณด้วยเสมอ
    """

    user_prompt = f"อ้างอิงข้อมูลนี้:\n{context_text}\n\nคำถาม: {question}"

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant", # ความเร็วแสงของ Groq
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการเชื่อมต่อ LLM: {str(e)}"