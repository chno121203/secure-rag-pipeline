import psycopg2
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder

# ==========================================
# ท่าลับของซีเนียร์: Thai Character Bigram Tokenizer
# ภาษาไทยไม่มีเว้นวรรคระหว่างคำ ถ้าใช้ .split() แบบฝรั่ง BM25 จะพังพินาศ
# เราจึงสับข้อความทีละ 2 ตัวอักษรเหลื่อมกัน (เช่น "เปิดเมื่อ" -> ['เป', 'ปิ', 'ิด', 'ดเ', 'เม', 'มื', 'ื่อ'])
# วิธีนี้ทำให้ BM25 กลายเป็นเอนจินค้นหาคำไทยที่โคตรแม่นโดยไม่ต้องพึ่ง Dictionary!
# ==========================================


def tokenize_thai_bigrams(text):
    t = text.replace(" ", "")
    return [t[i : i + 2] for i in range(len(t) - 1)]


def main():
    print("🧠 [STEP 1/4] กำลังโหลด AI สมองคู่ (Vector + Re-ranker)...")
    vector_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    # โหลดตะแกรงร่อนทอง (ครั้งแรกจะโหลดไฟล์ 2.2GB นานนิดนึงนะจูเนียร์)
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")

    question = "แหล่งน้ำมันดิบบนบกที่ใหญ่ที่สุดของไทยเปิดเมื่อวันที่เท่าไร?"
    print(f"\n👤 คำถาม: '{question}'")
    query_vec = vector_model.encode(question)

    print("\n🗄️ [STEP 2/4] เปิดประตูโกดัง ดึงแห 2 วง (Vector + BM25)...")
    conn = psycopg2.connect(
        dbname="rag_db",
        user="admin",
        password="securepassword123",
        host="localhost",
        port="5432",
    )
    cur = conn.cursor()

    # --- แหวงที่ 1: Vector Search (เอา Top 10) ---
    cur.execute(
        """
        SELECT id, page_number, content 
        FROM document_chunks 
        ORDER BY embedding <=> %s::vector ASC 
        LIMIT 10;
    """,
        (query_vec.tolist(),),
    )
    vector_rows = cur.fetchall()

    # --- แหวงที่ 2: BM25 Lexical Search (เอา Top 10) ---
    # ดึง Text ทั้งหมดใน DB ออกมาให้ BM25 วิ่งตรวจ
    cur.execute("SELECT id, page_number, content FROM document_chunks;")
    all_docs = cur.fetchall()

    # สับ corpus ทั้งหมดเป็น Bigram
    tokenized_corpus = [tokenize_thai_bigrams(doc[2]) for doc in all_docs]
    bm25 = BM25Okapi(tokenized_corpus)

    tokenized_query = tokenize_thai_bigrams(question)
    bm25_rows = bm25.get_top_n(tokenized_query, all_docs, n=10)

    # --- จับแห 2 วงเทรวมกันแล้วคัดตัวซ้ำออก (Union & Deduplicate) ---
    unique_candidates = {}
    for r in vector_rows:
        unique_candidates[r[0]] = {
            "page": r[1],
            "text": r[2],
            "caught_by": "Vector",
        }
    for r in bm25_rows:
        if r[0] in unique_candidates:
            unique_candidates[r[0]]["caught_by"] = "Both (Vector + BM25)"
        else:
            unique_candidates[r[0]] = {
                "page": r[1],
                "text": r[2],
                "caught_by": "BM25",
            }

    candidate_list = list(unique_candidates.values())
    print(
        f"   -> กวาดแหรวมกันได้ผู้เข้าชิงที่ไม่ซ้ำกันทั้งหมด: {len(candidate_list)} ย่อหน้า"
    )

    print(
        "\n⚖️ [STEP 3/4] โยนเข้าตะแกรงร่อนทอง (Re-ranker) เพื่อให้คะแนนตรรกะใหม่..."
    )
    # สร้างข้อสอบคู่ [(คำถาม, ย่อหน้า1), (คำถาม, ย่อหน้า2)...]
    pairs = [(question, c["text"]) for c in candidate_list]
    scores = reranker.predict(pairs)

    for idx, sc in enumerate(scores):
        candidate_list[idx]["rerank_score"] = float(sc)

    # เรียงลำดับจากคะแนน Re-ranker มากไปน้อย
    final_top3 = sorted(
        candidate_list, key=lambda x: x["rerank_score"], reverse=True
    )[:3]

    print("\n🏆 [STEP 4/4] THE MOMENT OF TRUTH! ผลการร่อนทอง Top 3 ที่แท้จริง:")
    for idx, item in enumerate(final_top3, 1):
        print(
            f"\nอันดับ {idx} [Rerank Score: {item['rerank_score']:.2f} | หน้า {item['page']} | ติดแหมาจาก: {item['caught_by']}]:"
        )
        print(f'"{item["text"]}"')

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()