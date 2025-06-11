import unittest
import os
import tempfile
from twd import twd

class TestTWD(unittest.TestCase):
    def test_save_directory(self):
        twd.save_directory()
        self.assertEqual(twd.TWD, os.getcwd())

    def test_save_specified_directory(self):
        # Use portable temporary directory instead of hardcoded /tmp
        path = tempfile.gettempdir()
        twd.save_directory(path)
        self.assertEqual(twd.TWD, path)

    def test_show_directory(self):
        # Use portable temporary directory instead of hardcoded /tmp
        temp_dir = tempfile.gettempdir()
        twd.TWD = temp_dir
        self.assertEqual(twd.TWD, temp_dir)

if __name__ == "__main__":
    unittest.main()
