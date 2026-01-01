import instaloader
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
import csv
import time
import random
import glob

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

# --- Files ---
LINKS_FILE = "links.txt"
OUTPUT_CSV = "reels_drive_links.csv"
PROCESSED_FILE = "processed_posts.txt"
RETRIES = 3
THREADS = 1  # Sequential processing - safer for Drive API

# Ensure processed posts tracking file exists
if not os.path.exists(PROCESSED_FILE):
    open(PROCESSED_FILE, "w").close()

with open(PROCESSED_FILE, "r") as f:
    processed_posts = set(line.strip() for line in f if line.strip())

# Initialize CSV with headers if it doesn't exist
if not os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["No.", "Username", "Video Title", "Drive Folder", "Filename", "Drive Link"])

# Read profile links
with open(LINKS_FILE, "r") as f:
    links = [line.strip() for line in f if line.strip()]

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
def process_post(args):
    username, post = args
    if post.shortcode in processed_posts:
        return

    # Get video number
    video_number = get_next_video_number()
    
    target_folder = f"{username}_reels"
    drive_folder = f"{username}_reels"
    os.makedirs(target_folder, exist_ok=True)

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
            title = post.title if post.title else post.caption or ""
            # Truncate title if too long
            if len(title) > 100:
                title = title[:100] + "..."
            
            with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    video_number,           # No.
                    username,               # Username
                    title.replace('\n', ' '),  # Video Title (single line)
                    drive_folder,           # Drive Folder
                    drive_filename,         # Filename in Drive
                    drive_link              # Drive Link
                ])

            # Mark as processed
            with open(PROCESSED_FILE, "a") as f:
                f.write(post.shortcode + "\n")

            # Delete local file
            if os.path.exists(local_file):
                os.remove(local_file)

            print(f"[{video_number:03d}] {username}/{drive_filename} -> {drive_link}")
            break  # success, exit retry loop

        except Exception as e:
            print(f"[{video_number:03d}] Attempt {attempt+1} failed for {post.shortcode}: {e}")
            time.sleep(2)  # small delay before retry

# --- Collect all video posts ---
all_videos = []
for link in links:
    username = link.rstrip("/").split("/")[-1]
    profile = instaloader.Profile.from_username(L.context, username)
    for post in profile.get_posts():
        if post.is_video and post.shortcode not in processed_posts:
            all_videos.append((username, post))

# --- Process sequentially (safer for Drive API) ---
print(f"Processing {len(all_videos)} videos sequentially...")
for i, video_args in enumerate(all_videos, 1):
    print(f"\n[{i}/{len(all_videos)}] Processing {video_args[0]}/{video_args[1].shortcode}")
    process_post(video_args)
