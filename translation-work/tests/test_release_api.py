"""Regression tests for API path generation during GitHub Release publication."""
from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release


class GitHubApiPaths(unittest.TestCase):
    def setUp(self):
        self.api = object.__new__(release.GitHub)
        self.api.repository = release.CANONICAL_REPO
        self.api.token = "synthetic-test-token"

    def test_repository_root_has_no_trailing_slash(self):
        self.assertEqual(
            self.api.endpoint(""),
            "/repos/isyuricunha/star-dynasties-gold-traducao-portugues-brasileiro",
        )

    def test_nested_release_paths_are_unaffected(self):
        self.assertEqual(
            self.api.endpoint("releases?per_page=100&page=1"),
            "/repos/isyuricunha/star-dynasties-gold-traducao-portugues-brasileiro/releases?per_page=100&page=1",
        )
        self.assertEqual(
            self.api.endpoint("/commits/main"),
            "/repos/isyuricunha/star-dynasties-gold-traducao-portugues-brasileiro/commits/main",
        )

    def test_current_commit_check_requests_canonical_repository_path(self):
        urls = []
        class Response(io.BytesIO):
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.close()
        def fake_urlopen(request, timeout=60):
            urls.append(request.full_url)
            if request.full_url.endswith("/commits/main"):
                return Response(json.dumps({"sha": "a" * 40}).encode())
            return Response(json.dumps({"default_branch": "main"}).encode())
        with patch.object(release.urllib.request, "urlopen", side_effect=fake_urlopen):
            self.api.assert_current("a" * 40)
        self.assertEqual(
            urls,
            [
                "https://api.github.com/repos/isyuricunha/star-dynasties-gold-traducao-portugues-brasileiro",
                "https://api.github.com/repos/isyuricunha/star-dynasties-gold-traducao-portugues-brasileiro/commits/main",
            ],
        )


if __name__ == "__main__":
    unittest.main()
