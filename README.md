# Instagram Reels to Google Drive Downloader

Automatically download Instagram reels from public profiles and upload them to Google Drive with shareable links.

---

## 📋 Table of Contents

- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Step 1: Install Python Dependencies](#step-1-install-python-dependencies)
- [Step 2: Set Up Google Drive API](#step-2-set-up-google-drive-api)
- [Step 3: Create Project Files](#step-3-create-project-files)
- [Step 4: Configure the Script](#step-4-configure-the-script)
- [Step 5: Run the Script](#step-5-run-the-script)
- [Output Files](#-output-files)
- [Configuration Options](#-configuration-options)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)

---

## ✨ Features

- ✅ Download reels from **public** Instagram profiles (no login required)
- ✅ Automatic upload to Google Drive
- ✅ Generate public shareable links
- ✅ Track processed posts (skip duplicates on re-run)
- ✅ Export video titles and Drive links to CSV
- ✅ Multi-threaded processing for speed
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

### 3.1 Create `links.txt`

Create a file named `links.txt` in the project folder.

Add Instagram profile URLs (one per line):

```
https://www.instagram.com/username1
https://www.instagram.com/username2
https://instagram.com/username3
```

**Important:**
- Only use **public** profiles (not private accounts)
- Use the profile URL, not individual post URLs
- One URL per line
- No trailing spaces

### 3.2 Verify Project Structure

Your folder should look like this:

```
instaToDrive/
├── main.py
├── client_secrets.json
├── links.txt
└── README.md (optional)
```

---

## Step 4: Configure the Script

Open `main.py` and review these settings:

### Basic Settings (Usually No Changes Needed)

```python
USE_LOGIN = False  # Keep False for public profiles
```

### Optional: Adjust Performance

```python
THREADS = 6    # Number of parallel downloads (reduce if getting errors)
RETRIES = 3    # Number of retry attempts per video
```

### Optional: Enable Instagram Login

Only if you need to:
- Access more content
- Reduce rate limiting
- Access private profiles you follow

```python
USE_LOGIN = True
USERNAME = "your_instagram_username"
PASSWORD = "your_instagram_password"
```

⚠️ **Warning**: Using login may risk your Instagram account being flagged.

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
python main.py
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
Running without Instagram login (public profiles only)
Processed ABC123 -> https://drive.google.com/file/d/xxx/view
Processed DEF456 -> https://drive.google.com/file/d/yyy/view
```

---

## 📁 Output Files

After running, you'll have:

| File | Description |
|------|-------------|
| `reels_drive_links.csv` | CSV with video titles and Google Drive links |
| `processed_posts.txt` | List of processed post IDs (prevents re-downloading) |
| `credentials.json` | Auto-generated Google auth token (don't delete) |

### CSV Format

```csv
"Video Title or Caption","https://drive.google.com/file/d/xxx/view"
"Another Video","https://drive.google.com/file/d/yyy/view"
```

### Google Drive Structure

Videos are organized in folders by username:
```
My Drive/
├── username1_reels/
│   ├── video1.mp4
│   └── video2.mp4
└── username2_reels/
    └── video1.mp4
```

---

## ⚙️ Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `USE_LOGIN` | `False` | Set `True` to login to Instagram |
| `USERNAME` | `""` | Instagram username (if login enabled) |
| `PASSWORD` | `""` | Instagram password (if login enabled) |
| `THREADS` | `6` | Parallel download threads |
| `RETRIES` | `3` | Retry attempts per failed download |
| `LINKS_FILE` | `links.txt` | File containing profile URLs |
| `OUTPUT_CSV` | `reels_drive_links.csv` | Output CSV filename |
| `PROCESSED_FILE` | `processed_posts.txt` | Tracking file for processed posts |

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
