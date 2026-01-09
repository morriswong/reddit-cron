# How to Add or Remove Subreddits

Managing your subreddit list is super easy! Just edit `config.yml`.

## 📝 Quick Guide

### 1. Open `config.yml`

```yaml
subreddits:
  - macapps
  # - iosapps
  # - androidapps
```

### 2. Add a Subreddit

**Remove the `#` to enable:**

```yaml
subreddits:
  - macapps
  - iosapps          # ← Enabled! (no # at start)
  # - androidapps    # ← Still disabled
```

**Or add a new line:**

```yaml
subreddits:
  - macapps
  - iosapps
  - programming      # ← New subreddit added!
```

### 3. Remove a Subreddit

**Option 1: Add `#` to disable:**

```yaml
subreddits:
  # - macapps       # ← Disabled with #
  - iosapps
```

**Option 2: Delete the line:**

```yaml
subreddits:
  - iosapps         # macapps line deleted
```

### 4. Commit and Push

```bash
git add config.yml
git commit -m "Add iosapps subreddit"
git push
```

The workflow will automatically pick up the changes on the next run!

---

## 🎯 Examples

### Example 1: Track Multiple Tech Subreddits

```yaml
subreddits:
  - programming
  - webdev
  - javascript
  - python
  - golang
  - rust
```

### Example 2: Track App Development

```yaml
subreddits:
  - macapps
  - iosapps
  - androidapps
  - SideProject
  - IndieDev
```

### Example 3: Track Tech News

```yaml
subreddits:
  - technology
  - gadgets
  - apple
  - startups
  - tech
```

### Example 4: Mix of Different Topics

```yaml
subreddits:
  - macapps         # Mac apps
  - programming     # Programming discussions
  - datascience     # Data science
  - AskReddit       # General discussions
```

---

## 📋 Config File Reference

### Full Format

```yaml
# Comments start with #
# Lines with # are ignored

subreddits:
  - subreddit_name_here    # This will be scraped
  # - disabled_subreddit   # This won't be scraped (has # at start)
```

### Rules

- ✅ **Use lowercase** subreddit names
- ✅ **No r/** prefix needed (just `macapps`, not `r/macapps`)
- ✅ **One per line** with a dash (`-`) before it
- ✅ **Comments** can be added after `#`
- ❌ **No spaces** in subreddit names

### Valid Examples

```yaml
✅ - macapps
✅ - programming
✅ - webdev          # My favorite subreddit
✅ - datascience
```

### Invalid Examples

```yaml
❌ - r/macapps       # Don't include r/
❌ - mac apps        # No spaces in names
❌ macapps           # Missing dash (-)
❌   - macapps       # Too many spaces before dash
```

---

## 🚀 Testing Your Changes

### Option 1: Test Locally

```bash
pip install pyyaml
python collect_reddit_hybrid.py
```

### Option 2: Check the Workflow

After pushing changes:
1. Go to GitHub Actions
2. Run the workflow manually
3. Check the logs to see which subreddits were loaded

Look for this in the logs:
```
📋 Loaded 3 subreddit(s) from config: macapps, iosapps, programming
```

---

## 📁 What Gets Created

For **each subreddit**, you get 3 files per day:

```
data/
├── macapps/
│   ├── macapps_2025-01-09.json
│   ├── macapps_2025-01-09_SUMMARY.txt
│   └── macapps_2025-01-09_TOP10.txt
├── iosapps/
│   ├── iosapps_2025-01-09.json
│   ├── iosapps_2025-01-09_SUMMARY.txt
│   └── iosapps_2025-01-09_TOP10.txt
└── programming/
    ├── programming_2025-01-09.json
    ├── programming_2025-01-09_SUMMARY.txt
    └── programming_2025-01-09_TOP10.txt
```

---

## ⚙️ Advanced Usage

### Enable/Disable Without Deleting

Keep subreddits in your config but temporarily disable them:

```yaml
subreddits:
  - macapps          # Always track
  - iosapps          # Always track
  # - androidapps    # Temporarily disabled (just add # to re-enable later)
  # - programming    # Temporarily disabled
```

### Add Notes

```yaml
subreddits:
  - macapps          # For market research
  - SideProject      # Find collaboration opportunities
  - IndieDev         # Inspiration for projects
```

### Organize by Category

```yaml
subreddits:
  # Apps & Development
  - macapps
  - iosapps
  - androidapps

  # Programming Languages
  - python
  - javascript
  - golang

  # Communities
  - programming
  - webdev
  - datascience
```

---

## ⚠️ Important Notes

### Rate Limiting

- Each subreddit takes ~30-60 seconds to collect
- Don't add too many at once (recommend < 10)
- The script is polite and includes delays

### Best Practices

1. **Start small** - Add 1-3 subreddits first
2. **Test** - Run manually to make sure it works
3. **Monitor** - Check GitHub Actions for any failures
4. **Expand** - Gradually add more subreddits

### Troubleshooting

**Issue:** "No subreddits found in config"
- **Fix:** Make sure you have at least one line without `#`

**Issue:** "Failed to collect r/subreddit"
- **Fix:** Check if the subreddit name is correct (no typos)

**Issue:** YAML syntax error
- **Fix:** Check indentation and dash placement

---

## 🎉 Quick Start Examples

### Just Want Tech News?

```yaml
subreddits:
  - technology
  - programming
  - webdev
```

### Building Mac Apps?

```yaml
subreddits:
  - macapps
  - SwiftUI
  - iOSProgramming
  - macOSBeta
```

### Indie Developer?

```yaml
subreddits:
  - SideProject
  - IndieDev
  - startups
  - Entrepreneur
```

---

**That's it!** Just edit `config.yml` and the scraper automatically picks up your changes. 🚀
