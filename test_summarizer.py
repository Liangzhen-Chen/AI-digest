import os
import sys
import types
import unittest
from unittest.mock import Mock, patch

fake_google = types.ModuleType("google")
fake_genai = types.ModuleType("google.genai")
fake_genai.Client = Mock()
fake_google.genai = fake_genai
sys.modules.setdefault("google", fake_google)
sys.modules.setdefault("google.genai", fake_genai)

import summarizer


class SummarizerFallbackTests(unittest.TestCase):
    def setUp(self):
        self.feeds = {
            "AI动态": [
                {
                    "source": "Test Feed",
                    "title": "AI model update",
                    "link": "https://example.com/ai",
                    "summary": "A new AI model was released.",
                    "published": "2026-04-27T07:00:00+00:00",
                }
            ]
        }

    @patch.dict(os.environ, {"GEMINI_API_KEY": "gemini-key"}, clear=True)
    def test_requires_deepseek_key_when_gemini_models_fail(self):
        gemini_client = Mock()
        gemini_client.models.generate_content.side_effect = RuntimeError("quota")

        with patch("summarizer.genai.Client", return_value=gemini_client):
            with self.assertRaisesRegex(RuntimeError, "DEEPSEEK_API_KEY"):
                summarizer.summarize_digest(self.feeds)

    @patch.dict(
        os.environ,
        {"GEMINI_API_KEY": "gemini-key", "DEEPSEEK_API_KEY": "deepseek-key"},
        clear=True,
    )
    def test_uses_deepseek_when_all_gemini_models_fail(self):
        gemini_client = Mock()
        gemini_client.models.generate_content.side_effect = RuntimeError("quota")
        deepseek_response = Mock()
        deepseek_response.json.return_value = {
            "choices": [{"message": {"content": "[[PRODUCT:ChatGPT]]\n## Digest"}}]
        }

        with patch("summarizer.genai.Client", return_value=gemini_client):
            with patch("summarizer.requests.post", return_value=deepseek_response) as post:
                with patch("summarizer.record_featured") as record_featured:
                    digest = summarizer.summarize_digest(self.feeds)

        self.assertEqual(digest, "## Digest")
        post.assert_called_once()
        deepseek_response.raise_for_status.assert_called_once()
        record_featured.assert_called_once_with("ChatGPT")


if __name__ == "__main__":
    unittest.main()
