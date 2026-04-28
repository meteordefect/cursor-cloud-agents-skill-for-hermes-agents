import json
import os
import unittest
import urllib.error
from io import BytesIO
from unittest.mock import patch

import handler


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.body).encode("utf-8")


class HandlerTests(unittest.TestCase):
    def test_launch_agent_builds_cursor_payload(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["method"] = request.get_method()
            captured["body"] = json.loads(request.data.decode("utf-8"))
            captured["auth"] = request.headers["Authorization"]
            return FakeResponse({"id": "bc_123", "status": "CREATING"})

        payload = {
            "action": "launch_agent",
            "prompt": "Update docs",
            "repository": "https://github.com/acme/app",
            "ref": "main",
            "model": "default",
            "branch_name": "cursor/update-docs",
            "auto_create_pr": True,
        }

        with patch.dict(os.environ, {"CURSOR_API_KEY": "test-key"}):
            with patch("urllib.request.urlopen", fake_urlopen):
                result = handler.handle(payload)

        self.assertEqual(result["id"], "bc_123")
        self.assertEqual(captured["url"], "https://api.cursor.com/v0/agents")
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["body"]["prompt"]["text"], "Update docs")
        self.assertEqual(captured["body"]["source"]["repository"], "https://github.com/acme/app")
        self.assertEqual(captured["body"]["source"]["ref"], "main")
        self.assertEqual(captured["body"]["target"]["branchName"], "cursor/update-docs")
        self.assertEqual(captured["body"]["target"]["autoCreatePr"], True)
        self.assertTrue(captured["auth"].startswith("Basic "))

    def test_list_agents_adds_query_parameters(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            return FakeResponse({"agents": []})

        payload = {
            "action": "list_agents",
            "limit": 5,
            "cursor": "next-page",
            "pr_url": "https://github.com/acme/app/pull/1",
        }

        with patch.dict(os.environ, {"CURSOR_API_KEY": "test-key"}):
            with patch("urllib.request.urlopen", fake_urlopen):
                result = handler.handle(payload)

        self.assertEqual(result, {"agents": []})
        self.assertIn("limit=5", captured["url"])
        self.assertIn("cursor=next-page", captured["url"])
        self.assertIn("prUrl=https%3A%2F%2Fgithub.com%2Facme%2Fapp%2Fpull%2F1", captured["url"])

    def test_missing_api_key_returns_skill_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(handler.SkillError) as context:
                handler.handle({"action": "me"})

        self.assertEqual(str(context.exception), "CURSOR_API_KEY is required")

    def test_http_error_is_wrapped(self):
        def fake_urlopen(request, timeout):
            raise urllib.error.HTTPError(
                request.full_url,
                401,
                "Unauthorized",
                {},
                BytesIO(b'{"error":"bad key"}'),
            )

        with patch.dict(os.environ, {"CURSOR_API_KEY": "bad-key"}):
            with patch("urllib.request.urlopen", fake_urlopen):
                with self.assertRaises(handler.SkillError) as context:
                    handler.handle({"action": "me"})

        self.assertIn("Cursor API error 401", str(context.exception))


if __name__ == "__main__":
    unittest.main()
