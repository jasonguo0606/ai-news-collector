import os
import time
import requests
import praw
import feedparser
from dataclasses import dataclass, field
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor

@dataclass
class NewsItem:
    title: str
    url: str
    source: str  # 'HN', 'Reddit', or 'RSS/SourceName'
    original_id: str
    content_snippet: str = ""
    score: int = 0
    comments_count: int = 0
    # Processed fields
    zh_title: Optional[str] = None
    summary: Optional[str] = None
    key_points: List[str] = field(default_factory=list)  # New field for bullet points
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    ai_score: int = 0

# Shared AI keyword filter
AI_KEYWORDS = [
    # Core AI Terms
    'AI', 'Artificial Intelligence', '人工智能',
    'LLM', 'Large Language Model', '大语言模型', '大模型',
    'GPT', 'ChatGPT', 'Claude', 'Gemini', 'Llama', 'Mistral', 'Qwen', '通义', '文心',
    # Companies & Labs
    'OpenAI', 'Anthropic', 'DeepMind', 'Google AI', 'Meta AI', 'Baidu AI', '百度', '阿里', 'Alibaba',
    # Technologies
    'Transformer', 'Diffusion', 'Generative', 'Neural Network', '神经网络',
    'Machine Learning', 'Deep Learning', '机器学习', '深度学习',
    'Computer Vision', 'NLP', 'Natural Language', '自然语言',
    'Reinforcement Learning', '强化学习',
    'RAG', 'Agent', 'Embedding', 'Fine-tuning', '微调', 'Prompt',
    # Applications
    'Text-to-Image', 'Image Generation', 'Video Generation', 'AIGC',
    'Chatbot', 'Virtual Assistant', 'AI编程', 'Copilot', 'Code Generation',
    # Research & Papers
    'arXiv', 'Paper', 'Model', 'Dataset', 'Benchmark', 'Algorithm',
]

def is_ai_related(title: str, content: str = "") -> bool:
    """Check if news item is AI-related using keyword matching."""
    text = (title + " " + content).lower()
    return any(keyword.lower() in text for keyword in AI_KEYWORDS)

class HackerNewsCollector:
    def __init__(self):
        self.base_url = "https://hacker-news.firebaseio.com/v0"

    def fetch_item(self, item_id):
        try:
            resp = requests.get(f"{self.base_url}/item/{item_id}.json", timeout=10)
            return resp.json()
        except Exception:
            return None

    def collect(self, limit=50) -> List[NewsItem]:
        print("Fetching Hacker News...")
        try:
            top_ids = requests.get(f"{self.base_url}/topstories.json").json()[:200]
        except Exception as e:
            print(f"Error fetching HN top stories: {e}")
            return []

        news_items = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(self.fetch_item, top_ids)
        
        for item in results:
            if not item or 'title' not in item or 'url' not in item:
                continue
            
            title = item['title']
            # AI keyword filtering
            if is_ai_related(title):
                news_items.append(NewsItem(
                    title=title,
                    url=item['url'],
                    source='HN',
                    original_id=str(item['id']),
                    score=item.get('score', 0),
                    comments_count=item.get('descendants', 0)
                ))
                if len(news_items) >= limit:
                    break
        
        print(f"Collected {len(news_items)} items from HN.")
        return news_items

class RedditCollector:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT", "python:ai-news-collector:v1.0")
        )
        self.subreddits = ["MachineLearning", "LocalLLaMA", "Singularity", "ArtificialIntelligence"]

    def collect(self, limit=10) -> List[NewsItem]:
        print("Fetching Reddit...")
        news_items = []
        try:
            for sub_name in self.subreddits:
                subreddit = self.reddit.subreddit(sub_name)
                # Fetch top posts of the day
                for submission in subreddit.top(time_filter="day", limit=5):
                    if submission.stickied:
                        continue
                    
                    # Filter out questions/help posts
                    if "question" in submission.title.lower() or "help" in submission.title.lower():
                        continue
                    
                    # Apply AI keyword filter
                    content = submission.selftext[:1000] if submission.selftext else ""
                    if not is_ai_related(submission.title, content):
                        continue

                    news_items.append(NewsItem(
                        title=submission.title,
                        url=submission.url,
                        source=f"Reddit/{sub_name}",
                        original_id=submission.id,
                        content_snippet=content,
                        score=submission.score,
                        comments_count=submission.num_comments
                    ))
        except Exception as e:
            print(f"Error fetching Reddit: {e}")
        
        unique_items = {item.url: item for item in news_items}.values()
        print(f"Collected {len(unique_items)} items from Reddit.")
        return list(unique_items)

class RSSCollector:
    def __init__(self):
        # Selected high-quality Chinese AI Tech sources
        self.feeds = [
            ("机器之心", "https://www.jiqizhixin.com/rss"),
            ("量子位", "https://www.qbitai.com/feed"),
            ("InfoQ-AI", "https://www.infoq.cn/feed/topic/33"),
        ]

    def collect(self, limit=10) -> List[NewsItem]:
        print("Fetching RSS Feeds (CN)...")
        news_items = []
        
        for source_name, feed_url in self.feeds:
            try:
                feed = feedparser.parse(feed_url)
                count = 0
                for entry in feed.entries:
                    if count >= 3:  # Limit per source
                        break
                        
                    # Basic content extraction
                    content = ""
                    if 'summary' in entry:
                        content = entry.summary
                    elif 'description' in entry:
                        content = entry.description
                    
                    # Apply AI keyword filter
                    if not is_ai_related(entry.title, content):
                        continue
                    
                    news_items.append(NewsItem(
                        title=entry.title,
                        url=entry.link,
                        source=f"媒体/{source_name}",
                        original_id=entry.link,
                        content_snippet=content[:1000],
                        score=0,
                        comments_count=0
                    ))
                    count += 1
            except Exception as e:
                print(f"Error fetching RSS {source_name}: {e}")

        print(f"Collected {len(news_items)} items from RSS.")
        return news_items
