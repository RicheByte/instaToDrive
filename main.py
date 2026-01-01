import instaloader
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
import csv
import time
import random
import glob
import re
import unicodedata
from datetime import datetime, timedelta

# Simple counter for video numbering (sequential processing)
video_counter = 0

def get_next_video_number():
    global video_counter
    video_counter += 1
    return video_counter

# --- Drive Folder Cache ---
# Cache folder IDs to avoid repeated API calls
folder_id_cache = {}

def get_or_create_folder(drive, folder_name):
    """Get folder ID from cache or create folder if needed"""
    if folder_name in folder_id_cache:
        return folder_id_cache[folder_name]
    
    # Search for existing folder
    folder_list = drive.ListFile({
        'q': f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    }).GetList()
    
    if folder_list:
        folder_id = folder_list[0]['id']
    else:
        # Create new folder
        folder_metadata = {'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
        folder = drive.CreateFile(folder_metadata)
        folder.Upload()
        folder_id = folder['id']
    
    # Cache the folder ID
    folder_id_cache[folder_name] = folder_id
    return folder_id

# --- Google Drive Setup ---
gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # Opens browser to authenticate
drive = GoogleDrive(gauth)

# --- Instaloader Setup ---
# Login recommended for better rate limits and smoother pipeline
# Use a burner Instagram account with no posting activity
USE_LOGIN = True
USERNAME = "your_username"  # Fill with your burner account
PASSWORD = "your_password"  # Fill with your burner account password

L = instaloader.Instaloader(
    download_comments=False,
    download_geotags=False,
    save_metadata=False,
    post_metadata_txt_pattern=""
)

if USE_LOGIN:
    L.login(USERNAME, PASSWORD)
    print("Logged in to Instagram")
else:
    print("Running without Instagram login (public profiles only)")

# --- Files & Niche Configuration ---
# 5 niches with separate input/output files
NICHES = {
    "niche1": {
        "links_file": "links_niche1.txt",
        "output_csv": "reels_niche1.csv",
        "processed_file": "processed_niche1.txt",
        "failed_file": "failed_niche1.txt",
        "drive_folder": "niche1_reels",  # All videos from this niche go here
    },
    "niche2": {
        "links_file": "links_niche2.txt",
        "output_csv": "reels_niche2.csv",
        "processed_file": "processed_niche2.txt",
        "failed_file": "failed_niche2.txt",
        "drive_folder": "niche2_reels",
    },
    "niche3": {
        "links_file": "links_niche3.txt",
        "output_csv": "reels_niche3.csv",
        "processed_file": "processed_niche3.txt",
        "failed_file": "failed_niche3.txt",
        "drive_folder": "niche3_reels",
    },
    "niche4": {
        "links_file": "links_niche4.txt",
        "output_csv": "reels_niche4.csv",
        "processed_file": "processed_niche4.txt",
        "failed_file": "failed_niche4.txt",
        "drive_folder": "niche4_reels",
    },
    "niche5": {
        "links_file": "links_niche5.txt",
        "output_csv": "reels_niche5.csv",
        "processed_file": "processed_niche5.txt",
        "failed_file": "failed_niche5.txt",
        "drive_folder": "niche5_reels",
    },
}

# Time between processing each niche (in seconds)
NICHE_DELAY_HOURS = 1
NICHE_DELAY_SECONDS = NICHE_DELAY_HOURS * 3600

RETRIES = 3
THREADS = 1  # Sequential processing - safer for Drive API

# File initialization moved to process_niche() function

# --- Text Normalization ---
def normalize_text(text):
    """Clean up text: remove/replace weird characters, normalize Unicode, handle emojis"""
    if not text:
        return ""
    
    # Normalize Unicode (NFKC normalizes compatibility characters)
    text = unicodedata.normalize('NFKC', text)
    
    # Remove zero-width characters and other invisible Unicode
    text = re.sub(r'[\u200b-\u200f\u2028-\u202f\u205f-\u206f\ufeff]', '', text)
    
    # Replace multiple spaces/newlines with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove control characters (except newline for description)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Cc' or char == '\n')
    
    return text.strip()

def remove_emojis(text):
    """Remove emojis from text (optional - for cleaner titles)"""
    if not text:
        return ""
    
    # Emoji pattern covering most emoji ranges
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols extended-A
        "\U00002600-\U000026FF"  # misc symbols
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text).strip()

