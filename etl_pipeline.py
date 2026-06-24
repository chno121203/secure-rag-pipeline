import fitz
import re

def clean_thai_text(text):
    # Remove unwanted characters (European zone, invisible ghosts, and Unicode Replacement Character \ufffd)
    text = re.sub(r"[\u0080-\u00FF\u200b-\u200f\xad\ufffd]", "", text)

    # Collapse duplicate vowels, tone marks, and diacritics (covering ะ-ู and ็-ํ, including 'ำ')
    text = re.sub(r"([ะ-ู็-ํ])\1+", r"\1", text)

    # Fix leading vowel spacing (e.g., เ สริมสร้าง -> เสริมสร้าง)
    text = re.sub(r"([เแโใไ])\s+([ก-ฮ])", r"\1\2", text)

    return text.strip()  # Remove leading and trailing whitespace

def extract_andchunk(pdf_path):
    print(f"เริ่มทำการซอยข้อมูลจากไฟล์ PDF: {pdf_path}...")
    doc = fitz.open(pdf_path)
    chunks = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        
        blocks = page.get_text("blocks")  # Get text blocks from the page

        for b in blocks:
            raw_paragraph = b[4]  # The text content of the block
            cleaned_paragraph = clean_thai_text(raw_paragraph)

            if len (cleaned_paragraph) > 30:  # Only add non-empty paragraphs
                chunks.append(
                    {"page_number": page_num + 1, 
                     "text": cleaned_paragraph,
                     "length": len(cleaned_paragraph)
                    }
                )

    return chunks

if __name__ == "__main__":
    all_chunks = extract_andchunk("sample_report.pdf")

    print(f"Total chunks extracted: {len(all_chunks)} ย่อหน้า (chunks) จากไฟล์ PDF")

    print("\n📊 ลองสุ่มดูผลงานชิ้นที่ 15:")
    print(f"อยู่หน้า: {all_chunks[14]['page_number']}")
    print(f"ความยาว: {all_chunks[14]['length']} ตัวอักษร")
    print(f"เนื้อหา: {all_chunks[14]['text'][:250]}...")