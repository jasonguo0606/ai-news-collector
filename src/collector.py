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

class HackerNewsCollector:
    def __init__(self):
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self.keywords = ['AI', 'LLM', 'GPT', 'Transformer', 'Diffusion', 'Generative', 'Machine Learning', 'Neural', 'DeepMind', 'OpenAI', 'Anthropic', 'Llama', 'Mistral', 'Gemini']

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
            # Keyword filtering
            if any(k.lower() in title.lower() for k in self.keywords):
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
        self.subreddits = ["MachineLearning", "LocalLLaMA", "Singularity", "ArtificialIntelligences"]

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
                    
                    if "question" in submission.title.lower() or "help" in submission.title.lower():
                        continue

                    news_items.append(NewsItem(
                        title=submission.title,
                        url=submission.url,
                        source=f"Reddit/{sub_name}",
                        original_id=submission.id,
                        content_snippet=submission.selftext[:1000] if submission.selftext else "", # Increased snippet length
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
        # Selected high-quality Chinese AI Tech Blogs
        self.feeds = {
            "机器之心": "https://www.jiqizhixin.com/rss",
            "量子位": "https://www.qbitai.com/feed",
            "36Kr-AI": "https://36kr.com/feed-tags/ai", # Note: 36kr tag feed structure might vary, generic fallback
            "AI-Hub": "https://rsshub.app/ai/news",  # Example aggregator if available
        }
        # Filter for strictly RSS URLs that work directly without heavy anti-bot
        # Using a safer list for stability
        self.feeds = [
            ("机器之心", "https://www.jiqizhixin.com/rss"),
            ("量子位", "https://www.qbitai.com/feed"),
            ("InfoQ-AI", "https://www.infoq.cn/feed/topic/33"), # InfoQ AI Topic
        ]

    def collect(self, limit=10) -> List[NewsItem]:
        print("Fetching RSS Feeds (CN)...")
        news_items = []
        
        for source_name, feed_url in self.feeds:
            try:
                feed = feedparser.parse(feed_url)
                count = 0
                for entry in feed.entries:
                    # Filter by date? Let's just take top N latest
                    if count >= 3: # Limit per source
                        break
                        
                    # Basic content extraction
                    content = ""
                    if 'summary' in entry:
                        content = entry.summary
                    elif 'description' in entry:
                        content = entry.description
                    
                    # Remove HTML tags roughly for snippet if needed, 
                    # but Processor handles text better. Let's keep raw text for now or truncate.
                    
                    news_items.append(NewsItem(
                        title=entry.title,
                        url=entry.link,
                        source=f"媒体/{source_name}",
                        original_id=entry.link,
                        content_snippet=content[:1000], # Provide more context
                        score=0, # RSS doesn't have scores usually
                        comments_count=0
                    ))
                    count += 1
            except Exception as e:
                print(f"Error fetching RSS {source_name}: {e}")

        print(f"Collected {len(news_items)} items from RSS.")
        return news_items
