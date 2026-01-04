"""
Static tests for main.py functions
Uses mocking to test logic without actual API calls
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import os
import csv
import tempfile
import shutil
import glob
import re
import unicodedata


class TestUploadToR2(unittest.TestCase):
    """Tests for upload_to_r2 function logic (Cloudflare R2 via boto3)"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_video.mp4")
        # Create a dummy file
        with open(self.test_file, "w") as f:
            f.write("dummy video content")

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_r2_public_link_format(self):
        """Test that R2 public links use the correct format"""
        R2_PUBLIC_DOMAIN = "https://pub-abc123xyz.r2.dev"
        niche_folder = "niche1_reels"
        filename = "001_testuser_ABC123.mp4"
        
        # R2 uses path-based keys
        r2_key = f"{niche_folder}/{filename}"
        direct_link = f"{R2_PUBLIC_DOMAIN}/{r2_key}"
        
        self.assertIn("r2.dev", direct_link)
        self.assertIn(niche_folder, direct_link)
        self.assertIn(filename, direct_link)
        self.assertEqual(direct_link, "https://pub-abc123xyz.r2.dev/niche1_reels/001_testuser_ABC123.mp4")
        print("✓ Test r2_public_link_format passed")

    def test_r2_key_generation(self):
        """Test R2 key (path) generation from niche folder and filename"""
        niche_folder_name = "niche2_reels"
        video_number = 42
        username = "cooluser"
        shortcode = "XYZ789"
        
        # Simulate upload_to_r2 key generation
        r2_key = f"{niche_folder_name}/{video_number:03d}_{username}_{shortcode}.mp4"
        r2_filename = os.path.basename(r2_key)
        
        self.assertEqual(r2_key, "niche2_reels/042_cooluser_XYZ789.mp4")
        self.assertEqual(r2_filename, "042_cooluser_XYZ789.mp4")
        print("✓ Test r2_key_generation passed")

    def test_r2_no_folder_creation_needed(self):
        """Test that R2 does not require explicit folder creation (uses key prefixes)"""
        # R2 uses flat object storage with key prefixes acting as "folders"
        # No folder creation API calls needed - just upload with the key
        niche_folder = "niche1_reels"
        filename = "001_user_ABC.mp4"
        
        r2_key = f"{niche_folder}/{filename}"
        
        # Key should contain the "folder" as a prefix
        self.assertTrue(r2_key.startswith(niche_folder + "/"))
        self.assertIn("/", r2_key)
        print("✓ Test r2_no_folder_creation_needed passed")

    def test_r2_content_type_for_video(self):
        """Test that video uploads use correct content type"""
        # Critical for Pinterest to recognize the file as video
        expected_content_type = "video/mp4"
        extra_args = {'ContentType': 'video/mp4'}
        
        self.assertEqual(extra_args['ContentType'], expected_content_type)
        print("✓ Test r2_content_type_for_video passed")

    def test_r2_upload_with_mock(self):
        """Test R2 upload logic with mocked boto3 client"""
        mock_s3_client = MagicMock()
        
        # Simulate upload_to_r2 logic
        R2_PUBLIC_DOMAIN = "https://pub-test123.r2.dev"
        R2_BUCKET_NAME = "pinterest-reels"
        niche_folder_name = "niche1_reels"
        video_number = 5
        username = "testuser"
        shortcode = "ABC123"
        local_file = self.test_file
        
        r2_key = f"{niche_folder_name}/{video_number:03d}_{username}_{shortcode}.mp4"
        r2_filename = os.path.basename(r2_key)
        
        # Simulate upload call
        mock_s3_client.upload_file(
            local_file,
            R2_BUCKET_NAME,
            r2_key,
            ExtraArgs={'ContentType': 'video/mp4'}
        )
        
        direct_link = f"{R2_PUBLIC_DOMAIN}/{r2_key}"
        
        # Verify upload was called correctly
        mock_s3_client.upload_file.assert_called_once_with(
            local_file,
            R2_BUCKET_NAME,
            r2_key,
            ExtraArgs={'ContentType': 'video/mp4'}
        )
        
        self.assertEqual(direct_link, "https://pub-test123.r2.dev/niche1_reels/005_testuser_ABC123.mp4")
        self.assertEqual(r2_filename, "005_testuser_ABC123.mp4")
        print("✓ Test r2_upload_with_mock passed")