# --- Pinterest Hashtags ---
# Default hashtags for video content (customize as needed)
DEFAULT_HASHTAGS = "#viral #trending #reels #fyp #explore #video #content #instagood #instadaily #foryou"

def format_for_pinterest(caption, drive_link):
    """Format caption for Pinterest: title (max 100 chars), description (overflow + hashtags)"""
    caption = normalize_text(caption or "")
    
    # Extract existing hashtags from caption
    existing_hashtags = ' '.join([word for word in caption.split() if word.startswith('#')])
    # Remove hashtags from main text for cleaner title
    caption_no_tags = ' '.join([word for word in caption.split() if not word.startswith('#')]).strip()
    
    # Clean title (remove emojis for Pinterest compatibility)
    clean_title = remove_emojis(caption_no_tags)
    
    # Pinterest title: max 100 chars
    if len(clean_title) <= 100:
        pin_title = clean_title if clean_title else "Check out this video! 🔥"
        pin_description = ""
    else:
        # Split: first 100 chars to title, rest to description
        pin_title = clean_title[:100].rsplit(' ', 1)[0] + "..."  # Break at word boundary
        pin_description = clean_title[len(pin_title)-3:].strip()  # Overflow text
    
    # Add hashtags to description (keep emojis in description, they're fine there)
    all_hashtags = existing_hashtags + " " + DEFAULT_HASHTAGS if existing_hashtags else DEFAULT_HASHTAGS
    if pin_description:
        pin_description = pin_description + "\n\n" + all_hashtags
    else:
        pin_description = all_hashtags
    
    return pin_title, pin_description

# CSV initialization moved to process_niche() function

# Function to find actual video file (Instaloader may rename)
def find_video_file(target_folder, shortcode):
    """Find the actual video file, handling Instaloader's naming variations"""
    expected_file = os.path.join(target_folder, shortcode + ".mp4")
    if os.path.exists(expected_file):
        return expected_file
    
    # Scan folder for any .mp4 file containing the shortcode
    pattern = os.path.join(target_folder, f"*{shortcode}*.mp4")
    matches = glob.glob(pattern)
    if matches:
        return matches[0]
    
    # Fallback: find any recent .mp4 in the folder
    all_mp4 = glob.glob(os.path.join(target_folder, "*.mp4"))
    if all_mp4:
        # Return the most recently modified
        return max(all_mp4, key=os.path.getmtime)
    
    return None

# Function to upload to Drive with numbered filename
def upload_to_drive(local_file, drive_folder_name, video_number, username):
    # Use cached folder ID to reduce API calls
    folder_id = get_or_create_folder(drive, drive_folder_name)

    # Create numbered filename: 001_username_shortcode.mp4
    original_name = os.path.basename(local_file)
    shortcode = os.path.splitext(original_name)[0]
    numbered_filename = f"{video_number:03d}_{username}_{shortcode}.mp4"
    
    gfile = drive.CreateFile({'parents':[{'id': folder_id}], 'title': numbered_filename})
    gfile.SetContentFile(local_file)
    gfile.Upload()
    gfile.InsertPermission({'type': 'anyone', 'value': 'anyone', 'role': 'reader'})  # Make public
    
    # Use direct download link (more reliable for Pinterest ingestion)
    file_id = gfile['id']
    direct_link = f"https://drive.usercontent.google.com/download?id={file_id}"
    
    # Add pacing delay after upload (2-5 seconds)
    time.sleep(random.uniform(2, 5))
    
    return direct_link, numbered_filename

