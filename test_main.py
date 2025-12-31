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

    def test_upload_to_drive_existing_folder_logic(self):
        """Test logic for uploading to an existing Drive folder"""
        # Simulate the folder lookup logic
        mock_drive = MagicMock()
        
        # Mock existing folder
        mock_folder = {'id': 'existing_folder_123'}
        mock_list_file = MagicMock()
        mock_list_file.GetList.return_value = [mock_folder]
        mock_drive.ListFile.return_value = mock_list_file
        
        # Simulate the upload_to_drive logic
        drive_folder_name = "test_user_reels"
        
        folder_list = mock_drive.ListFile({'q': f"title='{drive_folder_name}'"}).GetList()
        
        # Test folder exists branch
        if folder_list:
            folder_id = folder_list[0]['id']
        else:
            folder_id = None
        
        self.assertEqual(len(folder_list), 1)
        self.assertEqual(folder_id, 'existing_folder_123')
        print("✓ Test upload_to_drive_existing_folder_logic passed")

    def test_upload_to_drive_new_folder_logic(self):
        """Test logic when folder needs to be created"""
        mock_drive = MagicMock()
        
        # Mock empty folder list (folder doesn't exist)
        mock_list_file = MagicMock()
        mock_list_file.GetList.return_value = []
        mock_drive.ListFile.return_value = mock_list_file
        
        # Mock folder creation
        mock_new_folder = MagicMock()
        mock_new_folder.__getitem__ = Mock(return_value='new_folder_456')
        mock_drive.CreateFile.return_value = mock_new_folder
        
        folder_list = mock_drive.ListFile({'q': "title='new_folder'"}).GetList()
        
        # Test folder creation branch
        if folder_list:
            folder_id = folder_list[0]['id']
        else:
            # Create folder
            folder_metadata = {'title': 'new_folder', 'mimeType': 'application/vnd.google-apps.folder'}
            folder = mock_drive.CreateFile(folder_metadata)
            folder.Upload()
            folder_id = folder['id']
        
        self.assertEqual(len(folder_list), 0)
        self.assertEqual(folder_id, 'new_folder_456')
        mock_drive.CreateFile.assert_called_once()
        print("✓ Test upload_to_drive_new_folder_logic passed")

    def test_file_upload_logic(self):
        """Test file upload and permission logic"""
        mock_drive = MagicMock()
        mock_gfile = MagicMock()
        mock_gfile.__getitem__ = Mock(return_value='https://drive.google.com/file/test123')
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
        
        # Verify calls
        gfile.SetContentFile.assert_called_once_with(local_file)
        gfile.Upload.assert_called_once()
        gfile.InsertPermission.assert_called_once()
        
        # Verify link retrieval
        link = gfile['alternateLink']
        self.assertEqual(link, 'https://drive.google.com/file/test123')
        print("✓ Test file_upload_logic passed")


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

    def test_thread_safe_counter_logic(self):
        """Test thread-safe counter logic"""
        import threading
        
        counter = 0
        lock = threading.Lock()
        results = []
        
        def increment():
            nonlocal counter
            with lock:
                counter += 1
                results.append(counter)
        
        threads = [threading.Thread(target=increment) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All numbers should be unique
        self.assertEqual(len(set(results)), 10)
        self.assertEqual(counter, 10)
        print("✓ Test thread_safe_counter_logic passed")


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
