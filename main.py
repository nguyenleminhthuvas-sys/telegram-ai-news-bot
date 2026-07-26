"""
AI Insight Bot — bot Telegram tự động quét tin AI mới nhất, dùng Gemini
để trích Key Point / Insight / Skill Tip cho mỗi bài, rồi:
  - Bắn ALERT ngay khi có tin đạt ngưỡng HOT_THRESHOLD
  - Gửi 1 DIGEST tổng hợp mỗi sáng lúc DIGEST_HOUR (giờ TIMEZONE)

Chạy: python main.py
"""
import asyncio
import logging

from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import config
import storage
import sources
import insight
import notifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("ai_insight_bot")


async def fetch_and_alert_job(bot: Bot):
    """Chạy định kỳ mỗi FETCH_INTERVAL_MINUTES: quét nguồn tin mới, trích insight, lưu DB, bắn alert nếu HOT."""
    log.info("Bắt đầu quét tin mới...")
    seen_urls = storage.get_seen_urls(config.DB_PATH)
    new_articles = sources.fetch_new_articles(seen_urls, max_articles=config.MAX_ARTICLES_PER_FETCH)

    if not new_articles:
        log.info("Không có bài mới.")
        return

    log.info(f"Tìm thấy {len(new_articles)} bài mới. Đang trích insight...")
    for article in new_articles:
        result = insight.extract_insight(article)
        storage.save_article(config.DB_PATH, article, result)

        if result["hot_score"] >= config.HOT_THRESHOLD:
            text = notifier.format_alert(article, result)
            await notifier.send_to_all(bot, text)
            storage.mark_alert_sent(config.DB_PATH, article["link"])
            log.info(f"Đã bắn ALERT: {article['title']} ({result['hot_score']}/10)")

    log.info("Hoàn tất lượt quét.")


async def daily_digest_job(bot: Bot):
    """Chạy mỗi ngày lúc DIGEST_HOUR: tổng hợp toàn bộ bài chưa vào digest, gửi 1 (hoặc vài) tin tổng hợp."""
    log.info("Đang tạo digest sáng...")
    pending = storage.get_pending_digest_articles(config.DB_PATH)
    # Chỉ lấy bài đã có key_point (trích insight thành công); bài lỗi hot_score=0 bỏ qua.
    pending = [a for a in pending if a.get("key_point")]

    if not pending:
        log.info("Không có bài nào cho digest hôm nay.")
        return

    messages = notifier.format_digest(pending)
    for msg in messages:
        await notifier.send_to_all(bot, msg)

    storage.mark_digest_sent(config.DB_PATH, [a["link"] for a in pending])
    log.info(f"Đã gửi digest với {len(pending)} bài.")


async def cmd_start(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AI Insight Bot đang hoạt động!\n\n"
        f"• Quét tin mới mỗi {config.FETCH_INTERVAL_MINUTES} phút\n"
        f"• Bắn alert ngay khi tin đạt độ HOT ≥ {config.HOT_THRESHOLD}/10\n"
        f"• Gửi digest tổng hợp mỗi ngày lúc {config.DIGEST_HOUR}:00 ({config.TIMEZONE})\n\n"
        "Dùng /status để xem thống kê nhanh, /digest để lấy digest ngay."
    )


async def cmd_status(update, context: ContextTypes.DEFAULT_TYPE):
    seen = storage.get_seen_urls(config.DB_PATH)
    pending = storage.get_pending_digest_articles(config.DB_PATH)
    await update.message.reply_text(
        f"📊 Đã xử lý tổng cộng: {len(seen)} bài\n"
        f"⏳ Đang chờ vào digest tiếp theo: {len(pending)} bài"
    )


async def cmd_digest_now(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Đang tổng hợp digest, chờ chút...")
    await daily_digest_job(context.bot)


def main():
    config.validate()
    storage.init_db(config.DB_PATH)

    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("digest", cmd_digest_now))

    scheduler = AsyncIOScheduler(timezone=config.TIMEZONE)
    scheduler.add_job(
        fetch_and_alert_job,
        trigger="interval",
        minutes=config.FETCH_INTERVAL_MINUTES,
        args=[application.bot],
        next_run_time=None,  # để job đầu chạy ngay khi start, xem post_init bên dưới
    )
    scheduler.add_job(
        daily_digest_job,
        trigger=CronTrigger(hour=config.DIGEST_HOUR, minute=0),
        args=[application.bot],
    )

    async def _post_init(app: Application):
        scheduler.start()
        # Chạy 1 lượt quét ngay khi bot khởi động, không cần chờ đủ FETCH_INTERVAL_MINUTES đầu tiên
        asyncio.create_task(fetch_and_alert_job(app.bot))
        log.info("Scheduler đã khởi động.")

    application.post_init = _post_init

    log.info("AI Insight Bot đang khởi động (polling)...")
    application.run_polling()


if __name__ == "__main__":
    main()
