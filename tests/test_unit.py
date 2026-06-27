"""Testes unitários que não dependem de rede (lógica pura)."""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from meta_ad_agent.config import Config, _load_dotenv  # noqa: E402
from meta_ad_agent.posts import InstagramPost  # noqa: E402


class ConfigTests(unittest.TestCase):
    def test_normalized_ad_account_adds_prefix(self):
        cfg = Config(access_token="t", ad_account_id="1234567890")
        self.assertEqual(cfg.normalized_ad_account, "act_1234567890")

    def test_normalized_ad_account_keeps_prefix(self):
        cfg = Config(access_token="t", ad_account_id="act_999")
        self.assertEqual(cfg.normalized_ad_account, "act_999")

    def test_default_api_version(self):
        cfg = Config(access_token="t", ad_account_id="1")
        self.assertTrue(cfg.api_version.startswith("v"))

    def test_load_dotenv_does_not_override_existing(self, ):
        os.environ["DOTENV_TEST_KEY"] = "already"
        p = Path("_tmp_dotenv_test.env")
        p.write_text('DOTENV_TEST_KEY="changed"\nNEW_KEY=newval\n', encoding="utf-8")
        try:
            _load_dotenv(p)
            self.assertEqual(os.environ["DOTENV_TEST_KEY"], "already")
            self.assertEqual(os.environ["NEW_KEY"], "newval")
        finally:
            p.unlink(missing_ok=True)
            os.environ.pop("DOTENV_TEST_KEY", None)
            os.environ.pop("NEW_KEY", None)


class PostTests(unittest.TestCase):
    def test_from_api_parsing(self):
        post = InstagramPost.from_api(
            {
                "id": "178",
                "caption": "Olá mundo",
                "media_type": "IMAGE",
                "permalink": "https://instagram.com/p/abc",
                "timestamp": "2026-06-01T10:00:00+0000",
            }
        )
        self.assertEqual(post.id, "178")
        self.assertEqual(post.media_type, "IMAGE")

    def test_short_caption_truncates(self):
        post = InstagramPost.from_api({"caption": "x" * 200})
        self.assertTrue(post.short_caption.endswith("…"))
        self.assertLessEqual(len(post.short_caption), 71)

    def test_short_caption_collapses_newlines(self):
        post = InstagramPost.from_api({"caption": "linha1\nlinha2"})
        self.assertNotIn("\n", post.short_caption)


if __name__ == "__main__":
    unittest.main()
