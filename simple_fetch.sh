#!/bin/bash

# Ultra-simple Reddit RSS fetcher
# Uses the most basic approach possible

SUBREDDIT="macapps"
DATA_DIR="data"
DATE=$(date -u +%Y-%m-%d)

echo "[$(date -u)] Fetching r/${SUBREDDIT} via RSS..."

# Create directory
mkdir -p "${DATA_DIR}/${SUBREDDIT}"

# Try the simplest possible curl command
curl -L -s \
  -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  "https://www.reddit.com/r/${SUBREDDIT}.rss" \
  -o "${DATA_DIR}/${SUBREDDIT}/${SUBREDDIT}_${DATE}.xml"

if [ -s "${DATA_DIR}/${SUBREDDIT}/${SUBREDDIT}_${DATE}.xml" ]; then
  echo "[$(date -u)] ✓ Success! Saved to ${DATA_DIR}/${SUBREDDIT}/${SUBREDDIT}_${DATE}.xml"

  # Also save as text for easy viewing
  cat "${DATA_DIR}/${SUBREDDIT}/${SUBREDDIT}_${DATE}.xml" | \
    grep -oP '<title>.*?</title>' | \
    sed 's/<[^>]*>//g' | \
    sed '1d' > "${DATA_DIR}/${SUBREDDIT}/${SUBREDDIT}_${DATE}_titles.txt"

  echo "[$(date -u)] ✓ Extracted titles to ${DATA_DIR}/${SUBREDDIT}/${SUBREDDIT}_${DATE}_titles.txt"
  exit 0
else
  echo "[$(date -u)] ✗ Failed to fetch data"
  rm -f "${DATA_DIR}/${SUBREDDIT}/${SUBREDDIT}_${DATE}.xml"
  exit 1
fi
