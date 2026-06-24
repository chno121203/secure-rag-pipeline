from sentence_transformers import (
    SentenceTransformer,
)  # เรียกใช้เครื่องมือแปลง Vector

print("⏳ กำลังโหลด AI Model ลงหน่วยความจำ (ครั้งแรกจะใช้เวลาโหลดนิดนึงนะ)...")

# เราจะใช้โมเดลชื่อ 'paraphrase-multilingual-MiniLM-L12-v2'
# ซึ่งรองรับภาษาไทย โหลดเร็ว (ขนาดแค่ ~470MB) และเบาพอที่จะรันบน CPU สบายๆ
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# ลองเอาข้อความตัวอย่างจาก Chunk ที่ 15 ของคุณมาเทสต์
sample_text = "ด้านการกำกับดูแลกิจการ"

print(f"🧠 กำลังแปลงข้อความ: '{sample_text}' -> เป็น Vector...")
vector = model.encode(sample_text)

print("\n✅ แปลงสำเร็จ! ลองส่องดูหน้าตาของ Vector ที่ AI มองเห็น:")
print(vector[:5])  # ขอส่องดูตัวเลข 5 ตัวแรกจากแถวลำดับทั้งหมด

print(f"\n📏 ขนาดมิติ (Dimensions) ของ Vector นี้คือ: {len(vector)} มิติ")