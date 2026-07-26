"""
Danh sách nguồn tin AI + logic quét RSS.

Đây là danh sách khởi điểm, đã kiểm tra tồn tại tại thời điểm viết code.
RSS URL của các trang có thể đổi theo thời gian — nếu một nguồn liên tục
lỗi (xem log "[WARN]"), hãy vào website nguồn đó tìm link RSS mới và
sửa lại trong list RSS_SOURCES bên dưới. Bạn có thể thêm/bớt nguồn tùy ý.
"""
import time
import feedparser

RSS_SOURCES = [
    {"name": "OpenAI News", "url": "https://openai.com/news/rss.xml"},
    {"name": "Anthropic News (mirror)", "url": "https://rsshub.bestblogs.dev/anthropic/news"},
    {"name": "Google Research Blog", "url": "https://research.google/blog/rss/"},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "MIT Technology Review - AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "The Verge AI", "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"},
    {"name": "Ars Technica AI", "url": "https://arstechnica.com/ai/feed/"},
    {"name": "WIRED AI", "url": "https://www.wired.com/feed/tag/ai/latest/rss"},
    {"name": "arXiv cs.AI (bài nghiên cứu mới)", "url": "http://export.arxiv.org/rss/cs.AI"},
]


def _entry_published_ts(entry) -> float:
    """Lấy timestamp xuất bản của bài viết; fallback về thời điểm hiện tại nếu feed không cung cấp."""
    for key in ("published_parsed", "updated_parsed"):
        val = entry.get(key)
        if val:
            try:
                return time.mktime(val)
            except (TypeError, ValueError, OverflowError):
                pass
    return time.time()


def fetch_new_articles(seen_urls: set, max_articles: int = 40) -> list[dict]:
    """
    Quét toàn bộ RSS_SOURCES, trả về danh sách bài viết CHƯA có trong seen_urls,
    sắp xếp mới nhất trước, giới hạn số lượng bằng max_articles (tránh dội bom
    lần chạy đầu tiên khi DB còn trống).
    """
    new_articles = []

    for source in RSS_SOURCES:
        try:
            feed = feedparser.parse(source["url"])
            if feed.bozo and not feed.entries:
                # bozo=True + không có entries thường nghĩa là feed lỗi/đổi URL
                print(f"[WARN] Nguồn '{source['name']}' có vẻ lỗi hoặc đã đổi URL RSS.")
                continue
        except Exception as e:
            print(f"[WARN] Không đọc được nguồn '{source['name']}': {e}")
            continue

        for entry in feed.entries:
            link = entry.get("link")
            if not link or link in seen_urls:
                continue
            summary = entry.get("summary", "") or entry.get("description", "")
            new_articles.append({
                "title": (entry.get("title") or "(không có tiêu đề)").strip(),
                "link": link,
                "summary": summary,
                "source": source["name"],
                "published_ts": _entry_published_ts(entry),
            })

    new_articles.sort(key=lambda a: a["published_ts"], reverse=True)
    return new_articles[:max_articles]