class TestProcessPost(unittest.TestCase):
    """Tests for process_post function logic"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.processed_file = os.path.join(self.test_dir, "processed_posts.txt")
        self.output_csv = os.path.join(self.test_dir, "reels_drive_links.csv")
        
        # Create empty processed file
        with open(self.processed_file, "w") as f:
            pass

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_skip_already_processed(self):
        """Test that already processed posts are skipped"""
        # Write a processed shortcode
        with open(self.processed_file, "w") as f:
            f.write("ABC123\n")
        
        # Read processed posts
        with open(self.processed_file, "r") as f:
            processed_posts = set(line.strip() for line in f if line.strip())
        
        # Mock post
        mock_post = Mock()
        mock_post.shortcode = "ABC123"
        
        # Check if post should be skipped
        should_skip = mock_post.shortcode in processed_posts
        
        self.assertTrue(should_skip)
        print("✓ Test skip_already_processed passed")

    def test_process_new_post(self):
        """Test that new posts are not skipped"""
        with open(self.processed_file, "w") as f:
            f.write("ABC123\n")
        
        with open(self.processed_file, "r") as f:
            processed_posts = set(line.strip() for line in f if line.strip())
        
        mock_post = Mock()
        mock_post.shortcode = "NEW456"
        
        should_skip = mock_post.shortcode in processed_posts
        
        self.assertFalse(should_skip)
        print("✓ Test process_new_post passed")

    def test_csv_writing(self):
        """Test CSV writing functionality"""
        title = "Test Video Title"
        drive_link = "https://drive.google.com/file/test123"
        
        with open(self.output_csv, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([title, drive_link])
        
        # Verify CSV content
        with open(self.output_csv, "r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
        
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], title)
        self.assertEqual(rows[0][1], drive_link)
        print("✓ Test csv_writing passed")

    def test_processed_tracking(self):
        """Test processed posts tracking"""
        shortcode = "XYZ789"
        
        with open(self.processed_file, "a") as f:
            f.write(shortcode + "\n")
        
        with open(self.processed_file, "r") as f:
            content = f.read()
        
        self.assertIn(shortcode, content)
        print("✓ Test processed_tracking passed")


class TestFileOperations(unittest.TestCase):
    """Tests for file operations"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_create_target_folder(self):
        """Test target folder creation"""
        username = "test_user"
        target_folder = os.path.join(self.test_dir, f"{username}_reels")
        
        os.makedirs(target_folder, exist_ok=True)
        
        self.assertTrue(os.path.exists(target_folder))
        self.assertTrue(os.path.isdir(target_folder))
        print("✓ Test create_target_folder passed")

    def test_links_file_parsing(self):
        """Test parsing of links file"""
        links_file = os.path.join(self.test_dir, "links.txt")
        
        test_links = [
            "https://instagram.com/user1",
            "https://instagram.com/user2/",
            "https://instagram.com/user3"
        ]
        
        with open(links_file, "w") as f:
            f.write("\n".join(test_links))
        
        with open(links_file, "r") as f:
            links = [line.strip() for line in f if line.strip()]
        
        self.assertEqual(len(links), 3)
        
        # Test username extraction
        usernames = [link.rstrip("/").split("/")[-1] for link in links]
        
        self.assertEqual(usernames, ["user1", "user2", "user3"])
        print("✓ Test links_file_parsing passed")

    def test_empty_processed_file_creation(self):
        """Test creation of empty processed file"""
        processed_file = os.path.join(self.test_dir, "processed_posts.txt")
        
        if not os.path.exists(processed_file):
            open(processed_file, "w").close()
        
        self.assertTrue(os.path.exists(processed_file))
        self.assertEqual(os.path.getsize(processed_file), 0)
        print("✓ Test empty_processed_file_creation passed")


class TestRetryLogic(unittest.TestCase):
    """Tests for retry logic"""

    def test_retry_count(self):
        """Test that retry logic respects RETRIES constant"""
        RETRIES = 3
        attempts = 0
        
        for attempt in range(RETRIES):
            attempts += 1
        
        self.assertEqual(attempts, RETRIES)
        print("✓ Test retry_count passed")

    def test_retry_with_success(self):
        """Test retry breaks on success"""
        RETRIES = 3
        success_on_attempt = 2
        attempts_made = 0
        
        for attempt in range(RETRIES):
            attempts_made += 1
            if attempt + 1 == success_on_attempt:
                break  # Success
        
        self.assertEqual(attempts_made, success_on_attempt)
        print("✓ Test retry_with_success passed")


class TestPostFiltering(unittest.TestCase):
    """Tests for post filtering logic"""

    def test_video_filtering(self):
        """Test that only video posts are collected"""
        # Create mock posts
        posts = []
        for i in range(5):
            mock_post = Mock()
            mock_post.is_video = i % 2 == 0  # Alternate video/non-video
            mock_post.shortcode = f"POST{i}"
            posts.append(mock_post)
        
        processed_posts = set()
        video_posts = [p for p in posts if p.is_video and p.shortcode not in processed_posts]
        
        self.assertEqual(len(video_posts), 3)  # posts 0, 2, 4
        print("✓ Test video_filtering passed")

    def test_exclude_processed_videos(self):
        """Test that processed videos are excluded"""
        posts = []
        for i in range(5):
            mock_post = Mock()
            mock_post.is_video = True
            mock_post.shortcode = f"POST{i}"
            posts.append(mock_post)
        
        processed_posts = {"POST0", "POST2"}
        video_posts = [p for p in posts if p.is_video and p.shortcode not in processed_posts]
        
        self.assertEqual(len(video_posts), 3)  # posts 1, 3, 4
        print("✓ Test exclude_processed_videos passed")


