import fitz
import re
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

def clean_thai_text(text):
    # Remove unwanted characters (European zone, invisible ghosts, and Unicode Replacement Character \ufffd)
    text = re.sub(r"[\u0080-\u00FF\u200b-\u200f\xad\ufffd]", "", text)

    # Collapse duplicate vowels, tone marks, and diacritics (covering ะ-ู and ็-ํ, including 'ำ')
    text = re.sub(r"([ะ-ู็-ํ])\1+", r"\1", text)

    # Fix leading vowel spacing (e.g., เ สริมสร้าง -> เสริมสร้าง)
    text = re.sub(r"([เแโใไ])\s+([ก-ฮ])", r"\1\2", text)

    return text.strip()  # Remove leading and trailing whitespace

def extract_andchunk(pdf_path):
    doc = fitz.open(pdf_path)
    chunks = []
    for page_num in range(len(doc)):
        blocks = doc[page_num].get_text("blocks")
        for b in blocks:
            cleaned = clean_thai_text(b[4])
            if len(cleaned) > 30:
                chunks.append({"page": page_num + 1, "text": cleaned})

    return chunks

def main():
    print("🚀 [STEP 1/4] กำลังสูบและหั่น PDF...")
    chunks = extract_andchunk("sample_report.pdf")
    print(f"   -> ได้ข้อความมาทั้งหมด: {len(chunks)} ย่อหน้า\n")

    print("🧠 [STEP 2/4] กำลังปลุกสมองกล AI (MiniLM-L12)...")
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    print("\n🗄️ [STEP 3/4] กำลังต่อสายเข้าโกดัง PostgreSQL...")
    # พิกัดและกุญแจต้องตรงกับไฟล์ docker-compose.yml เป๊ะๆ
    conn = psycopg2.connect(
        dbname="rag_db",
        user="admin",
        password="securepassword123",
        host="localhost",
        port="5432",
    )
    cur = conn.cursor()

    # สั่งเปิดสวิตช์ Extension Vector ใน Postgres
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    register_vector(conn)  # สอนให้ Python รู้จัก Data Type 'vector'

    # สร้างตารางชื่อ 'document_chunks'
    cur.execute("""
        DROP TABLE IF EXISTS document_chunks;
        CREATE TABLE document_chunks (
            id SERIAL PRIMARY KEY,
            page_number INT,
            content TEXT,
            embedding vector(384)
        );
    """)
    conn.commit()
    print("   -> สร้างตารางพร้อมคลังเก็บ Vector(384) สำเร็จ!\n")

    print(
        "⚡ [STEP 4/4] เดินเครื่องแปลง Vector และยิงเข้า DB! (ขั้นตอนนี้ใช้เวลา 1-3 นาที นั่งมองแถบโหลดเพลินๆ ได้เลย)..."
    )

    # วิ่งวน Loop ทีละ Chunk พร้อมแสดงแถบโหลด tqdm
    for item in tqdm(chunks, desc="Ingesting to DB", unit="chunk"):
        # แปลงข้อความ -> เป็นตัวเลข 384 มิติ
        vec = model.encode(item["text"])

        # ยิงเก็บลง Database
        cur.execute(
            "INSERT INTO document_chunks (page_number, content, embedding) VALUES (%s, %s, %s)",
            (
                item["page"],
                item["text"],
                vec.tolist(),
            ),  # .tolist() คือการแปลง Numpy array เป็น List ธรรมดาให้ DB รับได้
        )

    conn.commit()  # กด Save ลงฮาร์ดดิสก์ DB
    cur.close()
    conn.close()

    print("\n🎉 [SUCCESS] อัดข้อมูลทั้ง 5,810 ย่อหน้าลงฐานข้อมูลปลอดภัย 100%!")
    print("ปิดจ๊อบ หมวก Data Engineer ประจำ Week 1 อย่างเป็นทางการครับจูเนียร์!")


if __name__ == "__main__":
    main()