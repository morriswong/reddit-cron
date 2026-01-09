#!/usr/bin/env python3
"""
Reddit RSS Feed Collector
Fetches Reddit data via RSS feeds which are more reliable than JSON endpoints
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

import requests


class RedditRSSCollector:
    def __init__(self):
        default_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        self.user_agent = os.getenv('REDDIT_USER_AGENT', default_ua)
        # Try multiple RSS endpoints
        self.rss_urls = [
            'https://old.reddit.com/r/{}.rss',
            'https://www.reddit.com/r/{}.rss',
            'https://reddit.com/r/{}.rss',
        ]
        self.max_retries = 3
        self.retry_delay = 5

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        })

    def log(self, message: str, level: str = 'INFO'):
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        print(f"[{timestamp}] {level}: {message}")

    def parse_rss_entry(self, entry: ET.Element, namespaces: dict) -> Dict:
        """Parse a single RSS feed entry"""
        # RSS 2.0 and Atom have different structures
        title = entry.find('title')
        link = entry.find('link')
        author = entry.find('author') or entry.find('{http://www.w3.org/2005/Atom}author')
        published = entry.find('pubDate') or entry.find('updated') or entry.find('{http://www.w3.org/2005/Atom}updated')
        content = entry.find('description') or entry.find('content') or entry.find('{http://www.w3.org/2005/Atom}content')

        # Extract author name
        author_name = 'unknown'
        if author is not None:
            if author.text:
                author_name = author.text
            else:
                name_elem = author.find('{http://www.w3.org/2005/Atom}name')
                if name_elem is not None:
                    author_name = name_elem.text

        # Extract link
        link_url = ''
        if link is not None:
            if link.text:
                link_url = link.text
            elif 'href' in link.attrib:
                link_url = link.attrib['href']

        return {
            'title': title.text if title is not None else '',
            'link': link_url,
            'author': author_name,
            'published': published.text if published is not None else '',
            'content': content.text if content is not None else '',
        }

    def get_subreddit_rss(self, subreddit: str) -> Optional[List[Dict]]:
        """Fetch RSS feed for a subreddit"""

        # Try each URL endpoint
        for url_template in self.rss_urls:
            url = url_template.format(subreddit)

            for attempt in range(self.max_retries):
                try:
                    self.log(f"Trying {url} (attempt {attempt + 1})")

                    if attempt > 0:
                        time.sleep(self.retry_delay)
                    else:
                        time.sleep(2)  # Small delay between different URLs

                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()

                    # Check if we got XML
                    content_type = response.headers.get('content-type', '')
                    if not any(xml_type in content_type.lower() for xml_type in ['xml', 'rss', 'atom']):
                        self.log(f"Unexpected content type: {content_type}", 'WARN')
                        if attempt < self.max_retries - 1:
                            continue
                        raise ValueError(f"Expected XML content, got {content_type}")

                    # Parse RSS/XML
                    root = ET.fromstring(response.content)

                    # Handle both RSS 2.0 and Atom feeds
                    entries = []

                    # Try RSS 2.0 format
                    channel = root.find('channel')
                    if channel is not None:
                        items = channel.findall('item')
                        for item in items:
                            try:
                                entries.append(self.parse_rss_entry(item, {}))
                            except Exception as e:
                                self.log(f"Error parsing RSS item: {e}", 'WARN')
                                continue
                    else:
                        # Try Atom format
                        ns = {'atom': 'http://www.w3.org/2005/Atom'}
                        items = root.findall('atom:entry', ns) or root.findall('{http://www.w3.org/2005/Atom}entry')
                        for item in items:
                            try:
                                entries.append(self.parse_rss_entry(item, ns))
                            except Exception as e:
                                self.log(f"Error parsing Atom entry: {e}", 'WARN')
                                continue

                    if not entries:
                        raise ValueError("No entries found in feed")

                    self.log(f"Successfully fetched {len(entries)} entries for r/{subreddit}")
                    return entries

                except requests.exceptions.RequestException as e:
                    self.log(f"Network error (attempt {attempt + 1}): {e}", 'WARN')
                    if attempt < self.max_retries - 1:
                        continue  # Try next attempt with same URL
                    else:
                        break  # All attempts failed, try next URL

                except (ET.ParseError, ValueError) as e:
                    self.log(f"Parse error: {e}", 'WARN')
                    break  # Parse error, try next URL

        self.log(f"Failed to fetch RSS feed for r/{subreddit} from all sources", 'ERROR')
        return None

    def save_data(self, subreddit: str, entries: List[Dict]):
        """Save RSS entries to files"""
        date_str = datetime.utcnow().strftime('%Y-%m-%d')

        # Create directory structure
        data_dir = Path('data') / subreddit
        data_dir.mkdir(parents=True, exist_ok=True)

        # Save as JSON
        json_filename = f"{subreddit}_{date_str}.json"
        json_filepath = data_dir / json_filename

        try:
            # Create a structure similar to Reddit's JSON API for compatibility
            output_data = {
                'kind': 'Listing',
                'data': {
                    'children': [
                        {
                            'kind': 't3',
                            'data': {
                                'title': entry['title'],
                                'author': entry['author'],
                                'url': entry['link'],
                                'permalink': entry['link'],
                                'created_utc': entry['published'],
                                'selftext': entry.get('content', '')[:500],  # Truncate content
                            }
                        }
                        for entry in entries
                    ]
                },
                'source': 'rss',
                'collected_at': datetime.utcnow().isoformat(),
            }

            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            self.log(f"Saved JSON data to {json_filepath}")

        except IOError as e:
            self.log(f"Failed to save JSON data to {json_filepath}: {e}", 'ERROR')
            raise

        # Save as readable text format
        try:
            text_filename = f"{subreddit}_{date_str}_readable.txt"
            text_filepath = data_dir / text_filename

            with open(text_filepath, 'w', encoding='utf-8') as f:
                f.write(f"Reddit r/{subreddit} - {date_str}\n")
                f.write(f"{'='*60}\n")
                f.write(f"Source: RSS Feed\n")
                f.write(f"Entries: {len(entries)}\n")
                f.write(f"{'='*60}\n\n")

                for i, entry in enumerate(entries, 1):
                    f.write(f"{'='*60}\n")
                    f.write(f"POST #{i}: {entry['title']}\n")
                    f.write(f"{'='*60}\n")
                    f.write(f"Author: u/{entry['author']}\n")
                    f.write(f"Published: {entry['published']}\n")
                    f.write(f"Link: {entry['link']}\n")
                    f.write(f"\nCONTENT:\n{entry.get('content', 'N/A')[:500]}\n\n")

            self.log(f"Saved readable text to {text_filepath}")

        except Exception as e:
            self.log(f"Failed to save readable text: {e}", 'ERROR')
            # Don't raise here - JSON was saved successfully

    def collect_subreddit(self, subreddit: str) -> bool:
        """Collect RSS feed data for a subreddit"""
        self.log(f"Starting RSS collection for r/{subreddit}")

        entries = self.get_subreddit_rss(subreddit)
        if entries is None:
            return False

        try:
            self.save_data(subreddit, entries)
            return True
        except Exception as e:
            self.log(f"Failed to save data for r/{subreddit}: {e}", 'ERROR')
            return False


def main():
    collector = RedditRSSCollector()

    # Configuration - can be extended for multiple subreddits
    subreddits = ['macapps']

    success_count = 0
    total_count = len(subreddits)

    for subreddit in subreddits:
        if collector.collect_subreddit(subreddit):
            success_count += 1
        else:
            collector.log(f"Failed to collect RSS data for r/{subreddit}", 'ERROR')

    collector.log(f"Collection complete: {success_count}/{total_count} successful")

    # Exit with error code if any collections failed
    if success_count < total_count:
        sys.exit(1)


if __name__ == '__main__':
    main()
