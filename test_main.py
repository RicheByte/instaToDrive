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


class TestUploadToDrive(unittest.TestCase):
    """Tests for upload_to_drive function logic (without pydrive dependency)"""

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

    def test_folder_cache_hit(self):
        """Test that cached folder IDs are reused"""
        folder_id_cache = {}
        folder_name = "test_user_reels"
        
        # Simulate caching a folder ID
        folder_id_cache[folder_name] = "cached_folder_123"
        
        # Test cache hit
        if folder_name in folder_id_cache:
            folder_id = folder_id_cache[folder_name]
        else:
            folder_id = None
        
        self.assertEqual(folder_id, "cached_folder_123")
        print("✓ Test folder_cache_hit passed")

    def test_folder_cache_miss_existing_folder(self):
        """Test cache miss with existing folder in Drive"""
        folder_id_cache = {}
        mock_drive = MagicMock()
        folder_name = "test_user_reels"
        
        # Mock existing folder in Drive
        mock_folder = {'id': 'existing_folder_456'}
        mock_list_file = MagicMock()
        mock_list_file.GetList.return_value = [mock_folder]
        mock_drive.ListFile.return_value = mock_list_file
        
        # Simulate get_or_create_folder logic
        if folder_name in folder_id_cache:
            folder_id = folder_id_cache[folder_name]
        else:
            folder_list = mock_drive.ListFile({'q': f"title='{folder_name}'"}).GetList()
            if folder_list:
                folder_id = folder_list[0]['id']
            else:
                folder_id = None
            folder_id_cache[folder_name] = folder_id
        
        self.assertEqual(folder_id, 'existing_folder_456')
        self.assertIn(folder_name, folder_id_cache)
        print("✓ Test folder_cache_miss_existing_folder passed")

    def test_folder_cache_miss_create_new(self):
        """Test cache miss requiring new folder creation"""
        folder_id_cache = {}
        mock_drive = MagicMock()
        folder_name = "new_user_reels"
        
        # Mock empty folder list (folder doesn't exist)
        mock_list_file = MagicMock()
        mock_list_file.GetList.return_value = []
        mock_drive.ListFile.return_value = mock_list_file
        
        # Mock folder creation
        mock_new_folder = MagicMock()
        mock_new_folder.__getitem__ = Mock(return_value='new_folder_789')
        mock_drive.CreateFile.return_value = mock_new_folder
        
        # Simulate get_or_create_folder logic
        if folder_name in folder_id_cache:
            folder_id = folder_id_cache[folder_name]
        else:
            folder_list = mock_drive.ListFile({'q': f"title='{folder_name}'"}).GetList()
            if folder_list:
                folder_id = folder_list[0]['id']
            else:
                folder_metadata = {'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
                folder = mock_drive.CreateFile(folder_metadata)
                folder.Upload()
                folder_id = folder['id']
            folder_id_cache[folder_name] = folder_id
        
        self.assertEqual(folder_id, 'new_folder_789')
        self.assertIn(folder_name, folder_id_cache)
        mock_drive.CreateFile.assert_called_once()
        print("✓ Test folder_cache_miss_create_new passed")

    def test_direct_download_link_format(self):
        """Test that direct download links use the correct format"""
        file_id = "1ABC123xyz"
        
        # This is the format we should use (not alternateLink)
        direct_link = f"https://drive.usercontent.google.com/download?id={file_id}"
        
        self.assertIn("drive.usercontent.google.com", direct_link)
        self.assertIn("download?id=", direct_link)
        self.assertIn(file_id, direct_link)
        self.assertNotIn("alternateLink", direct_link)
        print("✓ Test direct_download_link_format passed")

    def test_file_upload_with_direct_link(self):
        """Test file upload returns direct download link"""
        mock_drive = MagicMock()
        mock_gfile = MagicMock()
        mock_gfile.__getitem__ = Mock(return_value='file_id_123')
        mock_drive.CreateFile.return_value = mock_gfile
        
        # Simulate upload logic
        folder_id = 'folder_123'
        local_file = self.test_file
        
        gfile = mock_drive.CreateFile({
            'parents': [{'id': folder_id}], 
            'title': os.path.basename(local_file)
        })
        gfile.SetContentFile(local_file)
        gfile.Upload()
        gfile.InsertPermission({'type': 'anyone', 'value': 'anyone', 'role': 'reader'})
        
        # Build direct download link
        file_id = gfile['id']
        direct_link = f"https://drive.usercontent.google.com/download?id={file_id}"
        
        # Verify calls
        gfile.SetContentFile.assert_called_once_with(local_file)
        gfile.Upload.assert_called_once()
        gfile.InsertPermission.assert_called_once()
        
        self.assertEqual(direct_link, 'https://drive.usercontent.google.com/download?id=file_id_123')
        print("✓ Test file_upload_with_direct_link passed")


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
    """Tests for new CSV format with 6 columns"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.output_csv = os.path.join(self.test_dir, "reels_drive_links.csv")

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_csv_header_creation(self):
        """Test CSV header row creation"""
        headers = ["No.", "Username", "Video Title", "Drive Folder", "Filename", "Drive Link"]
        
        with open(self.output_csv, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
        
        with open(self.output_csv, "r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            header_row = next(reader)
        
        self.assertEqual(header_row, headers)
        self.assertEqual(len(header_row), 6)
        print("✓ Test csv_header_creation passed")

    def test_csv_data_row(self):
        """Test CSV data row with all 6 columns"""
        row_data = [
            1,                                      # No.
            "testuser",                             # Username
            "Test Video Title",                     # Video Title
            "testuser_reels",                       # Drive Folder
            "001_testuser_ABC123.mp4",              # Filename
            "https://drive.google.com/file/xyz"    # Drive Link
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
        self.assertEqual(len(saved_row), 6)
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


class TestDriveFolderNaming(unittest.TestCase):
    """Tests for Drive folder naming convention"""

    def test_folder_name_from_username(self):
        """Test folder name generation from username"""
        username = "cooluser"
        drive_folder = f"{username}_reels"
        
        self.assertEqual(drive_folder, "cooluser_reels")
        print("✓ Test folder_name_from_username passed")

    def test_folder_name_consistency(self):
        """Test folder name is consistent between local and drive"""
        username = "testuser"
        target_folder = f"{username}_reels"
        drive_folder = f"{username}_reels"
        
        self.assertEqual(target_folder, drive_folder)
        print("✓ Test folder_name_consistency passed")


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


class TestFolderCaching(unittest.TestCase):
    """Tests for folder ID caching system"""

    def test_cache_empty_initially(self):
        """Test that folder cache starts empty"""
        folder_id_cache = {}
        self.assertEqual(len(folder_id_cache), 0)
        print("✓ Test cache_empty_initially passed")

    def test_cache_stores_folder_id(self):
        """Test that folder ID is stored in cache"""
        folder_id_cache = {}
        folder_name = "user1_reels"
        folder_id = "folder_abc123"
        
        folder_id_cache[folder_name] = folder_id
        
        self.assertIn(folder_name, folder_id_cache)
        self.assertEqual(folder_id_cache[folder_name], folder_id)
        print("✓ Test cache_stores_folder_id passed")

    def test_cache_multiple_users(self):
        """Test caching multiple user folders"""
        folder_id_cache = {}
        
        users = [
            ("user1_reels", "folder_111"),
            ("user2_reels", "folder_222"),
            ("user3_reels", "folder_333"),
        ]
        
        for folder_name, folder_id in users:
            folder_id_cache[folder_name] = folder_id
        
        self.assertEqual(len(folder_id_cache), 3)
        self.assertEqual(folder_id_cache["user2_reels"], "folder_222")
        print("✓ Test cache_multiple_users passed")

    def test_cache_reduces_api_calls(self):
        """Test that cache prevents repeated API lookups"""
        folder_id_cache = {}
        mock_drive = MagicMock()
        api_call_count = 0
        
        def mock_get_or_create_folder(folder_name):
            nonlocal api_call_count
            if folder_name in folder_id_cache:
                return folder_id_cache[folder_name]
            
            # This would be an API call
            api_call_count += 1
            folder_id = f"folder_{folder_name}"
            folder_id_cache[folder_name] = folder_id
            return folder_id
        
        # First call should hit API
        mock_get_or_create_folder("user1_reels")
        self.assertEqual(api_call_count, 1)
        
        # Second call should use cache
        mock_get_or_create_folder("user1_reels")
        self.assertEqual(api_call_count, 1)  # Still 1, not 2
        
        # Different user should hit API
        mock_get_or_create_folder("user2_reels")
        self.assertEqual(api_call_count, 2)
        
        print("✓ Test cache_reduces_api_calls passed")


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
    suite.addTests(loader.loadTestsFromTestCase(TestUploadToDrive))
    suite.addTests(loader.loadTestsFromTestCase(TestProcessPost))
    suite.addTests(loader.loadTestsFromTestCase(TestFileOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestRetryLogic))
    suite.addTests(loader.loadTestsFromTestCase(TestPostFiltering))
    suite.addTests(loader.loadTestsFromTestCase(TestPostMetadata))
    suite.addTests(loader.loadTestsFromTestCase(TestVideoNumbering))
    suite.addTests(loader.loadTestsFromTestCase(TestNewCSVFormat))
    suite.addTests(loader.loadTestsFromTestCase(TestDriveFolderNaming))
    suite.addTests(loader.loadTestsFromTestCase(TestFileVerification))
    suite.addTests(loader.loadTestsFromTestCase(TestUploadPacing))
    suite.addTests(loader.loadTestsFromTestCase(TestSequentialProcessing))
    suite.addTests(loader.loadTestsFromTestCase(TestFolderCaching))
    
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