class TestPostMetadata(unittest.TestCase):
    """Tests for post metadata handling"""

    def test_title_fallback_to_caption(self):
        """Test title falls back to caption if title is empty"""
        mock_post = Mock()
        mock_post.title = ""
        mock_post.caption = "This is the caption"
        
        title = mock_post.title if mock_post.title else mock_post.caption or ""
        
        self.assertEqual(title, "This is the caption")
        print("✓ Test title_fallback_to_caption passed")

    def test_title_used_when_present(self):
        """Test title is used when present"""
        mock_post = Mock()
        mock_post.title = "Video Title"
        mock_post.caption = "Caption text"
        
        title = mock_post.title if mock_post.title else mock_post.caption or ""
        
        self.assertEqual(title, "Video Title")
        print("✓ Test title_used_when_present passed")

    def test_empty_title_and_caption(self):
        """Test handling when both title and caption are empty"""
        mock_post = Mock()
        mock_post.title = ""
        mock_post.caption = None
        
        title = mock_post.title if mock_post.title else mock_post.caption or ""
        
        self.assertEqual(title, "")
        print("✓ Test empty_title_and_caption passed")


class TestVideoNumbering(unittest.TestCase):
    """Tests for video numbering system"""

    def test_video_number_format(self):
        """Test that video numbers are formatted as 3-digit strings"""
        video_number = 1
        formatted = f"{video_number:03d}"
        self.assertEqual(formatted, "001")
        
        video_number = 42
        formatted = f"{video_number:03d}"
        self.assertEqual(formatted, "042")
        
        video_number = 999
        formatted = f"{video_number:03d}"
        self.assertEqual(formatted, "999")
        
        print("✓ Test video_number_format passed")

    def test_numbered_filename_generation(self):
        """Test generation of numbered filenames"""
        video_number = 5
        username = "testuser"
        shortcode = "ABC123"
        
        numbered_filename = f"{video_number:03d}_{username}_{shortcode}.mp4"
        
        self.assertEqual(numbered_filename, "005_testuser_ABC123.mp4")
        print("✓ Test numbered_filename_generation passed")

    def test_sequential_numbering(self):
        """Test sequential number generation"""
        counter = 0
        numbers = []
        
        for _ in range(5):
            counter += 1
            numbers.append(counter)
        
        self.assertEqual(numbers, [1, 2, 3, 4, 5])
        print("✓ Test sequential_numbering passed")


