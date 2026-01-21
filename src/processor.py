import os
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_fixed
from collector import NewsItem

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIProcessor:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")

    def _get_prompt(self, item: NewsItem) -> str:
        return f"""
        你是一个专业的 AI 科技新闻编辑。请分析以下新闻条目，并以 JSON 格式输出处理结果。

        新闻标题: {item.title}
        来源: {item.source}
        内容片段: {item.content_snippet}

        要求：
        1. zh_title: 将标题翻译为中文，保持信达雅。
        2. summary: 用中文写一段 50-80 字的摘要，概括核心内容。
        3. category: 从 ["🚀 模型发布", "🛠️ 工具应用", "🔬 学术研究", "💼 行业动态", "📱 社交媒体"] 中选择最合适的一个。
        4. tags: 提取 2-3 个英文标签 (如 LLM, RAG, Agent, CV)。
        5. score: 根据新闻对 AI 领域的重要性打分 (1-5 的整数)。

        请仅输出 JSON 字符串，不要包含 Markdown 标记。
        """

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def process_item(self, item: NewsItem) -> NewsItem:
        if not item.title:
            return item

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs strict JSON."},
                    {"role": "user", "content": self._get_prompt(item)}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            if content.startswith("```json"):
                content = content[7:-3]
            
            data = json.loads(content)
            
            item.zh_title = data.get("zh_title", item.title)
            item.summary = data.get("summary", "")
            item.category = data.get("category", "其他")
            item.tags = data.get("tags", [])
            item.ai_score = data.get("score", 3)
            
        except Exception as e:
            logger.error(f"Failed to process item {item.title}: {e}")
            item.zh_title = item.title
            item.summary = "AI 处理失败，请查看原文。"
            item.category = "⚠️ 未分类"
            item.ai_score = 1
            
        return item

    def process_batch(self, items: List[NewsItem]) -> List[NewsItem]:
        logger.info(f"Processing {len(items)} items with AI...")
        processed_items = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(self.process_item, items)
            processed_items = list(results)
        
        # Sort by Score
        processed_items.sort(key=lambda x: x.ai_score, reverse=True)
        return processed_items
