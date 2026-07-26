"""
Cấu hình bot — đọc từ biến môi trường (file .env khi chạy local,
hoặc "Environment Variables" trên Railway/Render khi deploy cloud).
"""
import os
from dotenv import load_dotenv

load_dotenv()  # đọc file .env nếu có (khi chạy local)

# --- Bắt buộc ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Nơi gửi tin (cần ít nhất 1 trong 2) ---
TELEGRAM_PERSONAL_CHAT_ID = os.getenv("TELEGRAM_PERSONAL_CHAT_ID")  # chat riêng của bạn
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")              # vd: @ten_kenh_cua_ban hoặc -100xxxxxxxxxx

# --- Tùy chỉnh ---
# Model Gemini dùng để trích Insight. gemini-2.0-flash-lite là free và nhanh nhất.
# Đổi sang "gemini-1.5-flash" nếu muốn chất lượng cao hơn (cũng free).
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")

HOT_THRESHOLD = int(os.getenv("HOT_THRESHOLD", "8"))              # điểm HOT (1-10) để bắn alert ngay
FETCH_INTERVAL_MINUTES = int(os.getenv("FETCH_INTERVAL_MINUTES", "30"))  # tần suất quét nguồn tin
DIGEST_HOUR = int(os.getenv("DIGEST_HOUR", "7"))                  # giờ gửi digest sáng (theo TIMEZONE)
TIMEZONE = os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh")

DB_PATH = os.getenv("DB_PATH", "ai_news.db")

MAX_ARTICLES_PER_FETCH = int(os.getenv("MAX_ARTICLES_PER_FETCH", "40"))  # giới hạn số bài xử lý/lượt quét


def validate():
    """Kiểm tra các biến bắt buộc, dừng sớm với thông báo rõ ràng nếu thiếu."""
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if missing:
        raise RuntimeError(
            f"Thiếu biến môi trường bắt buộc: {', '.join(missing)}. "
            f"Xem hướng dẫn trong README.md / file .env.example"
        )
    if not TELEGRAM_PERSONAL_CHAT_ID and not TELEGRAM_CHANNEL_ID:
        raise RuntimeError(
            "Cần khai báo ít nhất TELEGRAM_PERSONAL_CHAT_ID hoặc TELEGRAM_CHANNEL_ID "
            "(bot cần biết gửi tin vào đâu)."
        )