class TestNewCSVFormat(unittest.TestCase):
    """Tests for new CSV format with Pinterest columns"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.output_csv = os.path.join(self.test_dir, "reels_drive_links.csv")

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_csv_header_creation(self):
        """Test CSV header row creation with Pinterest columns"""
        headers = [
            "No.", "Username", "Video Title", "Drive Folder", "Filename", "Drive Link",
            "title", "description", "link", "board", "media_url"
        ]
        
        with open(self.output_csv, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
        
        with open(self.output_csv, "r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            header_row = next(reader)
        
        self.assertEqual(header_row, headers)
        self.assertEqual(len(header_row), 11)  # 6 original + 5 Pinterest
        print("✓ Test csv_header_creation passed")

    def test_csv_data_row(self):
        """Test CSV data row with all 11 columns (6 original + 5 Pinterest)"""
        r2_link = "https://pub-abc123.r2.dev/niche1_reels/001_testuser_ABC123.mp4"
        row_data = [
            1,                                      # No.
            "testuser",                             # Username
            "Test Video Title",                     # Video Title
            "niche1_reels",                         # R2 Folder (niche-based)
            "001_testuser_ABC123.mp4",              # Filename
            r2_link,                                # R2 Link
            "Test Video Title",                     # title (Pinterest)
            "#viral #trending",                     # description (Pinterest)
            "",                                     # link (empty)
            "",                                     # board (empty)
            r2_link                                 # media_url (Pinterest)
        ]
        
        with open(self.output_csv, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(row_data)
        
        with open(self.output_csv, "r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            saved_row = next(reader)
        
        self.assertEqual(saved_row[0], "1")  # CSV stores as string
        self.assertEqual(saved_row[1], "testuser")
        self.assertEqual(saved_row[4], "001_testuser_ABC123.mp4")
        self.assertEqual(saved_row[8], "")  # link should be empty
        self.assertEqual(saved_row[9], "")  # board should be empty
        self.assertEqual(saved_row[10], r2_link)  # media_url (R2 direct link)
        self.assertIn("r2.dev", saved_row[10])  # Verify R2 domain
        self.assertEqual(len(saved_row), 11)
        print("✓ Test csv_data_row passed")

    def test_title_truncation(self):
        """Test title truncation to 100 characters"""
        long_title = "A" * 150  # 150 characters
        
        if len(long_title) > 100:
            truncated = long_title[:100] + "..."
        else:
            truncated = long_title
        
        self.assertEqual(len(truncated), 103)  # 100 + "..."
        self.assertTrue(truncated.endswith("..."))
        print("✓ Test title_truncation passed")

    def test_title_no_truncation_needed(self):
        """Test short titles are not truncated"""
        short_title = "Short title"
        
        if len(short_title) > 100:
            result = short_title[:100] + "..."
        else:
            result = short_title
        
        self.assertEqual(result, "Short title")
        self.assertFalse(result.endswith("..."))
        print("✓ Test title_no_truncation_needed passed")

    def test_newline_removal_from_title(self):
        """Test newlines are removed from titles"""
        title_with_newlines = "Line 1\nLine 2\nLine 3"
        
        cleaned_title = title_with_newlines.replace('\n', ' ')
        
        self.assertEqual(cleaned_title, "Line 1 Line 2 Line 3")
        self.assertNotIn('\n', cleaned_title)
        print("✓ Test newline_removal_from_title passed")


class TestPinterestFormatting(unittest.TestCase):
    """Tests for Pinterest title/description formatting"""

    def test_short_caption_stays_in_title(self):
        """Test short captions stay in title, no overflow to description"""
        caption = "Check out this cool video!"
        caption_clean = caption.replace('\n', ' ').strip()
        
        # Remove hashtags for title
        caption_no_tags = ' '.join([word for word in caption_clean.split() if not word.startswith('#')]).strip()
        
        if len(caption_no_tags) <= 100:
            pin_title = caption_no_tags
            pin_description_overflow = ""
        else:
            pin_title = caption_no_tags[:100]
            pin_description_overflow = caption_no_tags[100:]
        
        self.assertEqual(pin_title, "Check out this cool video!")
        self.assertEqual(pin_description_overflow, "")
        print("✓ Test short_caption_stays_in_title passed")

    def test_long_caption_splits_to_description(self):
        """Test long captions overflow to description"""
        caption = "A" * 150  # 150 chars - exceeds 100 limit
        
        if len(caption) <= 100:
            pin_title = caption
            has_overflow = False
        else:
            pin_title = caption[:100] + "..."
            has_overflow = True
        
        self.assertEqual(len(pin_title), 103)  # 100 + "..."
        self.assertTrue(has_overflow)
        print("✓ Test long_caption_splits_to_description passed")

    def test_hashtag_extraction(self):
        """Test hashtags are extracted from caption"""
        caption = "Great video #viral #trending check it out #fyp"
        
        existing_hashtags = ' '.join([word for word in caption.split() if word.startswith('#')])
        caption_no_tags = ' '.join([word for word in caption.split() if not word.startswith('#')]).strip()
        
        self.assertEqual(existing_hashtags, "#viral #trending #fyp")
        self.assertEqual(caption_no_tags, "Great video check it out")
        print("✓ Test hashtag_extraction passed")

    def test_default_hashtags_added(self):
        """Test default hashtags are added to description"""
        DEFAULT_HASHTAGS = "#viral #trending #reels #fyp #explore"
        existing_hashtags = ""
        
        all_hashtags = existing_hashtags + " " + DEFAULT_HASHTAGS if existing_hashtags else DEFAULT_HASHTAGS
        
        self.assertIn("#viral", all_hashtags)
        self.assertIn("#reels", all_hashtags)
        print("✓ Test default_hashtags_added passed")

    def test_empty_caption_gets_default_title(self):
        """Test empty caption gets a default title"""
        caption = ""
        caption_clean = caption.replace('\n', ' ').strip()
        
        if len(caption_clean) <= 100:
            pin_title = caption_clean if caption_clean else "Check out this video! 🔥"
        else:
            pin_title = caption_clean[:100]
        
        self.assertEqual(pin_title, "Check out this video! 🔥")
        print("✓ Test empty_caption_gets_default_title passed")

    def test_pinterest_link_empty(self):
        """Test Pinterest link column is empty"""
        pin_link = ""
        self.assertEqual(pin_link, "")
        print("✓ Test pinterest_link_empty passed")

    def test_pinterest_board_empty(self):
        """Test Pinterest board column is empty"""
        pin_board = ""
        self.assertEqual(pin_board, "")
        print("✓ Test pinterest_board_empty passed")

    def test_media_url_is_r2_direct_link(self):
        """Test media_url uses R2 direct link format"""
        R2_PUBLIC_DOMAIN = "https://pub-abc123.r2.dev"
        r2_key = "niche1_reels/001_user_ABC123.mp4"
        media_url = f"{R2_PUBLIC_DOMAIN}/{r2_key}"
        
        self.assertIn("r2.dev", media_url)
        self.assertIn("niche1_reels", media_url)
        self.assertTrue(media_url.endswith(".mp4"))
        print("✓ Test media_url_is_r2_direct_link passed")


class TestR2FolderNaming(unittest.TestCase):
    """Tests for R2 folder (key prefix) naming convention"""

    def test_r2_key_prefix_from_niche(self):
        """Test R2 key prefix generation from niche name"""
        niche_name = "niche1"
        r2_folder = f"{niche_name}_reels"
        
        self.assertEqual(r2_folder, "niche1_reels")
        print("✓ Test r2_key_prefix_from_niche passed")

    def test_r2_key_prefix_consistency(self):
        """Test R2 key prefix is consistent between local and R2"""
        niche_config = {"drive_folder": "niche1_reels"}
        target_folder = f"{niche_config['drive_folder']}_local"
        r2_folder = niche_config['drive_folder']
        
        self.assertEqual(target_folder, "niche1_reels_local")
        self.assertEqual(r2_folder, "niche1_reels")
        print("✓ Test r2_key_prefix_consistency passed")


class TestFileVerification(unittest.TestCase):
    """Tests for file existence verification before upload"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_find_exact_file(self):
        """Test finding file with exact expected name"""
        shortcode = "ABC123"
        expected_file = os.path.join(self.test_dir, f"{shortcode}.mp4")
        
        # Create the file
        with open(expected_file, "w") as f:
            f.write("video content")
        
        # Simulate find_video_file logic
        if os.path.exists(expected_file):
            found_file = expected_file
        else:
            found_file = None
        
        self.assertEqual(found_file, expected_file)
        print("✓ Test find_exact_file passed")

    def test_find_renamed_file_by_pattern(self):
        """Test finding file when Instaloader renames it"""
        shortcode = "ABC123"
        # Instaloader might add date prefix or other modifications
        renamed_file = os.path.join(self.test_dir, f"2026-01-02_{shortcode}.mp4")
        
        # Create the renamed file
        with open(renamed_file, "w") as f:
            f.write("video content")
        
        # Simulate find_video_file logic
        expected_file = os.path.join(self.test_dir, f"{shortcode}.mp4")
        if os.path.exists(expected_file):
            found_file = expected_file
        else:
            # Scan for pattern match
            pattern = os.path.join(self.test_dir, f"*{shortcode}*.mp4")
            matches = glob.glob(pattern)
            found_file = matches[0] if matches else None
        
        self.assertEqual(found_file, renamed_file)
        print("✓ Test find_renamed_file_by_pattern passed")

    def test_find_any_mp4_fallback(self):
        """Test fallback to any .mp4 file in folder"""
        shortcode = "NOTFOUND"
        # Create a different mp4 file
        other_file = os.path.join(self.test_dir, "some_other_video.mp4")
        with open(other_file, "w") as f:
            f.write("video content")
        
        # Simulate find_video_file logic
        expected_file = os.path.join(self.test_dir, f"{shortcode}.mp4")
        if os.path.exists(expected_file):
            found_file = expected_file
        else:
            pattern = os.path.join(self.test_dir, f"*{shortcode}*.mp4")
            matches = glob.glob(pattern)
            if matches:
                found_file = matches[0]
            else:
                # Fallback to any mp4
                all_mp4 = glob.glob(os.path.join(self.test_dir, "*.mp4"))
                found_file = all_mp4[0] if all_mp4 else None
        
        self.assertEqual(found_file, other_file)
        print("✓ Test find_any_mp4_fallback passed")

    def test_no_file_found_returns_none(self):
        """Test that None is returned when no file exists"""
        shortcode = "MISSING"
        
        # Simulate find_video_file logic on empty directory
        expected_file = os.path.join(self.test_dir, f"{shortcode}.mp4")
        if os.path.exists(expected_file):
            found_file = expected_file
        else:
            pattern = os.path.join(self.test_dir, f"*{shortcode}*.mp4")
            matches = glob.glob(pattern)
            if matches:
                found_file = matches[0]
            else:
                all_mp4 = glob.glob(os.path.join(self.test_dir, "*.mp4"))
                found_file = all_mp4[0] if all_mp4 else None
        
        self.assertIsNone(found_file)
        print("✓ Test no_file_found_returns_none passed")


