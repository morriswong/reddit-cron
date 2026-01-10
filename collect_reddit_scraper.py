#!/usr/bin/env python3
"""
Reddit HTML Scraper - NO API, NO AUTH!
Gets post list from RSS, then scrapes public HTML pages for details.

This approach:
1. RSS feed → Get list of posts (officially supported)
2. Scrape public HTML pages → Extract upvotes, comments from page HTML
3. No API needed, no authentication, completely public data
4. Perfect for small batches (20-25 posts/day)
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

import requests
import yaml
from bs4 import BeautifulSoup


class RedditHTMLScraper:
    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })

    def log(self, message: str, level: str = 'INFO'):
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        print(f"[{timestamp}] {level}: {message}")

    def get_post_urls_from_rss(self, subreddit: str):
        """Fetch RSS feed to get list of post URLs"""
        rss_urls = [
            f'https://www.reddit.com/r/{subreddit}.rss',
            f'https://old.reddit.com/r/{subreddit}.rss',
        ]

        for rss_url in rss_urls:
            try:
                self.log(f"Fetching RSS feed from {rss_url}")
                time.sleep(2)

                response = self.session.get(rss_url, timeout=30)
                response.raise_for_status()

                root = ET.fromstring(response.content)
                post_urls = []

                # Try RSS 2.0 format
                items = root.findall('.//item')
                if not items:
                    # Try Atom format
                    items = root.findall('.//{http://www.w3.org/2005/Atom}entry')

                for item in items:
                    link_elem = item.find('link')
                    if link_elem is None:
                        link_elem = item.find('{http://www.w3.org/2005/Atom}link')

                    if link_elem is not None:
                        url = link_elem.text if link_elem.text else link_elem.get('href')
                        if url:
                            post_urls.append(url)

                if post_urls:
                    self.log(f"Found {len(post_urls)} posts from RSS feed")
                    return post_urls

            except Exception as e:
                self.log(f"Failed to fetch RSS from {rss_url}: {e}", 'WARN')
                continue

        self.log("Failed to fetch RSS from all sources", 'ERROR')
        return None

    def scrape_post_details(self, url: str):
        """Scrape a Reddit post page to extract details"""
        try:
            time.sleep(2)  # Be polite!

            self.log(f"Scraping {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract post details from HTML
            details = {}

            # Title - usually in h1 or title tag
            title_elem = soup.find('h1') or soup.find('title')
            details['title'] = title_elem.get_text(strip=True) if title_elem else 'No title'

            # Remove " : subreddit" suffix from title if present
            details['title'] = re.sub(r' : r/\w+$', '', details['title'])

            # Score/Upvotes - look for score in various places
            score = 0
            score_patterns = [
                {'class_': re.compile(r'.*score.*', re.I)},
                {'data-score': True},
                {'aria-label': re.compile(r'.*upvote.*', re.I)},
            ]

            for pattern in score_patterns:
                score_elem = soup.find(['div', 'span', 'button'], pattern)
                if score_elem:
                    score_text = score_elem.get('data-score') or score_elem.get('aria-label') or score_elem.get_text()
                    score_match = re.search(r'(\d+)', str(score_text))
                    if score_match:
                        score = int(score_match.group(1))
                        break

            # Try finding score in JSON-LD structured data
            if score == 0:
                json_ld = soup.find('script', {'type': 'application/ld+json'})
                if json_ld:
                    try:
                        data = json.loads(json_ld.string)
                        if isinstance(data, dict):
                            score = data.get('upvoteCount', 0)
                    except:
                        pass

            details['score'] = score

            # Comment count
            comments = 0
            comment_patterns = [
                re.compile(r'(\d+)\s*comment', re.I),
                re.compile(r'(\d+)\s*discussion', re.I),
            ]

            comment_text = soup.get_text()
            for pattern in comment_patterns:
                match = pattern.search(comment_text)
                if match:
                    comments = int(match.group(1))
                    break

            details['num_comments'] = comments

            # Author - look for author name
            author = 'unknown'
            author_elem = soup.find(['a', 'span'], {'class': re.compile(r'.*author.*', re.I)})
            if author_elem:
                author = author_elem.get_text(strip=True)

            details['author'] = author.replace('u/', '').replace('/u/', '')

            # Post content - try to find the selftext
            content = ''
            content_elem = soup.find(['div'], {'class': re.compile(r'.*content.*|.*text.*|.*post.*', re.I)})
            if content_elem:
                content = content_elem.get_text(strip=True)[:300]

            details['selftext'] = content
            details['url'] = url
            details['permalink'] = url

            self.log(f"Scraped: {details['title'][:50]}... | ⬆{score} 💬{comments}")
            return details

        except Exception as e:
            self.log(f"Failed to scrape {url}: {e}", 'ERROR')
            return {
                'title': 'Failed to scrape',
                'score': 0,
                'num_comments': 0,
                'author': 'unknown',
                'selftext': '',
                'url': url,
                'permalink': url,
            }

    def collect_subreddit(self, subreddit: str):
        """Collect subreddit data using HTML scraping"""
        self.log(f"Starting HTML scraping for r/{subreddit}")

        # Step 1: Get post URLs from RSS
        post_urls = self.get_post_urls_from_rss(subreddit)
        if not post_urls:
            return None

        # Step 2: Scrape each page for details
        self.log(f"Scraping {len(post_urls)} posts...")
        posts = []

        for i, url in enumerate(post_urls, 1):
            self.log(f"Scraping post {i}/{len(post_urls)}")
            details = self.scrape_post_details(url)
            posts.append(details)

            # Be extra polite between requests
            if i % 5 == 0:
                self.log("Taking a short break...")
                time.sleep(3)

        self.log(f"Successfully scraped {len(posts)} posts")
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

        # Save SUMMARY
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

        # Save TOP 10
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
    scraper = RedditHTMLScraper()

    # Load subreddits from config
    subreddits = load_config()
    scraper.log(f"📋 Loaded {len(subreddits)} subreddit(s) from config: {', '.join(subreddits)}")

    success_count = 0
    failed = []

    for subreddit in subreddits:
        posts = scraper.collect_subreddit(subreddit)

        if posts:
            scraper.save_data(subreddit, posts)
            scraper.log(f"✅ Successfully collected r/{subreddit}")
            success_count += 1
        else:
            scraper.log(f"❌ Failed to collect r/{subreddit}", 'ERROR')
            failed.append(subreddit)

    # Summary
    scraper.log(f"📊 Results: {success_count}/{len(subreddits)} successful")
    if failed:
        scraper.log(f"❌ Failed: {', '.join(failed)}", 'ERROR')
        sys.exit(1)

    scraper.log("✅ All done!")


if __name__ == '__main__':
    main()
