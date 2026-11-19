import json
import tempfile
import unittest
from pathlib import Path

from app import create_app


class AppStateApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database = Path(self.temp_dir.name) / "test.sqlite3"
        self.app = create_app(database)
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_state_is_saved_and_read_from_sqlite(self):
        state = {"profile": {"name": "Learner"}, "journal": [], "notes": []}

        response = self.client.put("/api/state", json=state)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"saved": True})
        self.assertEqual(self.client.get("/api/state").get_json()["state"], state)

    def test_rejects_state_missing_required_sections(self):
        response = self.client.put("/api/state", json={"notes": []})

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_rejects_non_object_state(self):
        response = self.client.put(
            "/api/state",
            data=json.dumps(["not", "an", "object"]),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_serves_website_and_health_status(self):
        page = self.client.get("/")
        health = self.client.get("/api/health")
        stylesheet = self.client.get("/static/style.css")

        self.assertEqual(page.status_code, 200)
        self.assertIn(b"My Life Hub", page.data)
        self.assertEqual(health.get_json(), {"status": "ok", "storage": "sqlite"})
        self.assertEqual(stylesheet.status_code, 200)
        self.assertIn(b".storage-status", stylesheet.data)
        page.close()
        stylesheet.close()


if __name__ == "__main__":
    unittest.main()