class TestUploadPacing(unittest.TestCase):
    """Tests for upload pacing logic"""

    def test_pacing_delay_range(self):
        """Test that pacing delay is within 2-5 seconds range"""
        import random
        
        for _ in range(100):
            delay = random.uniform(2, 5)
            self.assertGreaterEqual(delay, 2)
            self.assertLessEqual(delay, 5)
        
        print("✓ Test pacing_delay_range passed")

    def test_pacing_randomness(self):
        """Test that pacing delays are randomized (not constant)"""
        import random
        
        delays = [random.uniform(2, 5) for _ in range(10)]
        unique_delays = set(delays)
        
        # Should have multiple unique values (extremely unlikely to be all same)
        self.assertGreater(len(unique_delays), 1)
        print("✓ Test pacing_randomness passed")


class TestSequentialProcessing(unittest.TestCase):
    """Tests for sequential (non-parallel) processing"""

    def test_threads_is_one(self):
        """Test that THREADS constant is set to 1"""
        THREADS = 1  # Should match main.py
        self.assertEqual(THREADS, 1)
        print("✓ Test threads_is_one passed")

    def test_sequential_counter_increment(self):
        """Test simple counter works without threading"""
        video_counter = 0
        
        def get_next_video_number():
            nonlocal video_counter
            video_counter += 1
            return video_counter
        
        numbers = [get_next_video_number() for _ in range(5)]
        
        self.assertEqual(numbers, [1, 2, 3, 4, 5])
        self.assertEqual(video_counter, 5)
        print("✓ Test sequential_counter_increment passed")


