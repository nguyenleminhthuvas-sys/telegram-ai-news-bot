"""
Dùng Google Gemini (free tier) để đọc mỗi bài báo và trích ra:
- key_point: tóm tắt sự kiện trong 1-2 câu
- insight: TẠI SAO nó quan trọng / ý nghĩa sâu hơn đằng sau tin
- skill_tip: 1 hành động/kỹ năng CỤ THỂ người đọc có thể áp dụng ngay
- hot_score: 1-10, mức độ "phải biết ngay" của tin này
"""
import json
import re
import time
import google.generativeai as genai

import config

_model = None


def _get_model():
    global _model
    if _model is None:
        genai.configure(api_key=config.GEMINI_API_KEY)
        _model = genai.GenerativeModel(
            model_name=config.GEMINI_MODEL,
            system_instruction=SYSTEM_PROMPT,
        )
    return _model


SYSTEM_PROMPT = """Bạn là biên tập viên tin tức AI kỳ cựu, viết cho một người đang \
chủ động nâng cấp kiến thức và kỹ năng sử dụng AI (không phải người mới bắt đầu). \
Nhiệm vụ của bạn KHÔNG phải là tóm tắt tin, mà là rút ra GIÁ TRỊ thực sự: \
tin này thay đổi điều gì, và người đọc nên làm gì khác đi sau khi biết tin này.

Luôn trả lời CHỈ bằng JSON hợp lệ, không thêm chữ nào khác, không dùng markdown code fence, \
theo đúng cấu trúc:
{
  "key_point": "1-2 câu tóm tắt sự kiện chính, tiếng Việt, súc tích",
  "insight": "2-3 câu giải thích Ý NGHĨA sâu hơn: vì sao nó quan trọng, xu hướng nó cho thấy, \
tác động thực tế — không lặp lại key_point",
  "skill_tip": "1 hành động CỤ THỂ, làm được ngay, để người đọc áp dụng kiến thức này vào việc \
dùng AI hiệu quả hơn. Nếu bài không có ứng dụng rõ ràng, hãy nêu điều nên theo dõi.",
  "hot_score": <số nguyên 1-10>
}"""

USER_TEMPLATE = """Nguồn: {source}
Tiêu đề: {title}
Tóm tắt gốc: {summary}
Link: {link}

Hãy phân tích bài này theo đúng format JSON đã quy định."""

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "").strip()


def extract_insight(article: dict) -> dict:
    """
    Gọi Gemini để phân tích 1 bài viết. Trả về dict với key_point/insight/skill_tip/hot_score.
    Nếu có lỗi, trả về giá trị mặc định an toàn (hot_score=0).
    """
    model = _get_model()
    summary_text = _strip_html(article.get("summary", ""))[:1500]
    time.sleep(2)  # rate limit: free tier ~30 req/phút

    try:
        response = model.generate_content(
            USER_TEMPLATE.format(
                source=article["source"],
                title=article["title"],
                summary=summary_text or "(không có tóm tắt, hãy suy luận từ tiêu đề)",
                link=article["link"],
            ),
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=500,
                temperature=0.3,
            ),
        )
        raw_text = response.text
        match = _JSON_BLOCK_RE.search(raw_text)
        if not match:
            raise ValueError(f"Không tìm thấy JSON trong phản hồi: {raw_text[:200]}")
        data = json.loads(match.group(0))

        return {
            "key_point": str(data.get("key_point", "")).strip(),
            "insight": str(data.get("insight", "")).strip(),
            "skill_tip": str(data.get("skill_tip", "")).strip(),
            "hot_score": max(1, min(10, int(data.get("hot_score", 5)))),
        }
    except Exception as e:
        print(f"[WARN] Trích insight lỗi cho bài '{article.get('title')}': {e}")
        return {"key_point": "", "insight": "", "skill_tip": "", "hot_score": 0}
