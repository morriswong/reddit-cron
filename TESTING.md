# Testing Instructions

## Local Testing Results ✓

**Script Validation:**
- ✓ Python script syntax is valid
- ✓ Shell script syntax is valid
- ✓ Workflow YAML syntax is valid

**Local Network Test:**
- ✗ Reddit is blocking requests from this environment (expected)
- This is normal - Reddit often blocks data center IPs
- GitHub Actions typically has better success rates

## How to Test the Workflow on GitHub

### Method 1: Manual Trigger (Recommended)

1. Go to your repository on GitHub:
   `https://github.com/morriswong/reddit-cron`

2. Click the **"Actions"** tab at the top

3. In the left sidebar, click **"Reddit Data Collection"**

4. On the right side, click the **"Run workflow"** button

5. Select the branch: `claude/reddit-daily-scraper-011CUVP5AAeLzyotQoRKW42M`

6. Click the green **"Run workflow"** button

7. Wait 30-60 seconds and refresh the page

8. Click on the workflow run to see the logs

### What to Look For in the Logs

**Success indicators:**
- ✓ "Successfully fetched r/macapps"
- ✓ "New data files found"
- ✓ "Changes committed and pushed successfully"
- Check the "Workflow Summary" section at the bottom

**If it fails:**
- Check which method was tried (Shell or Python)
- Look for error messages in the logs
- The workflow will show which step failed

### Method 2: Wait for Scheduled Run

The workflow is scheduled to run daily at **12:00 UTC**.

Convert to your timezone:
- PST: 4:00 AM
- EST: 7:00 AM
- GMT: 12:00 PM

### Verifying Success

After a successful run, you should see:

1. New commit in the repository with message: "📊 Update Reddit data - YYYY-MM-DD"

2. New files in `data/macapps/`:
   - `macapps_YYYY-MM-DD.json` (raw data)
   - `macapps_YYYY-MM-DD_processed.json` (cleaned data)
   - `macapps_YYYY-MM-DD_readable.txt` (human-readable)

## Troubleshooting

### If Both Methods Fail

Reddit may be blocking GitHub Actions IPs temporarily. Solutions:

1. **Add User Agent Secret** (optional):
   - Go to Settings → Secrets and variables → Actions
   - Add a new secret: `REDDIT_USER_AGENT`
   - Value: `MyApp/1.0 (by /u/YOUR_REDDIT_USERNAME)`

2. **Wait and Retry**:
   - Sometimes Reddit's rate limiting is temporary
   - The workflow will retry automatically tomorrow

3. **Check Reddit's Status**:
   - Visit https://www.redditstatus.com/
   - Ensure Reddit's API is operational

### Checking Logs

The workflow summary will show:
- Date of execution
- Which method succeeded (Shell or Python)
- Whether data was collected
- List of created files

## Expected Behavior

**First run:** Should create new data files and commit them

**Subsequent runs:**
- Will create new files with today's date
- Old files remain (this is intentional for historical tracking)
- Each day adds 3 new files per subreddit

## Need Help?

If the workflow fails:
1. Share the workflow logs
2. Check if there are any error messages
3. Verify repository permissions (Actions needs write access)
