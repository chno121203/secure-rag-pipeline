import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

print("🧠 [STEP 1/3] กำลังโหลดสมองกล AI (MiniLM-L12)...")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# คำถามทดสอบ (เราจงใจถามเจาะประเด็นเรื่อง 'วันที่เปิดแหล่งน้ำมัน' ที่เราเคยส่องเห็นใน PDF!)
question = "แหล่งน้ำมันดิบบนบกที่ใหญ่ที่สุดของไทยเปิดเมื่อวันที่เท่าไร?"
print(f"\n👤 คำถามจาก User: '{question}'")

print("   -> กำลังแปลงคำถามเป็นพิกัด Vector 384 มิติ...")
query_vec = model.encode(question)

print("\n🗄️ [STEP 2/3] เปิดประตูโกดัง Postgres เพื่อค้นหา 3 ย่อหน้าลึกลับ...")
# พิกัดและรหัสผ่านต้องตรงกับตอนโหลดเป๊ะๆ
conn = psycopg2.connect(
    dbname="rag_db",
    user="admin",
    password="securepassword123",
    host="localhost",
    port="5432",
)
cur = conn.cursor()
register_vector(conn)  # สอน psycopg2 ให้รู้จัก Data Type 'vector'

# --- THE MAGIC SQL ---
# เราใช้ Operator '<=>' ของ pgvector ซึ่งก็คือการวัดระยะ Cosine Distance
# (ยิ่งค่าน้อย = ยิ่งใกล้เคียงความหมายคำถามที่สุด เราเลยใช้ ORDER BY ... ASC)
# และเราเอา (1 - distance) เพื่อแปลงกลับมาเป็นคะแนนความคล้ายคลึง (Similarity Score 0.0 ถึง 1.0)
cur.execute(
    """
    SELECT page_number, content, (1 - (embedding <=> %s::vector)) as similarity_score
    FROM document_chunks
    ORDER BY embedding <=> %s::vector ASC
    LIMIT 3;
""",
    (
        query_vec.tolist(),
        query_vec.tolist(),
    ),  # โยน Vector คำถามลงไปแทนที่ %s ทั้งสองจุด
)

results = cur.fetchall()

print("\n🎯 [STEP 3/3] คาบกลับมาได้สำเร็จ! นี่คือ Top 3 ย่อหน้า (Chunks):")
for idx, row in enumerate(results, 1):
    page = row[0]
    text = row[1]
    score = row[2]
    print(
        f"\nอันดับที่ {idx} [ความแม่นยำ: {score*100:.2f}% | มาจากหน้า {page}]:"
    )
    print(f'"{text}"')

cur.close()
conn.close()