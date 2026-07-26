"""
Script test nhanh: kiểm tra GEMINI_API_KEY có hoạt động không.
Chạy: python test_gemini.py
"""
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY", "")
if not api_key:
    print("❌ GEMINI_API_KEY chưa được set trong .env!")
    print("   → Thêm dòng GEMINI_API_KEY=AIzaSy... vào file .env")
    exit(1)

print(f"🔑 Key tìm thấy: {api_key[:10]}...")

import google.generativeai as genai

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    response = model.generate_content("Trả lời đúng 1 chữ: OK")
    print(f"✅ Gemini hoạt động! Phản hồi: {response.text.strip()}")
except Exception as e:
    print(f"❌ Gemini lỗi: {e}")
    if "API_KEY_INVALID" in str(e):
        print("   → Key không hợp lệ. Lấy key mới tại: https://aistudio.google.com/app/apikey")
    elif "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower():
        print("   → Key hợp lệ nhưng đã hết quota. Thử lại sau 1 phút.")
