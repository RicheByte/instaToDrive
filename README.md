# Instagram Reels to Cloudflare R2 Uploader

Automatically download Instagram reels from public profiles and upload them to **Cloudflare R2** (S3-compatible storage) with direct public links. Supports **5 separate niches** with scheduled processing and **Pinterest-ready CSV output**.

---

## 📋 Table of Contents

- [Features](#-features)
- [What Changed: Google Drive → Cloudflare R2](#-what-changed-google-drive--cloudflare-r2)
- [Prerequisites](#-prerequisites)
- [Step 1: Install Python Dependencies](#step-1-install-python-dependencies)
- [Step 2: Set Up Cloudflare R2](#step-2-set-up-cloudflare-r2)
- [Step 3: Create Project Files](#step-3-create-project-files)
- [Step 4: Configure the Script](#step-4-configure-the-script)
- [Step 5: Run the Script](#step-5-run-the-script)
- [Multi-Niche System](#-multi-niche-system)
- [Output Files](#-output-files)
- [Configuration Options](#-configuration-options)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)

---

## ✨ Features

- ✅ **Cloudflare R2 Storage** - Free tier with 10GB storage, no egress fees
- ✅ **Direct Video URLs** - Raw `.mp4` links that work perfectly with Pinterest
- ✅ **5 Separate Niches** - Organize different content categories
- ✅ **Scheduled Processing** - 1-hour delay between niches (configurable)
- ✅ **Pinterest-Ready CSV** - Direct upload format with title, description, hashtags
- ✅ Download reels from **public** Instagram profiles
- ✅ **Text normalization** - Cleans weird Unicode, emojis from titles
- ✅ **Failure logging** - Track failed posts for retry
- ✅ Track processed posts (skip duplicates on re-run)
- ✅ Sequential processing for stability (no rate limits)
- ✅ Automatic retry on failures

---

## 🔄 What Changed: Google Drive → Cloudflare R2

### Why We Switched

| Issue with Google Drive | Solution with R2 |
|------------------------|------------------|
| Wrapper links (`drive.google.com/...`) | Direct raw video URLs (`pub-xxx.r2.dev/video.mp4`) |
| Pinterest often rejects Drive links | Pinterest accepts R2 direct links perfectly |
| Requires OAuth authentication flow | Simple API key authentication |
| Complex folder creation API | No folders needed - uses path prefixes |
| Rate limits on permission changes | No permission management needed |

### What Was Changed in the Code

1. **Removed Google Drive dependencies:**
   - Deleted `pydrive` library imports
   - Removed `client_secrets.json` requirement
   - Removed OAuth browser authentication
   - Removed folder ID caching system

2. **Added Cloudflare R2 (via boto3):**
   - Uses `boto3` (AWS S3-compatible SDK)
   - Simple credential configuration
   - Direct public URL generation
   - Proper `Content-Type: video/mp4` for Pinterest

3. **New upload function:**
   - `upload_to_drive()` → `upload_to_r2()`
   - Returns direct public URLs like `https://pub-xxx.r2.dev/niche1_reels/001_user_ABC123.mp4`

---

## 📦 Prerequisites

- **Python 3.8+** installed ([Download Python](https://www.python.org/downloads/))
- **Cloudflare Account** (free) for R2 storage
- **Internet connection**

### Verify Python Installation

```bash
python --version
```

You should see `Python 3.x.x`.

---

## Step 1: Install Python Dependencies

Open terminal in the project folder and run:

```bash
pip install instaloader boto3
```

### Verify Installation

```bash
pip show instaloader boto3
```

Both packages should be listed.

> **Note:** We no longer need `pydrive` - it has been replaced with `boto3` for R2.

---

## Step 2: Set Up Cloudflare R2

### 2.1 Create a Cloudflare Account

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Sign up for a free account (or sign in)

### 2.2 Enable R2 Storage

1. In the Cloudflare dashboard sidebar, click **"R2 Object Storage"**
2. If prompted, add a payment method (required for R2, but free tier has no charges)
3. Click **"Create bucket"**

### 2.3 Create Your Bucket

1. **Bucket name:** `pinterest-reels` (or your preferred name)
2. **Location:** Choose closest to you (or leave as automatic)
3. Click **"Create bucket"**

### 2.4 Enable Public Access

1. Click on your new bucket (`pinterest-reels`)
2. Go to **"Settings"** tab
3. Find **"Public access"** section
4. Click **"Allow Access"**
5. Choose **"R2.dev subdomain"**
6. Click **"Allow Access"** to confirm
7. **Copy the public URL** - it looks like: `https://pub-xxxxxxxxxxxxxxxx.r2.dev`

> ⚠️ **Save this URL!** You'll need it for configuration.

### 2.5 Create API Credentials

1. Go back to **R2 Overview** (click "R2" in sidebar)
2. Click **"Manage R2 API Tokens"** (on the right side)
3. Click **"Create API token"**
4. Configure the token:
   - **Token name:** `pinterest-reels-uploader`
   - **Permissions:** Select **"Object Read & Write"**
   - **Specify bucket(s):** Select your `pinterest-reels` bucket
5. Click **"Create API Token"**
6. **Copy and save these values immediately:**
   - **Access Key ID** (looks like: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
   - **Secret Access Key** (looks like: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

> ⚠️ **Important:** The Secret Access Key is only shown once! Save it securely.

### 2.6 Get Your Account ID

1. In Cloudflare dashboard, look at the URL in your browser
2. It contains your Account ID: `https://dash.cloudflare.com/ACCOUNT_ID_HERE/...`
3. Or find it in **R2 Overview** → **Account ID** on the right sidebar

### Summary: What You Need

| Item | Example | Where to Find |
|------|---------|---------------|
| Account ID | `a1b2c3d4e5f6...` | Dashboard URL or R2 sidebar |
| Access Key ID | `xxxxxxxx...` | API token creation (step 2.5) |
| Secret Access Key | `xxxxxxxx...` | API token creation (step 2.5) |
| Bucket Name | `pinterest-reels` | What you named it (step 2.3) |
| Public Domain | `https://pub-abc123.r2.dev` | Bucket Settings → Public Access |

---

## Step 3: Create Project Files

### 3.1 Niche Links Files (5 Files)

Create these files with Instagram profile URLs (one per line):

| File | Purpose |
|------|---------|
| `links_niche1.txt` | Niche 1 profiles (e.g., Fitness) |
| `links_niche2.txt` | Niche 2 profiles (e.g., Food) |
| `links_niche3.txt` | Niche 3 profiles (e.g., Travel) |
| `links_niche4.txt` | Niche 4 profiles (e.g., Fashion) |
| `links_niche5.txt` | Niche 5 profiles (e.g., DIY) |

**Example `links_niche1.txt`:**
```
https://www.instagram.com/fitness_account1
https://www.instagram.com/fitness_account2
https://instagram.com/workout_videos
```

**Important:**
- Only use **public** profiles (not private accounts)
- Use the profile URL, not individual post URLs
- One URL per line
- Leave files empty to skip that niche

### 3.2 Project Structure

```
instaToDrive/
├── main.py                 # Main script (already configured for R2)
├── test_main.py            # Unit tests
├── links_niche1.txt        # Niche 1 profiles
├── links_niche2.txt        # Niche 2 profiles
├── links_niche3.txt        # Niche 3 profiles
├── links_niche4.txt        # Niche 4 profiles
├── links_niche5.txt        # Niche 5 profiles
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

> **Note:** No `client_secrets.json` needed anymore!

---

## Step 4: Configure the Script

Open `main.py` and update the **R2 Configuration** section (near the top):

```python
# --- Cloudflare R2 Configuration ---
R2_ACCOUNT_ID = "your_account_id"           # From step 2.6
R2_ACCESS_KEY = "your_access_key"           # From step 2.5
R2_SECRET_KEY = "your_secret_key"           # From step 2.5
R2_BUCKET_NAME = "pinterest-reels"          # From step 2.3
R2_PUBLIC_DOMAIN = "https://pub-xxxxxxxx.r2.dev"  # From step 2.4
```

### Example Configuration

```python
# --- Cloudflare R2 Configuration ---
R2_ACCOUNT_ID = "a1b2c3d4e5f67890abcdef1234567890"
R2_ACCESS_KEY = "abcdef1234567890abcdef1234567890"
R2_SECRET_KEY = "secret1234567890secret1234567890secret12"
R2_BUCKET_NAME = "pinterest-reels"
R2_PUBLIC_DOMAIN = "https://pub-abc123def456.r2.dev"
```

### Optional: Instagram Login

For better rate limits, enable login with a burner account:

```python
USE_LOGIN = True
USERNAME = "your_burner_account"  # Use a burner account!
PASSWORD = "your_password"
```

⚠️ **Warning:** Never use your main Instagram account.

---

## Step 5: Run the Script

### 5.1 Open Terminal in Project Folder

**Windows:**
- Navigate to project folder in File Explorer
- Click address bar, type `cmd`, press Enter

**Or use VS Code:**
- Open folder in VS Code
- Press `` Ctrl+` `` to open terminal

### 5.2 Run Commands

```bash
# Process all 5 niches with 1-hour delay between each
python main.py

# Process all niches without delay (for testing)
python main.py --no-delay

# Process a single niche only
python main.py --niche=niche1

# Show help
python main.py --help
```

### 5.3 Watch the Progress

```
############################################################
INSTAGRAM TO DRIVE - MULTI-NICHE PROCESSOR
Processing 5 niches
Delay between niches: 1 hour(s)
############################################################

[1/5] Starting niche1 at 2026-01-05 10:00:00
============================================================
PROCESSING NICHE: niche1
Links file: links_niche1.txt
Drive folder: niche1_reels
Output CSV: reels_niche1.csv
============================================================
Fetching posts from @fitness_account1...

[1/10] Processing fitness_account1/ABC123
[001] fitness_account1/001_fitness_account1_ABC123.mp4 -> https://pub-abc123.r2.dev/niche1_reels/001_fitness_account1_ABC123.mp4

Completed niche1: 10 videos processed
⏰ Waiting 1 hour(s) before processing niche2...
```

> **Note:** No browser authentication popup! R2 uses direct API credentials.

---

## 🎯 Multi-Niche System

### How It Works

1. **5 Separate Niches** - Each niche has its own input/output files
2. **Scheduled Processing** - 1-hour delay between niches (avoids rate limits)
3. **Separate Tracking** - Each niche tracks processed posts independently
4. **Niche-Based R2 Prefixes** - All videos from a niche share a folder prefix

### File Structure Per Niche

| Niche | Input | Output CSV | Processed | Failed | R2 Prefix |
|-------|-------|-----------|-----------|--------|-----------|
| niche1 | `links_niche1.txt` | `reels_niche1.csv` | `processed_niche1.txt` | `failed_niche1.txt` | `niche1_reels/` |
| niche2 | `links_niche2.txt` | `reels_niche2.csv` | `processed_niche2.txt` | `failed_niche2.txt` | `niche2_reels/` |
| niche3 | `links_niche3.txt` | `reels_niche3.csv` | `processed_niche3.txt` | `failed_niche3.txt` | `niche3_reels/` |
| niche4 | `links_niche4.txt` | `reels_niche4.csv` | `processed_niche4.txt` | `failed_niche4.txt` | `niche4_reels/` |
| niche5 | `links_niche5.txt` | `reels_niche5.csv` | `processed_niche5.txt` | `failed_niche5.txt` | `niche5_reels/` |

### R2 Storage Structure

```
pinterest-reels (bucket)/
├── niche1_reels/
│   ├── 001_fitness_user_ABC123.mp4
│   └── 002_fitness_user_DEF456.mp4
├── niche2_reels/
│   └── 001_food_account_GHI789.mp4
└── niche3_reels/
    └── ...
```

> **Note:** R2 doesn't have real folders - these are key prefixes that organize files.

---

## 📁 Output Files

### Generated Files Per Niche

| File | Description |
|------|-------------|
| `reels_niche1.csv` | Pinterest-ready CSV with video links |
| `processed_niche1.txt` | Processed post IDs (prevents re-downloading) |
| `failed_niche1.txt` | Failed posts with error messages |

### CSV Format (Pinterest-Ready)

```csv
No.,Username,Video Title,Drive Folder,Filename,Drive Link,title,description,link,board,media_url
1,fitness_user,Great workout,niche1_reels,001_fitness_user_ABC123.mp4,https://pub-xxx.r2.dev/niche1_reels/001_fitness_user_ABC123.mp4,Great workout,#fitness #viral #trending,,,https://pub-xxx.r2.dev/niche1_reels/001_fitness_user_ABC123.mp4
```

| Column | Description |
|--------|-------------|
| `No.` | Video number (resets per niche) |
| `Username` | Instagram username |
| `Video Title` | Cleaned caption (max 100 chars) |
| `Drive Folder` | R2 prefix/folder name |
| `Filename` | File name (e.g., `001_user_ABC123.mp4`) |
| `Drive Link` | Direct R2 URL |
| `title` | Pinterest title (emoji-free, max 100 chars) |
| `description` | Overflow text + hashtags |
| `link` | Empty (for Pinterest) |
| `board` | Empty (fill in for Pinterest) |
| `media_url` | Direct R2 URL for Pinterest |

### Using with Pinterest Bulk Upload

1. Open your `reels_niche1.csv`
2. Add your board name to the `board` column
3. Upload to Pinterest's bulk create tool
4. Videos load directly from R2 - no redirects!

---

## ⚙️ Configuration Options

### R2 Configuration (Required)

| Option | Description |
|--------|-------------|
| `R2_ACCOUNT_ID` | Your Cloudflare account ID |
| `R2_ACCESS_KEY` | R2 API access key |
| `R2_SECRET_KEY` | R2 API secret key |
| `R2_BUCKET_NAME` | Your bucket name |
| `R2_PUBLIC_DOMAIN` | Public URL from bucket settings |

### Script Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `USE_LOGIN` | `True` | Login to Instagram (recommended) |
| `USERNAME` | `""` | Instagram username (burner account) |
| `PASSWORD` | `""` | Instagram password |
| `NICHE_DELAY_HOURS` | `1` | Hours between niches |
| `RETRIES` | `3` | Retry attempts per failed download |
| `DEFAULT_HASHTAGS` | `"#viral #trending..."` | Added to Pinterest description |

---

## 🔧 Troubleshooting

### Error: `No module named 'boto3'`

**Solution:** Install dependencies
```bash
pip install boto3
```

### Error: `NoCredentialsError` or `InvalidAccessKeyId`

**Solution:**
- Double-check your `R2_ACCESS_KEY` and `R2_SECRET_KEY`
- Ensure there are no extra spaces in the values
- Verify the API token has "Object Read & Write" permission

### Error: `NoSuchBucket`

**Solution:**
- Verify `R2_BUCKET_NAME` matches exactly (case-sensitive)
- Ensure the bucket exists in your R2 dashboard

### Error: `AccessDenied` on upload

**Solution:**
- Check API token permissions include your bucket
- Verify the token has "Object Read & Write" access

### Videos upload but URLs don't work

**Solution:**
- Ensure public access is enabled (Step 2.4)
- Verify `R2_PUBLIC_DOMAIN` starts with `https://pub-`
- Check the bucket settings show "Public access: Allowed"

### Error: `Profile not found` / `404`

**Solution:**
- Check the username is correct
- Ensure the profile is **public**, not private
- Remove trailing slashes from URLs

### Error: `Too many requests` / `429 Error`

**Solution:**
- Instagram is rate-limiting you
- Wait 1-2 hours before running again
- Enable login for better rate limits

### R2 Upload Failed: Connection Error

**Solution:**
- Check your internet connection
- Verify `R2_ACCOUNT_ID` is correct
- The endpoint URL format should be: `https://{ACCOUNT_ID}.r2.cloudflarestorage.com`

---

## ❓ FAQ

### Q: Why Cloudflare R2 instead of Google Drive?

**A:** R2 provides direct video URLs (`pub-xxx.r2.dev/video.mp4`) that work perfectly with Pinterest. Google Drive wrapper links often get rejected by Pinterest's bulk uploader.

### Q: Is R2 really free?

**A:** Yes! R2 free tier includes:
- 10 GB storage per month
- 1 million Class A operations (uploads)
- 10 million Class B operations (downloads)
- **Zero egress fees** (unlike AWS S3)

For most users, you'll never exceed the free tier.

### Q: Do I need a credit card for Cloudflare?

**A:** Yes, Cloudflare requires a payment method for R2, but you won't be charged within free tier limits.

### Q: Can I still use Google Drive?

**A:** The old Google Drive code has been removed. If you need Drive support, you can revert to an earlier version of the code.

### Q: How do I check my R2 usage?

**A:** In Cloudflare dashboard → R2 → Your bucket → Metrics

### Q: Can I delete videos from R2?

**A:** Yes, in Cloudflare dashboard → R2 → Your bucket → Browse files

### Q: Where are my videos stored?

**A:** In your Cloudflare R2 bucket, organized by niche prefix:
- `niche1_reels/001_user_ABC.mp4`
- `niche2_reels/001_user_XYZ.mp4`

### Q: How do I reset and re-download everything?

**A:** Delete the `processed_niche*.txt` files and run again.

---

## 🧪 Running Tests

The project includes unit tests to verify the R2 integration:

```bash
python test_main.py
```

Expected output:
```
============================================================
Running Static Tests for main.py
============================================================
...
Ran 73 tests in 0.2s
OK
============================================================
Tests run: 73
Failures: 0
Errors: 0
============================================================
```

---

## 📝 Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Run `pip install instaloader boto3`
- [ ] Create Cloudflare account
- [ ] Create R2 bucket (`pinterest-reels`)
- [ ] Enable public access on bucket
- [ ] Create R2 API token with read/write access
- [ ] Copy Account ID, Access Key, Secret Key, Public Domain
- [ ] Update `main.py` with your R2 credentials
- [ ] Create `links_niche1.txt` (etc.) with Instagram URLs
- [ ] Run `python main.py --niche=niche1` to test
- [ ] Check `reels_niche1.csv` for Pinterest-ready links

---

## 🔐 Security Notes

1. **Never commit credentials** - Add `main.py` to `.gitignore` if it contains secrets
2. **Use environment variables** - For production, store R2 keys in env vars
3. **Limit API token scope** - Only grant access to your specific bucket
4. **Use a burner Instagram account** - Never use your main account

### Using Environment Variables (Recommended)

Instead of hardcoding credentials, use:

```python
import os

R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID")
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")
R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME", "pinterest-reels")
R2_PUBLIC_DOMAIN = os.environ.get("R2_PUBLIC_DOMAIN")
```

Then set environment variables before running:

**Windows (PowerShell):**
```powershell
$env:R2_ACCOUNT_ID = "your_account_id"
$env:R2_ACCESS_KEY = "your_access_key"
$env:R2_SECRET_KEY = "your_secret_key"
$env:R2_PUBLIC_DOMAIN = "https://pub-xxx.r2.dev"
python main.py
```

**Linux/Mac:**
```bash
export R2_ACCOUNT_ID="your_account_id"
export R2_ACCESS_KEY="your_access_key"
export R2_SECRET_KEY="your_secret_key"
export R2_PUBLIC_DOMAIN="https://pub-xxx.r2.dev"
python main.py
```

---

## 🆘 Still Having Issues?

1. Double-check your R2 credentials (Account ID, keys, bucket name)
2. Verify public access is enabled on your bucket
3. Test with a single niche first: `python main.py --niche=niche1`
4. Check the terminal for specific error messages
5. Run the tests: `python test_main.py`

---

**Happy uploading! 🎬**
