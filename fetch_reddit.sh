#!/bin/bash

# Simple Reddit data fetcher for git scraping
# This script fetches Reddit data using curl with minimal dependencies

set -e  # Exit on error

# Configuration
SUBREDDITS=("macapps")
DATA_DIR="data"
DATE=$(date -u +%Y-%m-%d)
USER_AGENT="Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0"

# Function to fetch Reddit data
fetch_subreddit() {
    local subreddit=$1
    local output_dir="${DATA_DIR}/${subreddit}"
    local output_file="${output_dir}/${subreddit}_${DATE}.json"

    echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] INFO: Fetching r/${subreddit}"

    # Create directory if it doesn't exist
    mkdir -p "$output_dir"

    # Fetch data using curl with retry logic
    local max_attempts=3
    local attempt=1
    local success=false

    while [ $attempt -le $max_attempts ]; do
        echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] INFO: Attempt $attempt of $max_attempts"

        # Try to fetch data
        if curl -s -L \
            -H "User-Agent: ${USER_AGENT}" \
            -H "Accept: application/json" \
            --max-time 30 \
            "https://www.reddit.com/r/${subreddit}.json" \
            -o "$output_file"; then

            # Check if file is valid JSON and not empty
            if [ -s "$output_file" ] && jq empty "$output_file" 2>/dev/null; then
                local file_size=$(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file" 2>/dev/null)
                echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] INFO: Successfully fetched r/${subreddit} (${file_size} bytes)"
                success=true
                break
            else
                echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] WARN: Invalid or empty response"
                rm -f "$output_file"
            fi
        fi

        if [ $attempt -lt $max_attempts ]; then
            echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] INFO: Retrying in 5 seconds..."
            sleep 5
        fi

        attempt=$((attempt + 1))
    done

    if [ "$success" = false ]; then
        echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] ERROR: Failed to fetch r/${subreddit}"
        return 1
    fi

    return 0
}

# Main execution
echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] INFO: Starting Reddit data collection"

success_count=0
total_count=${#SUBREDDITS[@]}

for subreddit in "${SUBREDDITS[@]}"; do
    if fetch_subreddit "$subreddit"; then
        success_count=$((success_count + 1))
    fi
done

echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] INFO: Collection complete: ${success_count}/${total_count} successful"

if [ $success_count -lt $total_count ]; then
    exit 1
fi

exit 0
