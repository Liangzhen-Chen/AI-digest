"""
AI Summarizer — uses Google Gemini (free tier) to produce a daily digest.
"""

import os
import re
import json
import requests
from google import genai
from history import get_featured_titles, record_featured

SYSTEM_PROMPT = """你是一位资深的信息分析师，正在为一位产品经理准备每日信息简报。
你的读者重点关注 AI、互联网产品、平台生态、开发者工具、创业公司、消费科技和商业模式。
宏观经济、金融市场和国际政治只在它们会明显影响科技行业、AI 监管、供应链、资本市场或平台公司时纳入。

要求：
1. 用中文撰写，专业术语可保留英文
2. 时事板块每个分类选出最重要的 2-4 条信息，优先选择 AI、互联网、科技商业相关内容
3. 每条信息包含：一句话标题摘要 + 2-3 句分析（为什么重要、可能的影响）
4. 学习板块中，经济金融分析选 2-3 条，互联网产品分析选 6-10 条（权重最高）
5. 学习板块要提炼核心观点和方法论，而不是简单转述
6. 新增「每日产品拆解」环节（500-1000 字，深度分析）：
   - 优先从当天采集到的产品相关信息中挑选一个值得深度分析的产品或功能
   - 如果当天信息中没有合适的产品素材，则根据近期行业动态自主选择一个热门或经典产品进行拆解（需注明"本期为编辑精选"）
   - ⚠️ 重要：所有分析必须基于提供的素材（RSS 全文、Wikipedia 背景资料）中的事实信息。数据、数字、市场份额等必须有来源依据，不要编造具体数字。如果缺少某方面的数据，请如实说明"暂无公开数据"
   - ⚠️ 重要：本节分析也需要标注来源。若涉及多个来源，在具体信息附近标注信息来源及链接。绝对不允许捏造事实。
   - 拆解内容包括：产品五层：【1️⃣战略层（产品目标、用户需求、定位、核心用户价值）；2️⃣ 范围层（功能性产品的主要功能和特色功能、信息性产品的主要内容和特色内容）；3️⃣ 结构层（信息架构、产品结构、页面结构、交互流程）；4️⃣ 框架层 （抽象结构层的具像化，具体表现为信息如何设计、导航如何设计） 5️⃣表现层（感知设计如视觉效果和用户操作）】，商业模式，增长策略，竞争格局，可借鉴的产品方法论
7. 在末尾给出一段 "今日观察"（3-5 句），从产品/商业/投资角度点评今天最值得关注的趋势
8. 语气专业但不死板，像一位见多识广的同事在跟你聊天
9. 如果某个板块信息不足，如实说明，不要编造

输出格式（严格遵循）：

## 📰 时事速览

### 🌍 国际经济政治（仅保留与科技/商业强相关）
- **标题** — 分析内容 [来源](链接)

### 🤖 AI 动态
...

### 💰 商业与金融
...

### 🔬 科技动态
...

## 📚 学习精选

### 📈 经济金融分析
...

### 📱 互联网产品分析
（5-8 条，权重高于其他板块）
...

## 🔍 每日产品拆解
（选一个产品/功能做 500-1000 字深度分析：产品五层、商业模式、增长策略、竞争格局、可借鉴的方法论）
...

## 💡 今日观察
...
"""


GEMINI_MODELS_TO_TRY = [
    "gemini-2.5-flash",       # free tier: 5 RPM, 2 TPM
    "gemini-2.0-flash-lite",  # fallback
]

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"


def _generate_with_gemini(contents: list[dict]) -> str | None:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("  ⚠️  GEMINI_API_KEY is not set; skipping Gemini")
        return None

    client = genai.Client(api_key=api_key)

    for model_name in GEMINI_MODELS_TO_TRY:
        try:
            print(f"  Trying Gemini model: {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
            )
            print(f"  ✅ Success with Gemini model {model_name}")
            return response.text
        except Exception as e:
            print(f"  ❌ Gemini model {model_name} failed: {e}")

    return None


def _generate_with_deepseek(prompt: str) -> str:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "All Gemini models failed and DEEPSEEK_API_KEY is not set"
        )

    print(f"  Trying DeepSeek model: {DEEPSEEK_MODEL}")
    response = requests.post(
        DEEPSEEK_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": DEEPSEEK_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You produce concise, source-grounded Chinese news digests.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        },
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    try:
        digest = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected DeepSeek response: {data}") from exc

    print(f"  ✅ Success with DeepSeek model {DEEPSEEK_MODEL}")
    return digest


def summarize_digest(feeds: dict[str, list[dict]]) -> str:
    """
    Takes the raw feed data, sends it to Gemini for summarisation,
    falls back to DeepSeek if Gemini fails,
    and returns a formatted Markdown digest.
    """
    # Build the raw material prompt
    raw_sections = []
    for section, articles in feeds.items():
        if section == "_wiki_product_context":
            # Special section: Wikipedia grounding data
            lines = ["\n=== 产品背景资料（来自 Wikipedia，用于产品拆解的事实依据）==="]
            for a in articles:
                lines.append(a.get("content", a.get("summary", "")))
            raw_sections.append("\n".join(lines))
            continue

        lines = [f"\n=== {section} ==="]
        for a in articles:
            article_text = (
                f"- [{a.get('source', '')}] {a['title']}\n"
                f"  Link: {a['link']}\n"
                f"  Summary: {a['summary']}\n"
                f"  Published: {a.get('published', 'N/A')}"
            )
            # Include full content for product articles (richer context)
            content = a.get("content", "")
            if content and len(content) > len(a.get("summary", "")):
                article_text += f"\n  Full Content: {content[:2000]}"
            lines.append(article_text)
        raw_sections.append("\n".join(lines))

    # Add history of previously featured products so AI avoids repeats
    featured = get_featured_titles()
    history_note = ""
    if featured:
        history_note = (
            "\n\n=== 已拆解过的产品（请勿重复选择）===\n"
            + "、".join(sorted(featured))
        )

    user_prompt = (
        f"以下是今天从各渠道采集到的原始信息（产品类信息包含近30天内容作为候选池），"
        f"请按要求整理成每日简报：\n\n"
        + "\n\n".join(raw_sections)
        + history_note
        + "\n\n⚠️ 请在「每日产品拆解」板块的第一行用 [[PRODUCT:产品名称]] 格式标注你选择拆解的产品名称，方便系统记录。"
    )

    full_prompt = SYSTEM_PROMPT + "\n\n" + user_prompt
    contents = [
        {"role": "user", "parts": [{"text": full_prompt}]}
    ]

    digest = _generate_with_gemini(contents)
    if digest is None:
        digest = _generate_with_deepseek(full_prompt)

    # Extract and record the featured product name
    match = re.search(r"\[\[PRODUCT:(.+?)\]\]", digest)
    if match:
        product_name = match.group(1).strip()
        record_featured(product_name)
        print(f"  📝 Recorded featured product: {product_name}")
        # Remove the tag from final output
        digest = digest.replace(match.group(0), "").strip()

    return digest
