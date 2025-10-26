#!/bin/bash

# Simple Reddit data fetcher for git scraping
# This script fetches Reddit data using curl with minimal dependencies

# Configuration
SUBREDDITS=("macapps")
DATA_DIR="data"
DATE=$(date -u +%Y-%m-%d)
USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Function to try different Reddit endpoints
fetch_subreddit() {
    local subreddit=$1
    local output_dir="${DATA_DIR}/${subreddit}"
    local output_file="${output_dir}/${subreddit}_${DATE}.json"

    echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] INFO: Fetching r/${subreddit}"

    # Create directory if it doesn't exist
    mkdir -p "$output_dir"

    # Try multiple approaches
    local urls=(
        "https://old.reddit.com/r/${subreddit}.json"
        "https://www.reddit.com/r/${subreddit}.json"
        "https://api.reddit.com/r/${subreddit}"
    )

    local success=false

    for url in "${urls[@]}"; do
        echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] INFO: Trying ${url}"

        # Add random delay to avoid rate limiting
        sleep $((2 + RANDOM % 3))

        # Try with wget first (sometimes works better than curl)
        if command -v wget &> /dev/null; then
            if wget -q --timeout=30 \
                --header="User-Agent: ${USER_AGENT}" \
                --header="Accept: application/json, text/html" \
                --header="Accept-Language: en-US,en;q=0.9" \
                -O "$output_file" \
                "$url" 2>/dev/null; then

                if [ -s "$output_file" ] && jq empty "$output_file" 2>/dev/null; then
                    local file_size=$(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file" 2>/dev/null)
                    echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] INFO: Successfully fetched with wget (${file_size} bytes)"
                    success=true
                    break
                fi
            fi
        fi

        # Fallback to curl
        if curl -s -L --max-time 30 \
            -H "User-Agent: ${USER_AGENT}" \
            -H "Accept: application/json, text/html" \
            -H "Accept-Language: en-US,en;q=0.9" \
            -H "Accept-Encoding: gzip, deflate, br" \
            -H "DNT: 1" \
            -H "Connection: keep-alive" \
            -H "Upgrade-Insecure-Requests: 1" \
            -o "$output_file" \
            "$url" 2>/dev/null; then

            # Check if file is valid JSON and not empty
            if [ -s "$output_file" ] && jq empty "$output_file" 2>/dev/null; then
                local file_size=$(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file" 2>/dev/null)
                echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] INFO: Successfully fetched with curl (${file_size} bytes)"
                success=true
                break
            fi
        fi

        rm -f "$output_file"
    done

    if [ "$success" = false ]; then
        echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] ERROR: Failed to fetch r/${subreddit} from all sources"
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
