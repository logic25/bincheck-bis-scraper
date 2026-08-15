import unittest

from server import detect_block


class DetectBlockTests(unittest.TestCase):
    def test_hard_block_is_not_clean_data(self):
        reason = detect_block("<html>Access Denied</html>", "https://example.test", ["Property Profile"])
        self.assertIn("blocked", reason)

    def test_soft_redirect_is_not_clean_data(self):
        reason = detect_block("<html>BIS home page</html>", "https://example.test/home", ["Property Profile"])
        self.assertIn("unexpected page", reason)

    def test_expected_page_is_accepted(self):
        self.assertIsNone(detect_block("<h1>Property Profile</h1>", "https://example.test/profile", ["Property Profile"]))


if __name__ == "__main__":
    unittest.main()
