# Instagram Reels to Google Drive Downloader

Automatically download Instagram reels from public profiles and upload them to Google Drive with shareable links. Supports **5 separate niches** with scheduled processing and **Pinterest-ready CSV output**.

---

## 📋 Table of Contents

- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Step 1: Install Python Dependencies](#step-1-install-python-dependencies)
- [Step 2: Set Up Google Drive API](#step-2-set-up-google-drive-api)
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

- ✅ **5 Separate Niches** - Organize different content categories
- ✅ **Scheduled Processing** - 1-hour delay between niches (configurable)
- ✅ **Pinterest-Ready CSV** - Direct upload format with title, description, hashtags
- ✅ Download reels from **public** Instagram profiles
- ✅ Automatic upload to Google Drive with **direct download links**
- ✅ **Folder caching** - Reduces API calls by 50%+
- ✅ **Text normalization** - Cleans weird Unicode, emojis from titles
- ✅ **Failure logging** - Track failed posts for retry
- ✅ Track processed posts (skip duplicates on re-run)
- ✅ Sequential processing for stability (no rate limits)
- ✅ Automatic retry on failures

---

## 📦 Prerequisites

- **Python 3.8+** installed ([Download Python](https://www.python.org/downloads/))
- **Google Account** for Google Drive
- **Internet connection**

### Verify Python Installation

Open terminal/command prompt and run:

```bash
python --version
```

You should see `Python 3.x.x`. If not, install Python first.

---

## Step 1: Install Python Dependencies

Open terminal in the project folder and run:

```bash
pip install instaloader pydrive
```

### Verify Installation

```bash
pip show instaloader pydrive
```

Both packages should be listed.

---

## Step 2: Set Up Google Drive API

This is the most important step. Follow carefully.

### 2.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Click **"Select a project"** (top-left) → **"New Project"**
4. Enter project name: `InstaToDrive`
5. Click **"Create"**
6. Wait for project creation, then select it

### 2.2 Enable Google Drive API

1. In the left sidebar, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google Drive API"**
3. Click on **"Google Drive API"**
4. Click **"Enable"**
5. Wait for it to enable

### 2.3 Configure OAuth Consent Screen

1. Go to **"APIs & Services"** → **"OAuth consent screen"**
2. Select **"External"** → Click **"Create"**
3. Fill in the required fields:
   - **App name**: `InstaToDrive`
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Click **"Save and Continue"**
5. On **Scopes** page, click **"Save and Continue"** (no changes needed)
6. On **Test users** page:
   - Click **"Add Users"**
   - Enter your Gmail address
   - Click **"Add"**
7. Click **"Save and Continue"**
8. Click **"Back to Dashboard"**

### 2.4 Create OAuth Credentials

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"+ Create Credentials"** → **"OAuth client ID"**
3. Select **Application type**: **"Desktop app"**
4. Enter name: `InstaToDrive Desktop`
5. Click **"Create"**
6. A popup appears with your credentials
7. Click **"Download JSON"**
8. **Rename** the downloaded file to exactly: `client_secrets.json`
9. **Move** this file to your project folder (same folder as `main.py`)

### 2.5 Verify File Location

Your project folder should now have:

```
instaToDrive/
├── main.py
├── client_secrets.json   ← Must be here!
└── links.txt             ← Create this next
```

---

## Step 3: Create Project Files

### 3.1 Niche Links Files (5 Files)

The script uses **5 separate niche files** for different content categories:

| File | Purpose |
|------|---------|
| `links_niche1.txt` | Niche 1 Instagram profiles (e.g., Fitness) |
| `links_niche2.txt` | Niche 2 Instagram profiles (e.g., Food) |
| `links_niche3.txt` | Niche 3 Instagram profiles (e.g., Travel) |
| `links_niche4.txt` | Niche 4 Instagram profiles (e.g., Fashion) |
| `links_niche5.txt` | Niche 5 Instagram profiles (e.g., DIY) |

Each file should contain Instagram profile URLs (one per line):

```
https://www.instagram.com/username1
https://www.instagram.com/username2
https://instagram.com/username3
```

**Important:**
- Only use **public** profiles (not private accounts)
- Use the profile URL, not individual post URLs
- One URL per line
- Lines starting with `#` are comments (ignored)
- Leave files empty or delete them to skip that niche

### 3.2 Verify Project Structure

Your folder should look like this:

```
instaToDrive/
├── main.py
├── client_secrets.json
├── links_niche1.txt      ← Niche 1 profiles
├── links_niche2.txt      ← Niche 2 profiles
├── links_niche3.txt      ← Niche 3 profiles
├── links_niche4.txt      ← Niche 4 profiles
├── links_niche5.txt      ← Niche 5 profiles
└── README.md
```

---

## Step 4: Configure the Script

Open `main.py` and review these settings:

### Niche Configuration

Each niche has its own settings in the `NICHES` dictionary:

```python
NICHES = {
    "niche1": {
        "links_file": "links_niche1.txt",
        "output_csv": "reels_niche1.csv",
        "processed_file": "processed_niche1.txt",
        "failed_file": "failed_niche1.txt",
        "drive_folder": "niche1_reels",  # Google Drive folder name
    },
    # ... niche2 through niche5
}
```

### Timing Configuration

```python
NICHE_DELAY_HOURS = 1  # Wait 1 hour between each niche
```

### Optional: Enable Instagram Login

Recommended for better rate limits:

```python
USE_LOGIN = True
USERNAME = "your_burner_account"  # Use a burner account!
PASSWORD = "your_password"
```

⚠️ **Warning**: Use a burner Instagram account with no posting activity.

---

## Step 5: Run the Script

### 5.1 Open Terminal in Project Folder

**Windows:**
- Navigate to project folder in File Explorer
- Click address bar, type `cmd`, press Enter

**Or use VS Code:**
- Open folder in VS Code
- Press `` Ctrl+` `` to open terminal

### 5.2 Run the Script

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

### 5.3 First Run - Google Authentication

1. A browser window will open automatically
2. Sign in with your Google account
3. You may see "This app isn't verified" warning:
   - Click **"Advanced"**
   - Click **"Go to InstaToDrive (unsafe)"**
4. Click **"Continue"** to grant permissions
5. Close the browser tab when you see "Authentication successful"
6. Return to the terminal - the script will continue

### 5.4 Watch the Progress

The script will:
1. ✅ Authenticate with Google Drive
2. ✅ Read Instagram profiles from `links.txt`
3. ✅ Fetch all video posts from each profile
4. ✅ Download each video
5. ✅ Upload to Google Drive
6. ✅ Generate shareable link
7. ✅ Save to CSV
8. ✅ Delete local file
9. ✅ Move to next video

You'll see output like:
```
############################################################
INSTAGRAM TO DRIVE - MULTI-NICHE PROCESSOR
Processing 5 niches
Delay between niches: 1 hour(s)
############################################################

[1/5] Starting niche1 at 2026-01-02 10:00:00
============================================================
PROCESSING NICHE: niche1
Links file: links_niche1.txt
Drive folder: niche1_reels
Output CSV: reels_niche1.csv
============================================================
Fetching posts from @fitness_account1...

[1/10] Processing fitness_account1/ABC123
[001] fitness_account1/001_fitness_account1_ABC123.mp4 -> https://drive.usercontent.google.com/download?id=xxx

Completed niche1: 10 videos processed
⏰ Waiting 1 hour(s) before processing niche2...
Next niche will start at: 2026-01-02 11:00:00
```

---

## 🎯 Multi-Niche System

### How It Works

1. **5 Separate Niches** - Each niche has its own input/output files
2. **Scheduled Processing** - 1-hour delay between niches (avoids rate limits)
3. **Separate Tracking** - Each niche tracks processed posts independently
4. **Niche-Based Folders** - All videos from a niche go to one Drive folder

### File Structure Per Niche

| Niche | Input | Output CSV | Processed | Failed | Drive Folder |
|-------|-------|-----------|-----------|--------|--------------|
| niche1 | `links_niche1.txt` | `reels_niche1.csv` | `processed_niche1.txt` | `failed_niche1.txt` | `niche1_reels` |
| niche2 | `links_niche2.txt` | `reels_niche2.csv` | `processed_niche2.txt` | `failed_niche2.txt` | `niche2_reels` |
| niche3 | `links_niche3.txt` | `reels_niche3.csv` | `processed_niche3.txt` | `failed_niche3.txt` | `niche3_reels` |
| niche4 | `links_niche4.txt` | `reels_niche4.csv` | `processed_niche4.txt` | `failed_niche4.txt` | `niche4_reels` |
| niche5 | `links_niche5.txt` | `reels_niche5.csv` | `processed_niche5.txt` | `failed_niche5.txt` | `niche5_reels` |

### Command Line Options

| Command | Description |
|---------|-------------|
| `python main.py` | Process all niches with 1-hour delay |
| `python main.py --no-delay` | Process all niches immediately (testing) |
| `python main.py --niche=niche1` | Process single niche only |
| `python main.py --help` | Show help message |

---

## 📁 Output Files

After running, you'll have these files **per niche**:

| File | Description |
|------|-------------|
| `reels_niche1.csv` | Pinterest-ready CSV for niche 1 |
| `processed_niche1.txt` | Processed post IDs (prevents re-downloading) |
| `failed_niche1.txt` | Failed posts with error messages |
| `credentials.json` | Auto-generated Google auth token (don't delete) |

### CSV Format (Pinterest-Ready)

The CSV includes both tracking columns and Pinterest columns:

```csv
No.,Username,Video Title,Drive Folder,Filename,Drive Link,title,description,link,board,media_url
1,fitness_user,Great workout video,niche1_reels,001_fitness_user_ABC123.mp4,https://drive.usercontent.google.com/download?id=xxx,Great workout video,#fitness #workout #viral #trending,,,https://drive.usercontent.google.com/download?id=xxx
```

| Column | Description |
|--------|-------------|
| `No.` | Video number (resets per niche) |
| `Username` | Instagram username |
| `Video Title` | Cleaned caption (max 100 chars) |
| `Drive Folder` | Niche folder name |
| `Filename` | File in Drive (e.g., `001_user_ABC123.mp4`) |
| `Drive Link` | Direct download URL |
| `title` | Pinterest title (emoji-free, max 100 chars) |
| `description` | Overflow text + hashtags |
| `link` | Empty (for Pinterest) |
| `board` | Empty (fill in for Pinterest) |
| `media_url` | Direct download URL for Pinterest |

### Google Drive Structure

Videos are organized by niche:
```
My Drive/
├── niche1_reels/
│   ├── 001_fitness_user_ABC123.mp4
│   └── 002_fitness_user_DEF456.mp4
├── niche2_reels/
│   └── 001_food_account_GHI789.mp4
└── niche3_reels/
    └── ...
```

---

## ⚙️ Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `USE_LOGIN` | `True` | Login to Instagram (recommended) |
| `USERNAME` | `""` | Instagram username (burner account) |
| `PASSWORD` | `""` | Instagram password |
| `NICHE_DELAY_HOURS` | `1` | Hours to wait between niches |
| `RETRIES` | `3` | Retry attempts per failed download |
| `DEFAULT_HASHTAGS` | `"#viral #trending..."` | Hashtags added to Pinterest description |

### Customizing Niches

Edit the `NICHES` dictionary in `main.py` to:
- Rename niches (e.g., `"fitness"` instead of `"niche1"`)
- Change Drive folder names
- Use different file names

---

## 🔧 Troubleshooting

### Error: `No module named 'instaloader'`

**Solution:** Install dependencies
```bash
pip install instaloader pydrive
```

### Error: `client_secrets.json not found`

**Solution:** 
- Make sure you completed [Step 2.4](#24-create-oauth-credentials)
- File must be named exactly `client_secrets.json`
- File must be in the same folder as `main.py`

### Error: `FileNotFoundError: links.txt`

**Solution:** Create `links.txt` file with Instagram profile URLs

### Error: `Profile not found` or `404`

**Solution:**
- Check the username is correct
- Ensure the profile is **public**, not private
- Remove any trailing slashes or spaces from URLs

### Error: `Too many requests` / `429 Error`

**Solution:**
- Instagram is rate-limiting you
- Wait 1-2 hours before running again
- Reduce `THREADS` to `2` or `3`
- Consider enabling login for better rate limits

### Error: `Login required`

**Solution:**
- The profile might be private
- Some content requires login
- Enable `USE_LOGIN = True` with your credentials

### Browser doesn't open for Google Auth

**Solution:**
- Check your default browser settings
- Try running in a regular terminal (not VS Code)
- Manually open the URL shown in terminal

### Google Auth: "This app isn't verified"

**This is normal for personal projects.**

**Solution:**
1. Click **"Advanced"**
2. Click **"Go to InstaToDrive (unsafe)"**
3. Continue with authentication

### Videos not uploading to Drive

**Solution:**
- Check your Google Drive storage quota
- Verify `client_secrets.json` is valid
- Delete `credentials.json` and re-authenticate

### Script runs but no videos downloaded

**Solution:**
- Verify profiles in `links.txt` have video posts
- Check if posts are already in `processed_posts.txt`
- Delete `processed_posts.txt` to re-process all videos

---

## ❓ FAQ

### Q: Do I need an Instagram account?

**A:** No, for public profiles. Yes, for private profiles or to avoid rate limits.

### Q: Is this safe for my Instagram account?

**A:** Without login = no risk. With login = small risk of temporary blocks if you download too much.

### Q: How many videos can I download?

**A:** No hard limit, but Instagram may rate-limit you. Recommended: < 100 videos per hour without login.

### Q: Can I download from private profiles?

**A:** Only if you login AND follow that private account.

### Q: Where are videos stored in Google Drive?

**A:** In folders named `{username}_reels` in your Drive root.

### Q: Can I run this again to get new videos?

**A:** Yes! The script tracks processed videos and only downloads new ones.

### Q: How do I reset and re-download everything?

**A:** Delete `processed_posts.txt` and run again.

### Q: Can I change the Google Drive folder location?

**A:** Modify the `upload_to_drive` function in `main.py` to specify a parent folder ID.

---

## 📝 Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Run `pip install instaloader pydrive`
- [ ] Create Google Cloud project
- [ ] Enable Google Drive API
- [ ] Configure OAuth consent screen
- [ ] Create OAuth credentials (Desktop app)
- [ ] Download and rename to `client_secrets.json`
- [ ] Place `client_secrets.json` in project folder
- [ ] Create `links.txt` with Instagram profile URLs
- [ ] Run `python main.py`
- [ ] Complete Google authentication in browser
- [ ] Check `reels_drive_links.csv` for results

---

## 🆘 Still Having Issues?

1. Double-check every step in this guide
2. Ensure all file names are exact (case-sensitive)
3. Try with a single profile first
4. Check terminal for specific error messages
5. Search the error message online

---

**Happy downloading! 🎬**
