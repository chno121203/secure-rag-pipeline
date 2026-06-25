import os
from dotenv import load_dotenv
from openai import OpenAI
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi

load_dotenv()

# ดึง Key จากไฟล์ .env (ใช้ MY_API_KEY ตามที่คุณตั้งไว้)
api_key = os.getenv("MY_API_KEY")
if not api_key:
    raise ValueError("ไม่พบ MY_API_KEY ในไฟล์ .env กรุณาตรวจสอบให้แน่ใจว่าได้ใส่คีย์ไว้แล้ว")

# สร้าง Client ของ OpenAI แต่ชี้ไปที่ OpenRouter
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

# โหลดโมเดลไว้ข้างนอกฟังก์ชัน เพื่อไม่ให้มันโหลดซ้ำทุกครั้งที่ถาม (ประหยัด RAM)
vector_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")

def tokenize_thai_bigrams(text):
    t = text.replace(" ", "")
    return [t[i : i + 2] for i in range(len(t) - 1)]

def get_answer(question):
    conn = psycopg2.connect(dbname="rag_db", user="admin", password="securepassword123", host="localhost", port="5432")
    cur = conn.cursor()
    register_vector(conn)
    
    # 1. RETRIEVE: ดึงข้อมูลจาก DB
    cur.execute("SELECT id, page_number, content, embedding FROM document_chunks;")
    all_docs = cur.fetchall()
    
    # Vector Search
    query_vec = vector_model.encode(question)
    cur.execute("SELECT id, page_number, content FROM document_chunks ORDER BY embedding <=> %s::vector LIMIT 10;", (query_vec.tolist(),))
    vector_rows = cur.fetchall()
    
    # BM25 Search
    tokenized_corpus = [tokenize_thai_bigrams(doc[2]) for doc in all_docs]
    bm25 = BM25Okapi(tokenized_corpus)
    bm25_rows = bm25.get_top_n(tokenize_thai_bigrams(question), all_docs, n=10)
    
    # Union & Re-ranker
    candidates = {r[0]: {"text": r[2], "page": r[1]} for r in vector_rows + bm25_rows}
    candidate_list = list(candidates.values())
    
    # ให้ Re-ranker จัดอันดับใหม่
    scores = reranker.predict([(question, c["text"]) for c in candidate_list])
    for idx, sc in enumerate(scores):
        candidate_list[idx]["score"] = float(sc)
        
    final_top3 = sorted(candidate_list, key=lambda x: x["score"], reverse=True)[:3]
    
    # 2. GENERATE: สั่ง AI ให้ตอบ
    context_text = "\n\n".join([f"[หน้า {item['page']}]: {item['text']}" for item in final_top3])
    
    prompt = f"""จงตอบคำถามโดยใช้ข้อมูลจาก [Context] ที่ให้มาเท่านั้น! 
    ห้ามใช้ความรู้ภายนอกเด็ดขาด ถ้าข้อมูลไม่เพียงพอให้ตอบว่า "ไม่ทราบข้อมูลครับ"
    
    [Context]:
    {context_text}
    
    [คำถาม]:
    {question}"""
    
    # เรียกใช้งาน OpenRouter (ตอนนี้เปลี่ยนเป็น openrouter/free เพื่อให้ระบบเลือกโมเดลฟรีที่ไม่ติด Rate Limit ให้อัตโนมัติ)
    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[{"role": "user", "content": prompt}]
    )
    
    cur.close()
    conn.close()
    return response.choices[0].message.content

# ทดสอบรัน
if __name__ == "__main__":
    while True: # สั่งให้มันวนถามซ้ำๆ เหมือนแชทบอท
        user_question = input("\n👤 มึงอยากถามอะไร (พิมพ์ 'exit' เพื่อปิด): ")
        if user_question.lower() == 'exit':
            break
        
        print("\n🤖 AI กำลังค้นหาคำตอบ...")
        answer = get_answer(user_question)
        print(f"\n🤖 คำตอบ: {answer}")