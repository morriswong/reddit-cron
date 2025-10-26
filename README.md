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
│       └── reddit-cron.yml      # GitHub Actions workflow
├── data/
│   └── macapps/                 # Data organized by subreddit
│       ├── macapps_2025-10-26.json
│       ├── macapps_2025-10-26_processed.json
│       └── macapps_2025-10-26_readable.txt
├── collect_reddit_data.py       # Python-based data collector
├── fetch_reddit.sh              # Shell-based data collector
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

### Method 1: Shell Script (Primary)
- Simple curl-based fetching
- Fast and lightweight
- Minimal dependencies

### Method 2: Python Script (Fallback)
- More sophisticated with multiple approaches
- Better error handling
- Additional data processing

## Adding More Subreddits

To collect data from additional subreddits:

1. **Edit `fetch_reddit.sh`**:
   ```bash
   SUBREDDITS=("macapps" "iosapps" "androidapps")
   ```

2. **Edit `collect_reddit_data.py`**:
   ```python
   subreddits = ['macapps', 'iosapps', 'androidapps']
   ```

## Manual Execution

### Running Locally

**Shell Script:**
```bash
chmod +x fetch_reddit.sh
./fetch_reddit.sh
```

**Python Script:**
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

### No Data Being Collected

1. Check GitHub Actions logs in the "Actions" tab
2. Verify Reddit's API is accessible (not blocking requests)
3. Try the manual trigger to debug

### Workflow Not Running

1. Ensure GitHub Actions is enabled for the repository
2. Check repository permissions (workflow needs write access)
3. Verify the schedule in `.github/workflows/reddit-cron.yml`

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
