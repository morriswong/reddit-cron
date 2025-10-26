# Reddit Daily Scraper

Automated daily collection of Reddit subreddit data using GitHub Actions and git scraping.

## Overview

This repository automatically scrapes Reddit data daily and stores it as JSON files using GitHub Actions. This is an implementation of the "git scraping" pattern - using GitHub Actions as a scheduled data collection pipeline.

## How It Works

1. **Scheduled Execution**: GitHub Actions runs daily at 12:00 UTC
2. **Data Collection**: Fetches the latest posts from configured subreddits via Reddit's JSON API
3. **Storage**: Saves data as JSON files in the `data/` directory
4. **Version Control**: Commits and pushes changes automatically

## Repository Structure

```
reddit-cron/
├── .github/
│   └── workflows/
│       └── reddit-cron.yml         # GitHub Actions workflow
├── data/
│   └── macapps/                    # Data organized by subreddit
│       ├── macapps_2025-10-26.json
│       └── macapps_2025-10-26_readable.txt
├── collect_reddit_rss.py           # RSS-based collector (Primary)
├── fetch_reddit.sh                 # Shell-based collector (Fallback)
├── collect_reddit_data.py          # Python JSON collector (Final fallback)
├── requirements.txt                # Python dependencies
└── README.md
```

## Features

- **Daily Automation**: Runs automatically every day at 12:00 UTC
- **Manual Trigger**: Can be triggered manually via GitHub Actions UI
- **Dual Methods**: Uses both shell script (primary) and Python (fallback) for reliability
- **Multiple Formats**: Saves data in raw JSON, processed JSON, and human-readable text
- **Error Handling**: Retry logic and fallback mechanisms
- **No Dependencies**: Works without authentication or API keys

## Data Collection Methods

The system uses a **triple-fallback approach** to maximize reliability:

### Method 1: RSS Feeds (Primary) ⭐ Recommended
- **Script**: `collect_reddit_rss.py`
- Uses Reddit's official RSS feeds
- Most reliable and least likely to be blocked
- Tries multiple endpoints: old.reddit.com, www.reddit.com, reddit.com
- RSS feeds are designed for automated consumption
- Converts RSS/XML to JSON format for consistency

### Method 2: Shell Script (Fallback)
- **Script**: `fetch_reddit.sh`
- Simple curl/wget-based fetching
- Fast and lightweight
- Tries multiple Reddit JSON endpoints
- Minimal dependencies

### Method 3: Python JSON Scraping (Final Fallback)
- **Script**: `collect_reddit_data.py`
- More sophisticated with multiple approaches
- Better error handling
- Session management and cookie handling
- Additional data processing

## Adding More Subreddits

To collect data from additional subreddits, edit all three collection scripts:

1. **Edit `collect_reddit_rss.py`** (Primary method):
   ```python
   subreddits = ['macapps', 'iosapps', 'androidapps']
   ```

2. **Edit `fetch_reddit.sh`** (Fallback):
   ```bash
   SUBREDDITS=("macapps" "iosapps" "androidapps")
   ```

3. **Edit `collect_reddit_data.py`** (Final fallback):
   ```python
   subreddits = ['macapps', 'iosapps', 'androidapps']
   ```

## Manual Execution

### Running Locally

**RSS Method (Recommended):**
```bash
pip install requests
python collect_reddit_rss.py
```

**Shell Script:**
```bash
chmod +x fetch_reddit.sh
./fetch_reddit.sh
```

**Python JSON Method:**
```bash
pip install requests
python collect_reddit_data.py
```

### Running in GitHub Actions

1. Go to the "Actions" tab in your repository
2. Select "Reddit Data Collection" workflow
3. Click "Run workflow"

## File Naming Convention

Files are saved with the format: `{subreddit}_{YYYY-MM-DD}.json`

Example: `macapps_2025-10-26.json`

## Data Formats

### Raw JSON (`*_YYYY-MM-DD.json`)
Complete Reddit API response with all fields

### Processed JSON (`*_YYYY-MM-DD_processed.json`)
Cleaned and simplified data structure with key fields:
- Title, author, score
- Number of comments
- Post content (truncated)
- Timestamps and links

### Readable Text (`*_YYYY-MM-DD_readable.txt`)
Human-friendly formatted text file for easy reading

## GitHub Actions Workflow

The workflow includes:
- Automatic scheduling (daily at 12:00 UTC)
- Manual trigger capability
- Dual collection methods with fallback
- Automatic commit and push
- Detailed workflow summaries

## Troubleshooting

### ⚠️ Reddit is Blocking Requests (Less Common with RSS)

**Symptoms:**
- All three methods (RSS, Shell, Python) fail
- "Access denied" or empty responses
- All retry attempts fail

**Why it happens:**
Reddit may block automated scraping, though RSS feeds are usually more reliable because they're officially supported. They may block:
- Known data center IP ranges (including GitHub Actions)
- Requests without proper authentication
- High-frequency automated requests
- Non-browser user agents

**Good News:**
The RSS method (primary) is designed for automated consumption and has a much higher success rate than JSON scraping.

**Solutions if RSS also fails:**

1. **Use Reddit's Official API** (Recommended for 100% reliability)
   - Create a Reddit app at https://www.reddit.com/prefs/apps
   - Get OAuth credentials
   - Update the scripts to use authenticated requests
   - This is the most reliable long-term solution

2. **Try Alternative Hosting**
   - Consider using a service like Render, Railway, or Vercel
   - Different hosting providers may have better success rates
   - Some providers' IP ranges are less likely to be blocked

3. **Accept Intermittent Failures**
   - Reddit blocking is sometimes temporary
   - The workflow will retry daily automatically
   - Some days may succeed while others fail
   - This is normal for unauthenticated git scraping

4. **Try Different Timing**
   - Sometimes blocking varies by time of day
   - The workflow runs daily at 12:00 UTC
   - You can manually trigger at different times to test

### No Data Being Collected

1. Check GitHub Actions logs in the "Actions" tab
2. Look for specific error messages in the workflow output
3. Try the manual trigger to debug
4. Check the workflow summary for helpful suggestions

### Workflow Not Running

1. Ensure GitHub Actions is enabled for the repository
2. Check repository permissions (workflow needs write access)
3. Verify the schedule in `.github/workflows/reddit-cron.yml`
4. Check if you've hit GitHub Actions usage limits

## Rate Limiting

Reddit's public JSON API has rate limits. The scripts include:
- User-agent headers to identify the bot
- Retry logic with delays
- Multiple fetch approaches

## Privacy & Ethics

- Only collects publicly available data
- Uses Reddit's public JSON endpoints
- No authentication required
- Respects robots.txt and rate limits

## Credits

Based on the "git scraping" pattern popularized by Simon Willison.

## License

MIT License - Feel free to use and modify for your own projects.

## Related Resources

- [Git Scraping](https://simonwillison.net/2020/Oct/9/git-scraping/) by Simon Willison
- [Reddit JSON API](https://www.reddit.com/dev/api/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
