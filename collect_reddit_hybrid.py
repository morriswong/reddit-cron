#!/usr/bin/env python3
"""
Hybrid Reddit Data Collector - NO AUTH REQUIRED
Uses RSS to get post list, then fetches individual post JSONs for details.

This clever approach:
1. Gets post links from RSS (officially supported, less blocked)
2. Fetches each post's JSON individually (less aggressive than bulk scraping)
3. Extracts upvotes, comments, and other stats
"""

import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

import requests
import yaml


class HybridRedditCollector:
    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/json, text/html, */*',
        })

    def log(self, message: str, level: str = 'INFO'):
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        print(f"[{timestamp}] {level}: {message}")

    def get_post_ids_from_rss(self, subreddit: str):
        """Fetch RSS feed to get list of post IDs"""
        rss_urls = [
            f'https://www.reddit.com/r/{subreddit}.rss',
            f'https://old.reddit.com/r/{subreddit}.rss',
        ]

        for rss_url in rss_urls:
            try:
                self.log(f"Fetching RSS feed from {rss_url}")
                time.sleep(2)  # Be polite

                response = self.session.get(rss_url, timeout=30)
                response.raise_for_status()

                # Parse RSS
                root = ET.fromstring(response.content)

                post_ids = []

                # Try RSS 2.0 format
                items = root.findall('.//item')
                if not items:
                    # Try Atom format
                    items = root.findall('.//{http://www.w3.org/2005/Atom}entry')

                for item in items:
                    # Get link
                    link_elem = item.find('link')
                    if link_elem is None:
                        link_elem = item.find('{http://www.w3.org/2005/Atom}link')

                    if link_elem is not None:
                        link = link_elem.text if link_elem.text else link_elem.get('href')

                        # Extract post ID from link
                        # Format: https://www.reddit.com/r/subreddit/comments/POST_ID/title/
                        match = re.search(r'/comments/([a-z0-9]+)/', link)
                        if match:
                            post_ids.append({
                                'id': match.group(1),
                                'link': link
                            })

                if post_ids:
                    self.log(f"Found {len(post_ids)} posts from RSS feed")
                    return post_ids

            except Exception as e:
                self.log(f"Failed to fetch RSS from {rss_url}: {e}", 'WARN')
                continue

        self.log("Failed to fetch RSS from all sources", 'ERROR')
        return None

    def get_post_details(self, post_id: str, subreddit: str):
        """Fetch individual post JSON to get detailed stats"""
        # Individual post JSON endpoint
        json_url = f'https://www.reddit.com/r/{subreddit}/comments/{post_id}.json'

        max_retries = 2
        for attempt in range(max_retries):
            try:
                time.sleep(1.5)  # Rate limiting

                response = self.session.get(json_url, timeout=20)
                response.raise_for_status()

                data = response.json()

                # Reddit returns an array with 2 elements: [post_data, comments_data]
                if isinstance(data, list) and len(data) > 0:
                    post_data = data[0]['data']['children'][0]['data']

                    return {
                        'id': post_data.get('id'),
                        'title': post_data.get('title', 'No title'),
                        'author': post_data.get('author', '[deleted]'),
                        'score': post_data.get('score', 0),
                        'upvote_ratio': post_data.get('upvote_ratio', 0),
                        'num_comments': post_data.get('num_comments', 0),
                        'created_utc': post_data.get('created_utc', 0),
                        'url': post_data.get('url', ''),
                        'permalink': f"https://reddit.com{post_data.get('permalink', '')}",
                        'selftext': post_data.get('selftext', '')[:300],
                        'is_self': post_data.get('is_self', False),
                    }

            except Exception as e:
                if attempt < max_retries - 1:
                    self.log(f"Retry fetching post {post_id}: {e}", 'WARN')
                    time.sleep(3)
                else:
                    self.log(f"Failed to fetch post {post_id}: {e}", 'ERROR')
                    return None

        return None

    def collect_subreddit(self, subreddit: str):
        """Collect subreddit data using hybrid approach"""
        self.log(f"Starting hybrid collection for r/{subreddit}")

        # Step 1: Get post IDs from RSS
        post_ids = self.get_post_ids_from_rss(subreddit)
        if not post_ids:
            return None

        # Step 2: Fetch details for each post
        self.log(f"Fetching details for {len(post_ids)} posts...")
        posts = []

        for i, post_info in enumerate(post_ids, 1):
            self.log(f"Fetching post {i}/{len(post_ids)}: {post_info['id']}")

            details = self.get_post_details(post_info['id'], subreddit)
            if details:
                posts.append(details)
            else:
                # If we can't get details, at least save the link
                posts.append({
                    'id': post_info['id'],
                    'title': 'Details unavailable',
                    'score': 0,
                    'num_comments': 0,
                    'permalink': post_info['link'],
                })

            # Be polite, don't hammer the server
            if i % 5 == 0:
                time.sleep(2)

        self.log(f"Successfully fetched {len(posts)} posts")
        return posts

    def save_data(self, subreddit: str, posts: list):
        """Save data in multiple formats for easy scanning"""
        date_str = datetime.utcnow().strftime('%Y-%m-%d')

        # Create directory
        data_dir = Path('data') / subreddit
        data_dir.mkdir(parents=True, exist_ok=True)

        # Sort by score (most popular first)
        posts_by_score = sorted(posts, key=lambda x: x.get('score', 0), reverse=True)

        # Save JSON
        json_file = data_dir / f"{subreddit}_{date_str}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(posts_by_score, f, indent=2, ensure_ascii=False)
        self.log(f"Saved JSON to {json_file}")

        # Save SUMMARY for quick scanning (sorted by popularity)
        summary_file = data_dir / f"{subreddit}_{date_str}_SUMMARY.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"r/{subreddit} - {date_str}\n")
            f.write(f"{'='*80}\n")
            f.write(f"SORTED BY POPULARITY (Most upvoted first)\n")
            f.write(f"Total posts: {len(posts)}\n")
            f.write(f"{'='*80}\n\n")

            for i, post in enumerate(posts_by_score, 1):
                f.write(f"\n{'─'*80}\n")
                f.write(f"#{i} | ⬆ {post.get('score', 0):4d} upvotes | 💬 {post.get('num_comments', 0):3d} comments | 👤 u/{post.get('author', 'unknown')}\n")
                f.write(f"{'─'*80}\n")
                f.write(f"{post.get('title', 'No title')}\n")
                f.write(f"🔗 {post.get('permalink', 'No link')}\n")

                if post.get('selftext'):
                    f.write(f"\n{post['selftext'][:200]}...\n")

        self.log(f"Saved SUMMARY to {summary_file}")

        # Save TOP 10 for super quick scanning
        top10_file = data_dir / f"{subreddit}_{date_str}_TOP10.txt"
        with open(top10_file, 'w', encoding='utf-8') as f:
            f.write(f"r/{subreddit} - TOP 10 MOST POPULAR - {date_str}\n")
            f.write(f"{'='*80}\n\n")

            for i, post in enumerate(posts_by_score[:10], 1):
                f.write(f"{i:2d}. ⬆{post.get('score', 0):4d} 💬{post.get('num_comments', 0):3d} | {post.get('title', 'No title')[:60]}\n")
                f.write(f"    {post.get('permalink', '')}\n\n")

        self.log(f"Saved TOP 10 to {top10_file}")


def load_config():
    """Load subreddits from config file"""
    config_file = Path('config.yml')

    if not config_file.exists():
        print(f"⚠️  Config file not found: {config_file}")
        print("Using default: ['macapps']")
        return ['macapps']

    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            subreddits = config.get('subreddits', ['macapps'])

            # Filter out None values and empty strings
            subreddits = [s for s in subreddits if s]

            if not subreddits:
                print("⚠️  No subreddits found in config, using default: ['macapps']")
                return ['macapps']

            return subreddits
    except Exception as e:
        print(f"⚠️  Error loading config: {e}")
        print("Using default: ['macapps']")
        return ['macapps']


def main():
    collector = HybridRedditCollector()

    # Load subreddits from config file
    subreddits = load_config()
    collector.log(f"📋 Loaded {len(subreddits)} subreddit(s) from config: {', '.join(subreddits)}")

    success_count = 0
    failed = []

    for subreddit in subreddits:
        posts = collector.collect_subreddit(subreddit)

        if posts:
            collector.save_data(subreddit, posts)
            collector.log(f"✅ Successfully collected r/{subreddit}")
            success_count += 1
        else:
            collector.log(f"❌ Failed to collect r/{subreddit}", 'ERROR')
            failed.append(subreddit)

    # Summary
    collector.log(f"📊 Results: {success_count}/{len(subreddits)} successful")
    if failed:
        collector.log(f"❌ Failed: {', '.join(failed)}", 'ERROR')
        sys.exit(1)

    collector.log("✅ All done!")


if __name__ == '__main__':
    main()