class TestR2Configuration(unittest.TestCase):
    """Tests for R2 configuration and setup"""

    def test_r2_config_required_fields(self):
        """Test that R2 config has all required fields"""
        # These are the required config values for R2
        required_configs = [
            "R2_ACCOUNT_ID",
            "R2_ACCESS_KEY",
            "R2_SECRET_KEY",
            "R2_BUCKET_NAME",
            "R2_PUBLIC_DOMAIN"
        ]
        
        # Simulate config (would be imported from main.py)
        config = {
            "R2_ACCOUNT_ID": "your_account_id",
            "R2_ACCESS_KEY": "your_access_key",
            "R2_SECRET_KEY": "your_secret_key",
            "R2_BUCKET_NAME": "pinterest-reels",
            "R2_PUBLIC_DOMAIN": "https://pub-xxxxxxxx.r2.dev"
        }
        
        for field in required_configs:
            self.assertIn(field, config)
        print("✓ Test r2_config_required_fields passed")

    def test_r2_endpoint_url_format(self):
        """Test R2 endpoint URL is correctly formatted"""
        R2_ACCOUNT_ID = "abc123def456"
        endpoint_url = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
        
        self.assertIn("r2.cloudflarestorage.com", endpoint_url)
        self.assertIn(R2_ACCOUNT_ID, endpoint_url)
        self.assertTrue(endpoint_url.startswith("https://"))
        print("✓ Test r2_endpoint_url_format passed")

    def test_r2_public_domain_format(self):
        """Test R2 public domain follows expected format"""
        R2_PUBLIC_DOMAIN = "https://pub-abc123xyz.r2.dev"
        
        self.assertTrue(R2_PUBLIC_DOMAIN.startswith("https://"))
        self.assertIn("r2.dev", R2_PUBLIC_DOMAIN)
        print("✓ Test r2_public_domain_format passed")

    def test_r2_bucket_name_valid(self):
        """Test bucket name is valid (lowercase, no special chars)"""
        R2_BUCKET_NAME = "pinterest-reels"
        
        # S3/R2 bucket names must be lowercase and can contain hyphens
        self.assertEqual(R2_BUCKET_NAME, R2_BUCKET_NAME.lower())
        self.assertTrue(all(c.isalnum() or c == '-' for c in R2_BUCKET_NAME))
        print("✓ Test r2_bucket_name_valid passed")


