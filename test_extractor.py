import fitz
import re  # <-- 1. เรียกใช้ 're' เครื่องมือจัดการ Text ขั้นสูงของ Python


def clean_thai_text(text):
    # ดาบที่ 1: ล้างบางอักขระขยะ โซนยุโรป, ผีล่องหน, และตัว "" (Unicode Replacement Character \ufffd)
    text = re.sub(r"[\u0080-\u00FF\u200b-\u200f\xad\ufffd]", "", text)

    # ดาบที่ 2: ยุบสระ วรรณยุกต์ และนิคหิตที่เบิ้ลซ้อนกัน (ครอบคลุมตั้งแต่ ะ-ู และ ็-ํ ซึ่งรวม 'ำ' แล้ว)
    text = re.sub(r"([ะ-ู็-ํ])\1+", r"\1", text)

    # ดาบที่ 3: ซ่อมช่องไฟสระนำหน้า (เ สริมสร้าง -> เสริมสร้าง)
    text = re.sub(r"([เแโใไ])\s+([ก-ฮ])", r"\1\2", text)

    return text


def test_read_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    raw_text = doc[1].get_text()

    # เอา Text ดิบๆ ไปวิ่งผ่านเครื่องกรองน้ำ
    fixed_text = clean_thai_text(raw_text)

    print("=== [แบบดิบๆ จาก PDF (สระเบิ้ล)] ===")
    print(raw_text[:500])  # ขอส่องท่อนกลางๆ ที่มีปัญหา

    print("\n=== [แบบผ่านฟังก์ชัน clean_thai_text แล้ว] ===")
    print(fixed_text[:500])


if __name__ == "__main__":
    test_read_pdf("sample_report.pdf")