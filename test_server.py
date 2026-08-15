import os
import unittest

os.environ.setdefault("SCRAPER_SECRET", "test-secret")

import server


class ScraperSafetyTests(unittest.TestCase):
    def test_detects_known_waf_pages(self):
        for signature in server.BLOCK_SIGNATURES:
            with self.subTest(signature=signature):
                reason = server.detect_block(
                    f"<html>{signature}</html>",
                    "https://a810-bisweb.nyc.gov/",
                    ["FILE DATE"],
                )
                self.assertIsNotNone(reason)

    def test_rejects_wrong_200_page(self):
        reason = server.detect_block(
            "<html><title>NYC Buildings</title><form>Search</form></html>",
            "https://a810-bisweb.nyc.gov/bisweb/bsqpm01.jsp",
            ["FILE DATE", "Jobs/Filings", "NO JOBS", "NO RECORDS"],
        )
        self.assertIn("unexpected page", reason)

    def test_accepts_verified_empty_jobs_page(self):
        reason = server.detect_block(
            "<html><h1>Jobs/Filings</h1><p>NO RECORDS</p></html>",
            "https://a810-bisweb.nyc.gov/bisweb/JobsQueryByLocationServlet",
            ["FILE DATE", "Jobs/Filings", "NO JOBS", "NO RECORDS"],
        )
        self.assertIsNone(reason)

    def test_extracts_expected_count(self):
        self.assertEqual(server.extract_expected_job_count("Total Jobs: 14,743"), 14743)
        self.assertEqual(server.extract_expected_job_count("Displaying 1 - 25 of 556"), 556)
        self.assertIsNone(server.extract_expected_job_count("Jobs/Filings - NO RECORDS"))

    def test_block_result_is_never_treated_as_verified_empty(self):
        class FakePage:
            url = "https://a810-bisweb.nyc.gov/bisweb/bsqpm01.jsp"

            def content(self):
                return "<html>Access Denied</html>"

            def goto(self, *args, **kwargs):
                return None

        original_sleep = server.time.sleep
        server.time.sleep = lambda _: None
        try:
            result = server.scrape_jobs_by_location(FakePage(), "1036460")
        finally:
            server.time.sleep = original_sleep
        self.assertTrue(result["blocked"])
        self.assertFalse(result["page_verified"])
        self.assertFalse(result["complete"])
        self.assertEqual(server.result_http_status(result), 503)

    def test_other_errors_are_non_200(self):
        self.assertEqual(server.result_http_status({"error": "navigation timed out"}), 502)
        self.assertEqual(server.result_http_status({"jobs": [], "page_verified": True}), 200)


if __name__ == "__main__":
    unittest.main()