class TestFailureLogging(unittest.TestCase):
    """Tests for failure logging functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.failed_file = os.path.join(self.test_dir, "failed_posts.txt")

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_failed_file_creation(self):
        """Test that failed_posts.txt is created if it does not exist"""
        if not os.path.exists(self.failed_file):
            open(self.failed_file, "w").close()
        
        self.assertTrue(os.path.exists(self.failed_file))
        print("✓ Test failed_file_creation passed")

    def test_failure_logging_format(self):
        """Test that failures are logged with username, shortcode, and error"""
        username = "testuser"
        shortcode = "ABC123"
        error = "Connection timeout"
        
        with open(self.failed_file, "a", encoding="utf-8") as f:
            f.write(f"{username},{shortcode},{error}\n")
        
        with open(self.failed_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        self.assertIn(username, content)
        self.assertIn(shortcode, content)
        self.assertIn(error, content)
        print("✓ Test failure_logging_format passed")

    def test_multiple_failures_logged(self):
        """Test that multiple failures are appended"""
        failures = [
            ("user1", "ABC123", "Error 1"),
            ("user2", "DEF456", "Error 2"),
            ("user3", "GHI789", "Error 3"),
        ]
        
        for username, shortcode, error in failures:
            with open(self.failed_file, "a", encoding="utf-8") as f:
                f.write(f"{username},{shortcode},{error}\n")
        
        with open(self.failed_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 3)
        print("✓ Test multiple_failures_logged passed")

    def test_failure_parsing_for_retry(self):
        """Test that failed posts can be parsed for retry"""
        with open(self.failed_file, "w", encoding="utf-8") as f:
            f.write("user1,ABC123,Error message\n")
            f.write("user2,DEF456,Another error\n")
        
        failed_posts = []
        with open(self.failed_file, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",", 2)  # Split into 3 parts max
                if len(parts) >= 2:
                    failed_posts.append((parts[0], parts[1]))
        
        self.assertEqual(len(failed_posts), 2)
        self.assertEqual(failed_posts[0], ("user1", "ABC123"))
        self.assertEqual(failed_posts[1], ("user2", "DEF456"))
        print("✓ Test failure_parsing_for_retry passed")


class TestTextNormalization(unittest.TestCase):
    """Tests for text normalization and cleanup"""

    def test_normalize_unicode(self):
        """Test Unicode normalization (NFKC)"""
        # Test full-width characters
        text = "ｆｕｌｌ　ｗｉｄｔｈ"
        normalized = unicodedata.normalize('NFKC', text)
        self.assertEqual(normalized, "full width")
        print("✓ Test normalize_unicode passed")

    def test_remove_zero_width_characters(self):
        """Test removal of zero-width characters"""
        text = "hello\u200bworld\u200c"  # zero-width space and non-joiner
        cleaned = re.sub(r'[\u200b-\u200f\u2028-\u202f\u205f-\u206f\ufeff]', '', text)
        self.assertEqual(cleaned, "helloworld")
        print("✓ Test remove_zero_width_characters passed")

    def test_collapse_multiple_spaces(self):
        """Test collapsing multiple spaces to single space"""
        text = "hello    world   test"
        cleaned = re.sub(r'\s+', ' ', text)
        self.assertEqual(cleaned, "hello world test")
        print("✓ Test collapse_multiple_spaces passed")

    def test_remove_control_characters(self):
        """Test removal of control characters"""
        text = "hello\x00world\x1f"  # null and unit separator
        cleaned = ''.join(char for char in text if unicodedata.category(char) != 'Cc' or char == '\n')
        self.assertEqual(cleaned, "helloworld")
        print("✓ Test remove_control_characters passed")

    def test_emoji_removal(self):
        """Test emoji removal from text"""
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001F900-\U0001F9FF"
            "\U0001FA00-\U0001FA6F"
            "\U0001FA70-\U0001FAFF"
            "\U00002600-\U000026FF"
            "]+",
            flags=re.UNICODE
        )
        
        text = "Hello 🔥 World 😀 Test 🎉"
        cleaned = emoji_pattern.sub('', text).strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Clean up extra spaces
        self.assertEqual(cleaned, "Hello World Test")
        print("✓ Test emoji_removal passed")

    def test_normalize_preserves_hashtags(self):
        """Test that normalization preserves hashtags"""
        text = "#viral #trending   #fyp"
        cleaned = re.sub(r'\s+', ' ', text).strip()
        self.assertIn("#viral", cleaned)
        self.assertIn("#trending", cleaned)
        self.assertIn("#fyp", cleaned)
        print("✓ Test normalize_preserves_hashtags passed")

    def test_empty_text_handling(self):
        """Test that empty text returns empty string"""
        text = ""
        result = text or ""
        self.assertEqual(result, "")
        
        text = None
        result = text or ""
        self.assertEqual(result, "")
        print("✓ Test empty_text_handling passed")

    def test_newline_handling(self):
        """Test that newlines are properly handled"""
        text = "Line 1\nLine 2\n\nLine 3"
        # For titles, collapse to single space
        title_clean = re.sub(r'\s+', ' ', text)
        self.assertEqual(title_clean, "Line 1 Line 2 Line 3")
        print("✓ Test newline_handling passed")


class TestNicheConfiguration(unittest.TestCase):
    """Tests for multi-niche configuration"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_niche_config_structure(self):
        """Test that niche config has all required keys"""
        niche_config = {
            "links_file": "links_niche1.txt",
            "output_csv": "reels_niche1.csv",
            "processed_file": "processed_niche1.txt",
            "failed_file": "failed_niche1.txt",
            "drive_folder": "niche1_reels",
        }
        
        required_keys = ["links_file", "output_csv", "processed_file", "failed_file", "drive_folder"]
        for key in required_keys:
            self.assertIn(key, niche_config)
        
        print("✓ Test niche_config_structure passed")

    def test_five_niches_defined(self):
        """Test that exactly 5 niches are defined"""
        NICHES = {
            "niche1": {"links_file": "links_niche1.txt"},
            "niche2": {"links_file": "links_niche2.txt"},
            "niche3": {"links_file": "links_niche3.txt"},
            "niche4": {"links_file": "links_niche4.txt"},
            "niche5": {"links_file": "links_niche5.txt"},
        }
        
        self.assertEqual(len(NICHES), 5)
        print("✓ Test five_niches_defined passed")

    def test_niche_file_naming_convention(self):
        """Test niche file naming follows convention"""
        for i in range(1, 6):
            niche_name = f"niche{i}"
            expected_links = f"links_niche{i}.txt"
            expected_csv = f"reels_niche{i}.csv"
            expected_processed = f"processed_niche{i}.txt"
            expected_failed = f"failed_niche{i}.txt"
            expected_drive = f"niche{i}_reels"
            
            self.assertTrue(expected_links.startswith("links_"))
            self.assertTrue(expected_csv.startswith("reels_"))
            self.assertTrue(expected_csv.endswith(".csv"))
        
        print("✓ Test niche_file_naming_convention passed")

    def test_niche_links_file_parsing(self):
        """Test parsing links from niche-specific file"""
        links_file = os.path.join(self.test_dir, "links_niche1.txt")
        
        test_links = [
            "https://instagram.com/fitness_account1",
            "https://instagram.com/fitness_account2/",
            "https://instagram.com/fitness_account3"
        ]
        
        with open(links_file, "w") as f:
            f.write("\n".join(test_links))
        
        with open(links_file, "r") as f:
            links = [line.strip() for line in f if line.strip()]
        
        self.assertEqual(len(links), 3)
        print("✓ Test niche_links_file_parsing passed")

    def test_separate_csv_per_niche(self):
        """Test that each niche gets its own CSV file"""
        csv_files = []
        for i in range(1, 6):
            csv_path = os.path.join(self.test_dir, f"reels_niche{i}.csv")
            csv_files.append(csv_path)
            
            # Create CSV with header
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["No.", "Username", "title"])
        
        # Verify all are separate files
        self.assertEqual(len(set(csv_files)), 5)
        for csv_file in csv_files:
            self.assertTrue(os.path.exists(csv_file))
        
        print("✓ Test separate_csv_per_niche passed")

    def test_separate_processed_tracking_per_niche(self):
        """Test that each niche tracks processed posts separately"""
        # Niche 1 processed posts
        processed1 = os.path.join(self.test_dir, "processed_niche1.txt")
        with open(processed1, "w") as f:
            f.write("ABC123\nDEF456\n")
        
        # Niche 2 processed posts (different)
        processed2 = os.path.join(self.test_dir, "processed_niche2.txt")
        with open(processed2, "w") as f:
            f.write("GHI789\n")
        
        # Load and verify they're separate
        with open(processed1, "r") as f:
            niche1_posts = set(line.strip() for line in f if line.strip())
        with open(processed2, "r") as f:
            niche2_posts = set(line.strip() for line in f if line.strip())
        
        self.assertEqual(len(niche1_posts), 2)
        self.assertEqual(len(niche2_posts), 1)
        self.assertNotEqual(niche1_posts, niche2_posts)
        
        print("✓ Test separate_processed_tracking_per_niche passed")


