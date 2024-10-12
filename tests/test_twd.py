import unittest
import os
from twd import twd

class TestTWD(unittest.TestCase):
    def test_save_directory(self):
        twd.save_directory()
        self.assertEqual(twd.TWD, os.getcwd())

    def test_save_specified_directory(self):
        path = "/tmp"
        twd.save_directory(path)
        self.assertEqual(twd.TWD, path)

    def test_show_directory(self):
        twd.TWD = "/tmp"
        self.assertEqual(twd.TWD, "/tmp")

if __name__ == "__main__":
    unittest.main()
