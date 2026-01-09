#!/usr/bin/env python3
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests


class RedditDataCollector:
    def __init__(self):
        # Use a realistic browser user agent
        default_ua = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        self.user_agent = os.getenv('REDDIT_USER_AGENT', default_ua)
        self.base_url = 'https://www.reddit.com/r/{}.json'
        self.max_retries = 3
        self.retry_delay = 5
        
        # Create a session for cookie persistence
        self.session = requests.Session()
        
        # Set comprehensive headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
        
    def log(self, message: str, level: str = 'INFO'):
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        print(f"[{timestamp}] {level}: {message}")
        
    def get_subreddit_data(self, subreddit: str) -> Optional[Dict]:
        url = self.base_url.format(subreddit)
        
        # First, visit the regular page to get cookies
        regular_url = f'https://www.reddit.com/r/{subreddit}'
        
        for attempt in range(self.max_retries):
            try:
                self.log(f"Fetching data for r/{subreddit} (attempt {attempt + 1})")
                
                # Add some delay to avoid being flagged as bot
                if attempt > 0:
                    time.sleep(self.retry_delay + attempt)
                else:
                    time.sleep(2)  # Always wait a bit
                
                # Try multiple approaches to get around blocking
                approaches = [
                    # Approach 1: Visit regular page first, then request JSON
                    lambda: self._try_with_session_establishment(url, regular_url),
                    # Approach 2: Direct request with rotating user agents
                    lambda: self._try_with_alternative_ua(url),
                    # Approach 3: Use old.reddit.com
                    lambda: self._try_old_reddit(subreddit),
                ]
                
                response = None
                for i, approach in enumerate(approaches):
                    try:
                        self.log(f"Trying approach {i+1}")
                        response = approach()
                        if response and response.status_code == 200:
                            break
                    except Exception as e:
                        self.log(f"Approach {i+1} failed: {e}", 'DEBUG')
                        continue
                
                if not response or response.status_code != 200:
                    raise requests.exceptions.RequestException("All approaches failed")
                response.raise_for_status()
                
                data = response.json()
                
                # Check if we got HTML instead of JSON (Reddit blocking)
                if response.headers.get('content-type', '').startswith('text/html'):
                    raise ValueError("Reddit returned HTML instead of JSON - likely blocking request")
                
                # Validate JSON structure
                if not isinstance(data, dict) or 'data' not in data:
                    raise ValueError("Invalid Reddit JSON structure")
                
                # Check for reasonable data size
                if len(response.content) < 100:
                    raise ValueError("Response too small, likely empty or error")
                    
                if len(response.content) > 50 * 1024 * 1024:  # 50MB limit
                    self.log(f"Warning: Large response size for r/{subreddit}: {len(response.content)} bytes", 'WARN')
                
                self.log(f"Successfully fetched data for r/{subreddit} ({len(response.content)} bytes)")
                return data
                
            except requests.exceptions.RequestException as e:
                self.log(f"Network error for r/{subreddit} (attempt {attempt + 1}): {e}", 'ERROR')
                if attempt < self.max_retries - 1:
                    self.log(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                    
            except (json.JSONDecodeError, ValueError) as e:
                self.log(f"Data validation error for r/{subreddit}: {e}", 'ERROR')
                break
                
        self.log(f"Failed to fetch data for r/{subreddit} after {self.max_retries} attempts", 'ERROR')
        return None
    
    def _try_with_session_establishment(self, url: str, regular_url: str):
        """Approach 1: Visit regular page first to establish session"""
        self.session.get(regular_url, timeout=30)
        json_headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': regular_url,
            'X-Requested-With': 'XMLHttpRequest',
        }
        return self.session.get(url, headers=json_headers, timeout=30)
    
    def _try_with_alternative_ua(self, url: str):
        """Approach 2: Try with different user agents"""
        alternative_uas = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0',
        ]
        
        for ua in alternative_uas:
            temp_session = requests.Session()
            temp_session.headers.update({'User-Agent': ua})
            try:
                response = temp_session.get(url, timeout=30)
                if response.status_code == 200:
                    return response
            except:
                continue
        return None
    
    def _try_old_reddit(self, subreddit: str):
        """Approach 3: Try old.reddit.com which is sometimes less restrictive"""
        old_url = f'https://old.reddit.com/r/{subreddit}.json'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        return self.session.get(old_url, headers=headers, timeout=30)
        
    def process_posts(self, data: Dict, subreddit: str) -> List[Dict]:
        """Process Reddit posts and extract relevant information"""
        posts = data['data']['children']
        processed_posts = []
        
        for i, post in enumerate(posts, 1):
            p = post['data']
            
            # Clean up the post content
            content = p.get('selftext', '')
            if content:
                # Remove markdown and clean up
                content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Bold
                content = re.sub(r'\*(.*?)\*', r'\1', content)      # Italic
                content = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', content)  # Links
                content = content[:500] + ('...' if len(content) > 500 else '')
            
            processed_post = {
                'rank': i,
                'title': p['title'],
                'author': p['author'],
                'score': p['score'],
                'num_comments': p['num_comments'],
                'created_utc': p['created_utc'],
                'posted_date': datetime.fromtimestamp(p['created_utc']).strftime('%Y-%m-%d %H:%M'),
                'permalink': f"https://reddit.com{p['permalink']}",
                'url': p.get('url', ''),
                'content': content if content else f"[Link/Image Post - URL: {p.get('url', 'N/A')}]",
                'is_self': p.get('is_self', False)
            }
            
            processed_posts.append(processed_post)
            
        return processed_posts

    def save_data(self, subreddit: str, data: Dict):
        date_str = datetime.utcnow().strftime('%Y-%m-%d')
        
        # Create directory structure
        data_dir = Path('data') / subreddit
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Save raw JSON data
        raw_filename = f"{subreddit}_{date_str}.json"
        raw_filepath = data_dir / raw_filename
        
        try:
            with open(raw_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self.log(f"Saved raw data to {raw_filepath}")
            
        except IOError as e:
            self.log(f"Failed to save raw data to {raw_filepath}: {e}", 'ERROR')
            raise
            
        # Process and save cleaned data
        try:
            processed_posts = self.process_posts(data, subreddit)
            
            # Save processed data as JSON
            processed_filename = f"{subreddit}_{date_str}_processed.json"
            processed_filepath = data_dir / processed_filename
            
            with open(processed_filepath, 'w', encoding='utf-8') as f:
                json.dump(processed_posts, f, indent=2, ensure_ascii=False)
                
            self.log(f"Saved processed data to {processed_filepath}")
            
            # Save as readable text format
            text_filename = f"{subreddit}_{date_str}_readable.txt"
            text_filepath = data_dir / text_filename
            
            with open(text_filepath, 'w', encoding='utf-8') as f:
                f.write(f"Reddit r/{subreddit} - {date_str}\n")
                f.write(f"{'='*60}\n\n")
                
                for post in processed_posts:
                    f.write(f"{'='*60}\n")
                    f.write(f"POST #{post['rank']}: {post['title']}\n")
                    f.write(f"{'='*60}\n")
                    f.write(f"Author: u/{post['author']}\n")
                    f.write(f"Score: {post['score']} | Comments: {post['num_comments']}\n")
                    f.write(f"Posted: {post['posted_date']}\n")
                    f.write(f"Link: {post['permalink']}\n")
                    f.write(f"\nCONTENT:\n{post['content']}\n\n")
                    
            self.log(f"Saved readable text to {text_filepath}")
            
        except Exception as e:
            self.log(f"Failed to process and save cleaned data: {e}", 'ERROR')
            # Don't raise here - raw data was saved successfully
            
    def collect_subreddit(self, subreddit: str) -> bool:
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
    collector = RedditDataCollector()
    
    # Configuration - can be extended for multiple subreddits
    subreddits = ['macapps']
    
    success_count = 0
    total_count = len(subreddits)
    
    for subreddit in subreddits:
        if collector.collect_subreddit(subreddit):
            success_count += 1
        else:
            collector.log(f"Failed to collect data for r/{subreddit}", 'ERROR')
            
    collector.log(f"Collection complete: {success_count}/{total_count} successful")
    
    # Exit with error code if any collections failed
    if success_count < total_count:
        sys.exit(1)


if __name__ == '__main__':
    main()