# Function to download + upload a single post with retries
def process_post(args, niche_config, processed_posts):
    username, post = args
    if post.shortcode in processed_posts:
        return

    # Get video number
    video_number = get_next_video_number()
    
    # Use niche-based Drive folder (not username-based)
    target_folder = f"{niche_config['drive_folder']}_local"  # Local temp folder
    drive_folder = niche_config['drive_folder']  # Drive folder name
    os.makedirs(target_folder, exist_ok=True)
    
    last_error = None  # Track last error for failure logging

    for attempt in range(RETRIES):
        try:
            # Download video
            L.download_post(post, target=target_folder)

            # Verify file exists before upload (Instaloader may rename)
            local_file = find_video_file(target_folder, post.shortcode)
            if local_file is None:
                raise FileNotFoundError(f"Video file not found for {post.shortcode}")

            # Upload to Drive with numbering
            drive_link, drive_filename = upload_to_drive(local_file, drive_folder, video_number, username)

            # === SUCCESS CONFIRMED - NOW WRITE CSV ===
            # Only write CSV after upload + permission success
            full_caption = post.title if post.title else post.caption or ""
            
            # Normalize and clean the title
            title = normalize_text(full_caption)
            if len(title) > 100:
                title = title[:100] + "..."
            
            # Pinterest formatted title and description
            pin_title, pin_description = format_for_pinterest(full_caption, drive_link)
            
            with open(niche_config['output_csv'], "a", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    # Original tracking columns
                    video_number,           # No.
                    username,               # Username
                    title,                  # Video Title (single line)
                    drive_folder,           # Drive Folder
                    drive_filename,         # Filename in Drive
                    drive_link,             # Drive Link
                    # Pinterest columns
                    pin_title,              # title (Pinterest)
                    pin_description,        # description (Pinterest) - overflow + hashtags
                    "",                     # link (empty)
                    "",                     # board (empty)
                    drive_link              # media_url (direct download link)
                ])

            # Mark as processed
            with open(niche_config['processed_file'], "a") as f:
                f.write(post.shortcode + "\n")

            # Delete local file
            if os.path.exists(local_file):
                os.remove(local_file)

            print(f"[{video_number:03d}] {username}/{drive_filename} -> {drive_link}")
            return  # success, exit function

        except Exception as e:
            last_error = str(e)
            print(f"[{video_number:03d}] Attempt {attempt+1} failed for {post.shortcode}: {e}")
            time.sleep(2)  # small delay before retry
    
    # === ALL RETRIES FAILED - LOG TO FAILED FILE ===
    print(f"[{video_number:03d}] FAILED permanently: {username}/{post.shortcode}")
    with open(niche_config['failed_file'], "a", encoding="utf-8") as f:
        f.write(f"{username},{post.shortcode},{last_error}\n")

