# AI Insight Bot

Bot Telegram tự động quét tin AI mới nhất từ 11 nguồn uy tín (OpenAI, Anthropic,
Google Research, Hugging Face, MIT Tech Review, VentureBeat, TechCrunch, The Verge,
Ars Technica, WIRED, arXiv cs.AI), dùng Claude để phân tích mỗi bài thành:

- 📌 **Key Point** — chuyện gì vừa xảy ra
- 💡 **Insight** — vì sao nó quan trọng, xu hướng gì đứng sau nó
- 🛠 **Skill Tip** — 1 việc cụ thể bạn có thể làm ngay để nâng cấp cách dùng AI

Rồi gửi vào Telegram theo 2 luồng:
- 🔥 **Alert tức thì** khi có tin đạt độ HOT (mặc định ≥ 8/10)
- ☀️ **Digest tổng hợp** mỗi sáng (mặc định 7:00, giờ Việt Nam)

Gửi đồng thời vào **cả chat riêng lẫn kênh Telegram** nếu bạn cấu hình cả hai.

---

## 1. Chuẩn bị: lấy 3 thứ cần thiết

### a) Tạo bot Telegram + lấy TOKEN
1. Mở Telegram, tìm **@BotFather**, nhắn `/newbot`
2. Đặt tên hiển thị (vd: `AI Insight Bot`) và username (phải kết thúc bằng `bot`, vd: `ai_insight_vn_bot`)
3. BotFather trả về 1 chuỗi dạng `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   → đây là `TELEGRAM_BOT_TOKEN`, **giữ bí mật**, không share công khai

### b) Lấy Chat ID cá nhân (nếu muốn nhận vào chat riêng)
1. Nhắn bất kỳ tin gì cho bot bạn vừa tạo (bấm Start)
2. Truy cập: `https://api.telegram.org/bot<TOKEN_CUA_BAN>/getUpdates`
3. Tìm số trong `"chat":{"id": 123456789, ...}` → đó là `TELEGRAM_PERSONAL_CHAT_ID`

### c) Tạo kênh + lấy Channel ID (nếu muốn chia sẻ công khai)
1. Tạo 1 kênh Telegram mới (Channel), đặt public hoặc private tùy ý
2. Thêm bot của bạn vào kênh với quyền **Admin** (bắt buộc, để bot gửi được tin)
3. Nếu kênh public: dùng luôn `@ten_kenh_cua_ban` làm `TELEGRAM_CHANNEL_ID`
   Nếu kênh private: forward 1 tin từ kênh tới bot `@userinfobot` để lấy ID dạng `-100xxxxxxxxxx`

