import os
import datetime
from typing import List, Dict
from jinja2 import Environment, FileSystemLoader
from collector import NewsItem

class MarkdownPublisher:
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'news')
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        
        # Mapping categories to icons for visual appeal
        self.category_icons = {
            "🚀 模型发布": "🚀",
            "🛠️ 工具应用": "🛠️",
            "🔬 学术研究": "🔬",
            "💼 行业动态": "💼",
            "📱 社交媒体": "📱",
            "⚠️ 未分类": "⚠️",
            "其他": "📰"
        }

    def publish(self, items: List[NewsItem]):
        # Group items by category
        news_by_category: Dict[str, List[NewsItem]] = {}
        for item in items:
            cat = item.category if item.category else "其他"
            if cat not in news_by_category:
                news_by_category[cat] = []
            news_by_category[cat].append(item)

        # Prepare context
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        context = {
            "date": today_str,
            "generation_time": datetime.datetime.now().strftime("%H:%M:%S"),
            "total_count": len(items),
            "news_by_category": news_by_category,
            "category_icons": self.category_icons
        }

        # Render template
        template = self.env.get_template("daily_digest.md.j2")
        output_content = template.render(context)

        # Write to file
        output_file = os.path.join(self.output_dir, f"{today_str}.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output_content)
        
        print(f"Successfully generated digest at: {output_file}")
        return output_file
