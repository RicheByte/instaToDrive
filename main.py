import instaloader
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from multiprocessing import Pool
import os
import csv
import time
import threading

# Thread-safe counter for video numbering
video_counter = 0
counter_lock = threading.Lock()

def get_next_video_number():
    global video_counter
    with counter_lock:
        video_counter += 1
        return video_counter

# --- Google Drive Setup ---
gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # Opens browser to authenticate
drive = GoogleDrive(gauth)

# --- Instaloader Setup ---
# Set to True and fill credentials if you want to login (better rate limits, access to more content)
# Set to False to use without login (public profiles only, stricter rate limits)
USE_LOGIN = False
USERNAME = "your_username"  # Only needed if USE_LOGIN = True
PASSWORD = "your_password"  # Only needed if USE_LOGIN = True

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
THREADS = 6

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

# Function to upload to Drive with numbered filename
def upload_to_drive(local_file, drive_folder_name, video_number, username):
    folder_list = drive.ListFile({'q': f"title='{drive_folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
    if folder_list:
        folder_id = folder_list[0]['id']
    else:
        folder_metadata = {'title': drive_folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
        folder = drive.CreateFile(folder_metadata)
        folder.Upload()
        folder_id = folder['id']

    # Create numbered filename: 001_username_shortcode.mp4
    original_name = os.path.basename(local_file)
    shortcode = os.path.splitext(original_name)[0]
    numbered_filename = f"{video_number:03d}_{username}_{shortcode}.mp4"
    
    gfile = drive.CreateFile({'parents':[{'id': folder_id}], 'title': numbered_filename})
    gfile.SetContentFile(local_file)
    gfile.Upload()
    gfile.InsertPermission({'type': 'anyone', 'value': 'anyone', 'role': 'reader'})  # Make public
    return gfile['alternateLink'], numbered_filename

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
    local_file = os.path.join(target_folder, post.shortcode + ".mp4")  # default filename

    for attempt in range(RETRIES):
        try:
            # Fresh Instaloader for safety in multi-threading
            L_thread = instaloader.Instaloader(
                download_comments=False,
                download_geotags=False,
                save_metadata=False,
                post_metadata_txt_pattern=""
            )
            
            if USE_LOGIN:
                L_thread.login(USERNAME, PASSWORD)

            # Download video
            L_thread.download_post(post, target=target_folder)

            # Upload to Drive with numbering
            drive_link, drive_filename = upload_to_drive(local_file, drive_folder, video_number, username)

            # Save to CSV with clear numbering and path info
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

# --- Process in parallel ---
with Pool(THREADS) as p:
    p.map(process_post, all_videos)