### d) Lấy Anthropic API Key (để Claude phân tích tin)
1. Vào [console.anthropic.com](https://console.anthropic.com) → **Settings → API Keys**
2. Tạo key mới, dạng `sk-ant-...` → đây là `ANTHROPIC_API_KEY`
3. Nạp credit (chi phí rất thấp: mỗi bài viết chỉ tốn 1 lệnh gọi model nhỏ;
   dùng model mặc định `claude-sonnet-5`, có thể đổi sang `claude-haiku-4-5-20251001`
   trong `.env` để rẻ hơn nếu bot quét nhiều nguồn/tần suất cao)

---

## 2. Chạy thử trên máy cá nhân (khuyên làm trước khi deploy)

```bash
cd ai_insight_bot
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Mở .env, điền TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, và ít nhất 1 trong 2 Chat ID/Channel ID

python main.py
```

Nếu chạy đúng, bạn sẽ thấy log `AI Insight Bot đang khởi động (polling)...` và
sau ít giây, bot sẽ tự quét lượt đầu tiên. Nhắn `/start` cho bot để kiểm tra
bot còn sống, `/status` để xem thống kê, `/digest` để lấy digest ngay lập tức
(không cần chờ tới sáng).

⚠️ Lưu ý: chạy theo cách này, bot chỉ hoạt động khi máy tính của bạn đang bật
và script đang chạy. Để bot chạy 24/7 mà không cần giữ máy mở, xem phần deploy
cloud bên dưới.

---

## 3. Deploy 24/7 miễn phí (khuyến nghị: Railway)

Bot cần chạy liên tục để quét tin & bắn alert đúng lúc, nên cần một dịch vụ
"luôn bật" — khác với Telegram (nơi bot **hiển thị**), đây là nơi **code chạy**.
Railway có gói miễn phí đơn giản, phù hợp cho bot cá nhân.

### Bước 1 — Đưa code lên GitHub
1. Tạo 1 repo GitHub mới (có thể để private)
2. Upload toàn bộ các file trong thư mục `ai_insight_bot/` (file `.env` KHÔNG
   upload — đã bị `.gitignore` chặn sẵn)

### Bước 2 — Deploy trên Railway
1. Vào [railway.app](https://railway.app), đăng nhập bằng GitHub
2. **New Project → Deploy from GitHub repo** → chọn repo vừa tạo
3. Railway tự nhận diện `Procfile` và chạy `python main.py` dưới dạng **worker**
4. Vào tab **Variables**, thêm từng biến trong `.env.example` (giá trị thật của bạn)
5. Deploy xong, xem tab **Logs** để xác nhận bot đã khởi động thành công

### Lựa chọn khác
- **Render.com**: tương tự Railway, chọn loại service "Background Worker", cũng có gói free (lưu ý free tier của Render có thể tự "ngủ" nếu không phải web service — chọn đúng loại Background Worker để tránh vấn đề này).
- **VPS riêng** (nếu sau này bạn có): cài Python, `pip install -r requirements.txt`, chạy `python main.py` trong `screen`/`tmux`, hoặc tạo `systemd` service để tự khởi động lại nếu crash.

---

## 4. Tùy chỉnh

Tất cả nằm trong file `.env` — không cần sửa code:

| Biến | Ý nghĩa | Mặc định |
|---|---|---|
| `HOT_THRESHOLD` | Điểm HOT (1-10) để bắn alert ngay | `8` |
| `FETCH_INTERVAL_MINUTES` | Bao lâu quét nguồn tin 1 lần | `30` |
| `DIGEST_HOUR` | Giờ gửi digest sáng (0-23) | `7` |
| `CLAUDE_MODEL` | Model Claude dùng phân tích | `claude-sonnet-5` |
| `MAX_ARTICLES_PER_FETCH` | Giới hạn số bài xử lý mỗi lượt quét | `40` |

Muốn thêm/bớt nguồn tin: mở `sources.py`, sửa list `RSS_SOURCES`.
Muốn đổi cách Claude phân tích (vd: giọng văn khác, thêm trường mới): sửa
`SYSTEM_PROMPT` trong `insight.py`.

---

## 5. Cấu trúc code

```
ai_insight_bot/
├── main.py        # Điều phối chính: scheduler + lệnh bot (/start, /status, /digest)
├── config.py       # Đọc biến môi trường
├── sources.py       # Danh sách RSS + logic quét tin mới
├── insight.py       # Gọi Claude để trích Key Point / Insight / Skill Tip / Hot Score
├── storage.py       # SQLite: chống trùng bài, theo dõi bài đã vào digest
├── notifier.py       # Định dạng tin nhắn HTML + gửi tới Telegram
├── requirements.txt
├── .env.example
├── Procfile        # Cho Railway/Render biết cách chạy bot
└── .gitignore
```

## 6. Sự cố thường gặp

- **Bot không gửi gì cả**: kiểm tra log — thường do thiếu quyền Admin trong
  kênh, hoặc Chat ID/Channel ID sai định dạng.
- **1 nguồn RSS liên tục báo lỗi `[WARN]`**: trang đó có thể đã đổi URL feed.
  Vào website nguồn đó tìm link RSS mới, cập nhật trong `sources.py`.
- **Chi phí Anthropic API tăng nhanh**: giảm `FETCH_INTERVAL_MINUTES` (quét
  thưa hơn), giảm `MAX_ARTICLES_PER_FETCH`, hoặc đổi `CLAUDE_MODEL` sang
  `claude-haiku-4-5-20251001`.
