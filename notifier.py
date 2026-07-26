"""
Định dạng và gửi tin nhắn Telegram (HTML parse mode) tới cả chat riêng
lẫn kênh, tùy theo biến nào được cấu hình trong config.py.
"""
import html
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

import config


def _esc(text: str) -> str:
    return html.escape(text or "", quote=False)


def format_alert(article: dict, insight: dict) -> str:
    return (
        f"🔥 <b>TIN HOT ({insight['hot_score']}/10)</b> — {_esc(article['source'])}\n\n"
        f"<b>{_esc(article['title'])}</b>\n\n"
        f"📌 <b>Điểm chính:</b> {_esc(insight['key_point'])}\n\n"
        f"💡 <b>Insight:</b> {_esc(insight['insight'])}\n\n"
        f"🛠 <b>Áp dụng ngay:</b> {_esc(insight['skill_tip'])}\n\n"
        f"🔗 <a href=\"{article['link']}\">Đọc bài gốc</a>"
    )


def format_digest(articles: list[dict]) -> list[str]:
    """
    Trả về danh sách message (chia nhỏ nếu quá dài — Telegram giới hạn ~4096 ký tự/tin).
    Mỗi phần tử trong `articles` là 1 dict article đã lưu trong DB (storage.py).
    """
    if not articles:
        return []

    header = f"☀️ <b>DIGEST AI SÁNG NAY</b> — {len(articles)} tin đáng chú ý\n"
    blocks = [header]

    for i, a in enumerate(articles, start=1):
        block = (
            f"\n<b>{i}. {_esc(a['title'])}</b>  <i>({_esc(a['source'])}, "
            f"{a['hot_score']}/10 🔥)</i>\n"
            f"📌 {_esc(a['key_point'])}\n"
            f"💡 {_esc(a['insight'])}\n"
            f"🛠 {_esc(a['skill_tip'])}\n"
            f"🔗 <a href=\"{a['link']}\">Đọc bài gốc</a>\n"
        )
        blocks.append(block)

    # Ghép lại rồi cắt theo giới hạn ký tự của Telegram, không cắt giữa 1 bài
    messages, current = [], ""
    for block in blocks:
        if len(current) + len(block) > 3800:
            messages.append(current)
            current = block
        else:
            current += block
    if current:
        messages.append(current)
    return messages


async def send_to_all(bot: Bot, text: str):
    """Gửi 1 đoạn text tới cả TELEGRAM_PERSONAL_CHAT_ID và TELEGRAM_CHANNEL_ID (nếu có cấu hình)."""
    targets = [t for t in (config.TELEGRAM_PERSONAL_CHAT_ID, config.TELEGRAM_CHANNEL_ID) if t]
    for chat_id in targets:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=False,
            )
        except TelegramError as e:
            print(f"[WARN] Gửi tin tới {chat_id} thất bại: {e}")
