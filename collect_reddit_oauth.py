#!/usr/bin/env python3
"""
Reddit Official API Collector with OAuth Authentication
This uses Reddit's official API which is reliable and won't be blocked.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests


class RedditOAuthCollector:
    def __init__(self):
        # Get credentials from environment variables
        self.client_id = os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        self.user_agent = os.getenv('REDDIT_USER_AGENT', 'github:reddit-cron:v1.0 (by /u/YOUR_USERNAME)')

        if not self.client_id or not self.client_secret:
            self.log("ERROR: Reddit API credentials not found!", 'ERROR')
            self.log("Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables", 'ERROR')
            self.log("See SETUP.md for instructions on how to get these credentials", 'ERROR')
            raise ValueError("Missing Reddit API credentials")

        self.access_token = None
        self.token_expires_at = 0
        self.base_url = 'https://oauth.reddit.com'

    def log(self, message: str, level: str = 'INFO'):
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        print(f"[{timestamp}] {level}: {message}")

    def get_access_token(self) -> str:
        """Get OAuth access token using client credentials"""
        # Check if we have a valid token
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token

        self.log("Getting new access token...")

        auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
        data = {
            'grant_type': 'client_credentials',
        }
        headers = {
            'User-Agent': self.user_agent,
        }

        try:
            response = requests.post(
                'https://www.reddit.com/api/v1/access_token',
                auth=auth,
                data=data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data['access_token']
            # Token expires in 1 hour, refresh 5 minutes early
            self.token_expires_at = time.time() + token_data['expires_in'] - 300

            self.log("Successfully obtained access token")
            return self.access_token

        except Exception as e:
            self.log(f"Failed to get access token: {e}", 'ERROR')
            raise

    def get_subreddit_data(self, subreddit: str, limit: int = 25) -> Optional[Dict]:
        """Fetch subreddit data using OAuth"""
        token = self.get_access_token()

        url = f'{self.base_url}/r/{subreddit}/hot.json'
        headers = {
            'Authorization': f'Bearer {token}',
            'User-Agent': self.user_agent,
        }
        params = {
            'limit': limit,
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.log(f"Fetching r/{subreddit} via OAuth API (attempt {attempt + 1})")

                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()

                # Validate response
                if not isinstance(data, dict) or 'data' not in data:
                    raise ValueError("Invalid Reddit API response")

                post_count = len(data['data']['children'])
                self.log(f"Successfully fetched {post_count} posts from r/{subreddit}")

                return data

            except requests.exceptions.RequestException as e:
                self.log(f"Network error (attempt {attempt + 1}): {e}", 'ERROR')
                if attempt < max_retries - 1:
                    time.sleep(5)
                    # Token might have expired, refresh it
                    if 'unauthorized' in str(e).lower() or response.status_code == 401:
                        self.access_token = None
                        self.get_access_token()
            except Exception as e:
                self.log(f"Error fetching r/{subreddit}: {e}", 'ERROR')
                break

        return None

    def process_posts(self, data: Dict, subreddit: str) -> List[Dict]:
        """Process Reddit posts and extract relevant information"""
        posts = data['data']['children']
        processed_posts = []

        for i, post in enumerate(posts, 1):
            p = post['data']

            # Get post content
            content = p.get('selftext', '')
            if content and len(content) > 500:
                content = content[:500] + '...'

            processed_post = {
                'rank': i,
                'title': p.get('title', ''),
                'author': p.get('author', '[deleted]'),
                'score': p.get('score', 0),
                'num_comments': p.get('num_comments', 0),
                'created_utc': p.get('created_utc', 0),
                'posted_date': datetime.fromtimestamp(p.get('created_utc', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                'permalink': f"https://reddit.com{p.get('permalink', '')}",
                'url': p.get('url', ''),
                'content': content if content else f"[Link Post - URL: {p.get('url', 'N/A')}]",
                'is_self': p.get('is_self', False),
                'upvote_ratio': p.get('upvote_ratio', 0),
                'post_id': p.get('id', ''),
            }

            processed_posts.append(processed_post)

        return processed_posts

    def save_data(self, subreddit: str, data: Dict):
        """Save data to files"""
        date_str = datetime.utcnow().strftime('%Y-%m-%d')

        # Create directory structure
        data_dir = Path('data') / subreddit
        data_dir.mkdir(parents=True, exist_ok=True)

        # Save raw JSON
        raw_filename = f"{subreddit}_{date_str}.json"
        raw_filepath = data_dir / raw_filename

        try:
            with open(raw_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.log(f"Saved raw data to {raw_filepath}")
        except Exception as e:
            self.log(f"Failed to save raw data: {e}", 'ERROR')
            raise

        # Process and save cleaned data
        try:
            processed_posts = self.process_posts(data, subreddit)

            # Save processed JSON
            processed_filename = f"{subreddit}_{date_str}_processed.json"
            processed_filepath = data_dir / processed_filename

            with open(processed_filepath, 'w', encoding='utf-8') as f:
                json.dump(processed_posts, f, indent=2, ensure_ascii=False)
            self.log(f"Saved processed data to {processed_filepath}")

            # Save readable text
            text_filename = f"{subreddit}_{date_str}_readable.txt"
            text_filepath = data_dir / text_filename

            with open(text_filepath, 'w', encoding='utf-8') as f:
                f.write(f"Reddit r/{subreddit} - {date_str}\n")
                f.write(f"{'='*70}\n")
                f.write(f"Source: Reddit Official API (OAuth)\n")
                f.write(f"Posts: {len(processed_posts)}\n")
                f.write(f"{'='*70}\n\n")

                for post in processed_posts:
                    f.write(f"{'='*70}\n")
                    f.write(f"POST #{post['rank']}: {post['title']}\n")
                    f.write(f"{'='*70}\n")
                    f.write(f"Author: u/{post['author']}\n")
                    f.write(f"Score: {post['score']} | Comments: {post['num_comments']} | ")
                    f.write(f"Upvote Ratio: {post['upvote_ratio']:.1%}\n")
                    f.write(f"Posted: {post['posted_date']} UTC\n")
                    f.write(f"Link: {post['permalink']}\n")
                    if post['url'] != post['permalink']:
                        f.write(f"URL: {post['url']}\n")
                    f.write(f"\nCONTENT:\n{post['content']}\n\n")

            self.log(f"Saved readable text to {text_filepath}")

        except Exception as e:
            self.log(f"Failed to process/save cleaned data: {e}", 'ERROR')

    def collect_subreddit(self, subreddit: str) -> bool:
        """Collect data for a subreddit"""
        self.log(f"Starting collection for r/{subreddit}")

        data = self.get_subreddit_data(subreddit)
        if data is None:
            return False

        try:
            self.save_data(subreddit, data)
            return True
        except Exception as e:
            self.log(f"Failed to save data for r/{subreddit}: {e}", 'ERROR')
            return False


def main():
    try:
        collector = RedditOAuthCollector()
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Configuration
    subreddits = ['macapps']

    success_count = 0
    total_count = len(subreddits)

    for subreddit in subreddits:
        if collector.collect_subreddit(subreddit):
            success_count += 1
        else:
            collector.log(f"Failed to collect data for r/{subreddit}", 'ERROR')

    collector.log(f"Collection complete: {success_count}/{total_count} successful")

    if success_count < total_count:
        sys.exit(1)


if __name__ == '__main__':
    main()
