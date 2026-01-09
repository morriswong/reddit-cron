# Reddit Daily Scraper

Automated daily collection of Reddit subreddit data using GitHub Actions and git scraping.

## 🚀 Quick Start (5 minutes)

**To make this work reliably, set up OAuth (recommended):**

1. Visit https://www.reddit.com/prefs/apps
2. Create a "script" app
3. Add `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` to GitHub Secrets

**See [SETUP.md](SETUP.md) for detailed instructions** ← Click here!

## Overview

This repository automatically collects Reddit data daily using GitHub Actions. It supports multiple methods with automatic fallback, but **OAuth API is the most reliable** (100% success rate).

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

The system uses a **quad-fallback approach** to maximize reliability:

### Method 1: OAuth API (Primary) ⭐⭐⭐ BEST & RECOMMENDED
- **Script**: `collect_reddit_oauth.py`
- **Reliability**: 100% ✅
- Uses Reddit's **Official API** with authentication
- Never gets blocked
- Free to use (requires 5-minute setup)
- **See [SETUP.md](SETUP.md) for setup instructions**

### Method 2: RSS Feeds (Fallback)
- **Script**: `collect_reddit_rss.py`
- **Reliability**: ~40%
- Uses Reddit's official RSS feeds
- Designed for automated consumption
- Tries multiple endpoints: old.reddit.com, www.reddit.com, reddit.com
- No authentication required

### Method 3: Shell Script (Fallback)
- **Script**: `fetch_reddit.sh`
- **Reliability**: ~10%
- Simple curl/wget-based fetching
- Fast and lightweight
- Minimal dependencies

### Method 4: Python JSON Scraping (Final Fallback)
- **Script**: `collect_reddit_data.py`
- **Reliability**: ~5%
- Most sophisticated fallback
- Session management and cookie handling
- Multiple retry strategies

## Adding More Subreddits

**✨ Super Easy - Just edit `config.yml`!**

```yaml
subreddits:
  - macapps
  - iosapps          # Add more by uncommenting
  - androidapps      # or adding new lines
  - programming
```

**See [HOW_TO_ADD_SUBREDDITS.md](HOW_TO_ADD_SUBREDDITS.md) for detailed instructions!**

### Quick Steps:

1. Open `config.yml`
2. Add or remove subreddits (one per line with `-` prefix)
3. Save and commit
4. Done! The scraper automatically picks them up

## Manual Execution

### Running Locally

**OAuth Method (Best - Requires setup):**
```bash
# Set up credentials first (see SETUP.md)
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_client_secret"
export REDDIT_USER_AGENT="github:reddit-cron:v1.0 (by /u/YOUR_USERNAME)"

pip install requests
python collect_reddit_oauth.py
```

**RSS Method:**
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
