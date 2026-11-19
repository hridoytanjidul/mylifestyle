from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional

from flask import Flask, current_app, jsonify, request, send_file
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge


ROOT = Path(__file__).resolve().parent
HUB_FILE = ROOT / "personal-hub.html"
MAX_STATE_BYTES = 2 * 1024 * 1024


def create_app(database_path: Optional[Path] = None) -> Flask:
    app = Flask(__name__, static_folder="static")
    app.config["DATABASE"] = str(database_path or ROOT / "personal-hub.sqlite3")
    app.config["MAX_CONTENT_LENGTH"] = MAX_STATE_BYTES

    def initialize_database() -> None:
        path = Path(current_app.config["DATABASE"])
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path, timeout=10) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS app_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    @app.get("/")
    def index():
        return send_file(HUB_FILE, mimetype="text/html")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "storage": "sqlite"})

    @app.get("/api/state")
    def get_state():
        try:
            initialize_database()
            with sqlite3.connect(app.config["DATABASE"], timeout=10) as connection:
                row = connection.execute(
                    "SELECT payload, updated_at FROM app_state WHERE id = 1"
                ).fetchone()
            if row is None:
                return jsonify({"state": None, "updatedAt": None})
            return jsonify({"state": json.loads(row[0]), "updatedAt": row[1]})
        except (sqlite3.Error, json.JSONDecodeError):
            app.logger.exception("Unable to read saved app state")
            return jsonify({"error": "Saved data could not be read from SQLite."}), 500

    @app.put("/api/state")
    def put_state():
        try:
            state = request.get_json()
        except BadRequest:
            return jsonify({"error": "Request body must be valid JSON."}), 400
        if not isinstance(state, dict):
            return jsonify({"error": "State must be a JSON object."}), 400
        if not isinstance(state.get("profile"), dict) or not isinstance(
            state.get("journal"), list
        ):
            return jsonify({"error": "State is missing required profile or journal data."}), 400

        payload = json.dumps(state, ensure_ascii=False, separators=(",", ":"))
        if len(payload.encode("utf-8")) > MAX_STATE_BYTES:
            return jsonify({"error": "State exceeds the 2 MB storage limit."}), 413

        try:
            initialize_database()
            with sqlite3.connect(app.config["DATABASE"], timeout=10) as connection:
                connection.execute(
                    """
                    INSERT INTO app_state (id, payload)
                    VALUES (1, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        payload = excluded.payload,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (payload,),
                )
            return jsonify({"saved": True})
        except sqlite3.Error:
            app.logger.exception("Unable to persist app state")
            return jsonify({"error": "Data could not be saved to SQLite."}), 500

    @app.errorhandler(RequestEntityTooLarge)
    def request_too_large(_error):
        return jsonify({"error": "Request exceeds the 2 MB storage limit."}), 413

    @app.errorhandler(sqlite3.Error)
    def database_error(error):
        current_app.logger.exception("SQLite request failed", exc_info=error)
        return jsonify({"error": "The local database is unavailable."}), 500

    return app


app = create_app()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