def process_niche(niche_name, niche_config):
    """Process all videos for a single niche"""
    global video_counter
    video_counter = 0  # Reset counter for each niche
    
    print("\n" + "=" * 60)
    print(f"PROCESSING NICHE: {niche_name}")
    print(f"Links file: {niche_config['links_file']}")
    print(f"Drive folder: {niche_config['drive_folder']}")
    print(f"Output CSV: {niche_config['output_csv']}")
    print("=" * 60)
    
    # Check if links file exists
    if not os.path.exists(niche_config['links_file']):
        print(f"WARNING: {niche_config['links_file']} not found. Skipping niche.")
        return 0
    
    # Ensure tracking files exist
    if not os.path.exists(niche_config['processed_file']):
        open(niche_config['processed_file'], "w").close()
    if not os.path.exists(niche_config['failed_file']):
        open(niche_config['failed_file'], "w").close()
    
    # Load processed posts for this niche
    with open(niche_config['processed_file'], "r") as f:
        processed_posts = set(line.strip() for line in f if line.strip())
    
    # Initialize CSV with headers if it doesn't exist
    if not os.path.exists(niche_config['output_csv']):
        with open(niche_config['output_csv'], "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "No.", "Username", "Video Title", "Drive Folder", "Filename", "Drive Link",
                "title", "description", "link", "board", "media_url"
            ])
    
    # Read profile links for this niche
    with open(niche_config['links_file'], "r") as f:
        links = [line.strip() for line in f if line.strip()]
    
    if not links:
        print(f"No links found in {niche_config['links_file']}. Skipping.")
        return 0
    
    # Collect all video posts for this niche
    all_videos = []
    for link in links:
        try:
            username = link.rstrip("/").split("/")[-1]
            print(f"Fetching posts from @{username}...")
            profile = instaloader.Profile.from_username(L.context, username)
            for post in profile.get_posts():
                if post.is_video and post.shortcode not in processed_posts:
                    all_videos.append((username, post))
        except Exception as e:
            print(f"Error fetching profile {link}: {e}")
    
    if not all_videos:
        print(f"No new videos to process for {niche_name}.")
        return 0
    
    # Process videos sequentially
    print(f"\nProcessing {len(all_videos)} videos for {niche_name}...")
    for i, video_args in enumerate(all_videos, 1):
        print(f"\n[{i}/{len(all_videos)}] Processing {video_args[0]}/{video_args[1].shortcode}")
        process_post(video_args, niche_config, processed_posts)
    
    return len(all_videos)


def run_all_niches(with_delay=True):
    """Run all niches with optional 1-hour delay between each"""
    niche_list = list(NICHES.items())
    total_niches = len(niche_list)
    
    print("\n" + "#" * 60)
    print("INSTAGRAM TO DRIVE - MULTI-NICHE PROCESSOR")
    print(f"Processing {total_niches} niches")
    if with_delay:
        print(f"Delay between niches: {NICHE_DELAY_HOURS} hour(s)")
    print("#" * 60)
    
    for idx, (niche_name, niche_config) in enumerate(niche_list):
        # Calculate and display timing
        start_time = datetime.now()
        print(f"\n[{idx+1}/{total_niches}] Starting {niche_name} at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Process this niche
        videos_processed = process_niche(niche_name, niche_config)
        
        end_time = datetime.now()
        print(f"\nCompleted {niche_name}: {videos_processed} videos processed")
        print(f"Finished at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Wait before next niche (except for the last one)
        if with_delay and idx < total_niches - 1:
            next_niche = niche_list[idx + 1][0]
            next_start = datetime.now() + timedelta(seconds=NICHE_DELAY_SECONDS)
            print(f"\n⏰ Waiting {NICHE_DELAY_HOURS} hour(s) before processing {next_niche}...")
            print(f"Next niche will start at: {next_start.strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(NICHE_DELAY_SECONDS)
    
    print("\n" + "#" * 60)
    print("ALL NICHES COMPLETED!")
    print("#" * 60)


# --- Main Entry Point ---
if __name__ == "__main__":
    import sys
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg == "--no-delay":
            # Process all niches without delay (for testing)
            print("Running without delay between niches...")
            run_all_niches(with_delay=False)
        
        elif arg.startswith("--niche="):
            # Process single niche: python main.py --niche=niche1
            niche_name = arg.split("=")[1]
            if niche_name in NICHES:
                process_niche(niche_name, NICHES[niche_name])
            else:
                print(f"Unknown niche: {niche_name}")
                print(f"Available niches: {', '.join(NICHES.keys())}")
        
        elif arg == "--help":
            print("Usage:")
            print("  python main.py              - Process all niches with 1-hour delay")
            print("  python main.py --no-delay   - Process all niches without delay")
            print("  python main.py --niche=X    - Process single niche (niche1-niche5)")
            print("  python main.py --help       - Show this help")
        
        else:
            print(f"Unknown argument: {arg}")
            print("Use --help for usage information.")
    
    else:
        # Default: process all niches with delay
        run_all_niches(with_delay=True)
