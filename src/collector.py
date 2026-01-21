import os
import time
import requests
import praw
from dataclasses import dataclass, field
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor

@dataclass
class NewsItem:
    title: str
    url: str
    source: str  # 'HN' or 'Reddit'
    original_id: str
    content_snippet: str = ""
    score: int = 0
    comments_count: int = 0
    # Processed fields
    zh_title: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    ai_score: int = 0

class HackerNewsCollector:
    def __init__(self):
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self.keywords = ['AI', 'LLM', 'GPT', 'Transformer', 'Diffusion', 'Generative', 'Machine Learning', 'Neural', 'DeepMind', 'OpenAI', 'Anthropic', 'Llama', 'Mistral']

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
                    
                    # Basic filtering for 'Help' or 'Question' flairs if possible, 
                    # but simple text filtering is safer.
                    if "question" in submission.title.lower() or "help" in submission.title.lower():
                        continue

                    news_items.append(NewsItem(
                        title=submission.title,
                        url=submission.url,
                        source=f"Reddit/{sub_name}",
                        original_id=submission.id,
                        content_snippet=submission.selftext[:500] if submission.selftext else "",
                        score=submission.score,
                        comments_count=submission.num_comments
                    ))
        except Exception as e:
            print(f"Error fetching Reddit: {e}")
        
        # Deduplicate by URL
        unique_items = {item.url: item for item in news_items}.values()
        print(f"Collected {len(unique_items)} items from Reddit.")
        return list(unique_items)