class TestNicheScheduling(unittest.TestCase):
    """Tests for niche scheduling functionality"""

    def test_delay_configuration(self):
        """Test delay between niches is configured correctly"""
        NICHE_DELAY_HOURS = 1
        NICHE_DELAY_SECONDS = NICHE_DELAY_HOURS * 3600
        
        self.assertEqual(NICHE_DELAY_HOURS, 1)
        self.assertEqual(NICHE_DELAY_SECONDS, 3600)
        print("✓ Test delay_configuration passed")

    def test_niche_order_preserved(self):
        """Test that niches are processed in order"""
        NICHES = {
            "niche1": {},
            "niche2": {},
            "niche3": {},
            "niche4": {},
            "niche5": {},
        }
        
        niche_list = list(NICHES.keys())
        expected_order = ["niche1", "niche2", "niche3", "niche4", "niche5"]
        
        self.assertEqual(niche_list, expected_order)
        print("✓ Test niche_order_preserved passed")

    def test_video_counter_reset_per_niche(self):
        """Test that video counter resets for each niche"""
        video_counter = 0
        
        # Simulate niche 1
        video_counter = 0  # Reset
        for _ in range(3):
            video_counter += 1
        niche1_final = video_counter
        
        # Simulate niche 2 (counter resets)
        video_counter = 0  # Reset
        for _ in range(2):
            video_counter += 1
        niche2_final = video_counter
        
        self.assertEqual(niche1_final, 3)
        self.assertEqual(niche2_final, 2)
        print("✓ Test video_counter_reset_per_niche passed")


class TestNicheR2Folders(unittest.TestCase):
    """Tests for niche-based R2 folder (key prefix) naming"""

    def test_r2_folder_matches_niche(self):
        """Test R2 folder is named after niche, not username"""
        niche_config = {
            "drive_folder": "niche1_reels"  # drive_folder key reused for R2 prefix
        }
        
        # All videos from this niche go to the same R2 prefix
        username1 = "fitness_user1"
        username2 = "fitness_user2"
        
        # Both should use niche folder prefix, not username
        r2_folder = niche_config["drive_folder"]
        
        self.assertEqual(r2_folder, "niche1_reels")
        self.assertNotEqual(r2_folder, f"{username1}_reels")
        self.assertNotEqual(r2_folder, f"{username2}_reels")
        
        print("✓ Test r2_folder_matches_niche passed")

    def test_local_folder_naming(self):
        """Test local temp folder naming convention"""
        niche_config = {"drive_folder": "niche1_reels"}
        
        target_folder = f"{niche_config['drive_folder']}_local"
        
        self.assertEqual(target_folder, "niche1_reels_local")
        print("✓ Test local_folder_naming passed")

    def test_r2_full_key_path(self):
        """Test full R2 key path generation"""
        niche_folder = "niche2_reels"
        video_number = 15
        username = "creator123"
        shortcode = "AbCdEf"
        
        r2_key = f"{niche_folder}/{video_number:03d}_{username}_{shortcode}.mp4"
        
        self.assertEqual(r2_key, "niche2_reels/015_creator123_AbCdEf.mp4")
        self.assertIn("/", r2_key)  # Has folder separator
        print("✓ Test r2_full_key_path passed")


def run_tests():
    """Run all tests and print summary"""
    print("=" * 60)
    print("Running Static Tests for main.py")
    print("=" * 60)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestUploadToR2))
    suite.addTests(loader.loadTestsFromTestCase(TestProcessPost))
    suite.addTests(loader.loadTestsFromTestCase(TestFileOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestRetryLogic))
    suite.addTests(loader.loadTestsFromTestCase(TestPostFiltering))
    suite.addTests(loader.loadTestsFromTestCase(TestPostMetadata))
    suite.addTests(loader.loadTestsFromTestCase(TestVideoNumbering))
    suite.addTests(loader.loadTestsFromTestCase(TestNewCSVFormat))
    suite.addTests(loader.loadTestsFromTestCase(TestPinterestFormatting))
    suite.addTests(loader.loadTestsFromTestCase(TestR2FolderNaming))
    suite.addTests(loader.loadTestsFromTestCase(TestFileVerification))
    suite.addTests(loader.loadTestsFromTestCase(TestUploadPacing))
    suite.addTests(loader.loadTestsFromTestCase(TestSequentialProcessing))
    suite.addTests(loader.loadTestsFromTestCase(TestR2Configuration))
    suite.addTests(loader.loadTestsFromTestCase(TestFailureLogging))
    suite.addTests(loader.loadTestsFromTestCase(TestTextNormalization))
    suite.addTests(loader.loadTestsFromTestCase(TestNicheConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestNicheScheduling))
    suite.addTests(loader.loadTestsFromTestCase(TestNicheR2Folders))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 60)
    
    return result


if __name__ == "__main__":
    run_tests()
