import os
import sys
from dotenv import load_dotenv
from collector import HackerNewsCollector, RedditCollector
from processor import AIProcessor
from publisher import MarkdownPublisher

# Load environment variables
load_dotenv()

def main():
    print("🚀 Starting AI News Collector...")

    # 1. Collection
    hn_collector = HackerNewsCollector()
    reddit_collector = RedditCollector()
    
    raw_items = []
    # Collect from HN
    raw_items.extend(hn_collector.collect(limit=30))
    # Collect from Reddit (Optional: Check if configured)
    if os.getenv("REDDIT_CLIENT_ID"):
        raw_items.extend(reddit_collector.collect(limit=20))
    else:
        print("Skipping Reddit (Not configured)")

    if not raw_items:
        print("No items collected. Exiting.")
        return

    print(f"Total raw items collected: {len(raw_items)}")

    # 2. Processing
    processor = AIProcessor()
    processed_items = processor.process_batch(raw_items)

    # 3. Publishing
    publisher = MarkdownPublisher()
    output_path = publisher.publish(processed_items)
    
    print(f"✅ Job done! Digest saved to: {output_path}")

if __name__ == "__main__":
    main()
