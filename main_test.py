import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
import google.generativeai as genai 

# โหลดค่าจากไฟล์ .env
load_dotenv()

# ดึง Key จากตัวแปรสภาพแวดล้อม (ปลอดภัยกว่า)
api_key = os.getenv("MY_API_KEY") 

genai.configure(api_key=api_key)

# ทดสอบ
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content("สวัสดี แนะนำตัวหน่อย")
print(response.text)