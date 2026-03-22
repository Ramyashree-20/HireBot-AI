"""
data_handler.py
═══════════════
In-memory candidate data store with simulated persistence.

In a production system, replace _store with a real database (PostgreSQL,
MongoDB, etc.). The public interface (save / get / list / export) stays
the same regardless of the backing store.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


class DataHandler:
    """Thread-safe in-memory candidate store with optional JSON snapshot."""

    _SNAPSHOT_PATH = Path("data/candidates_session.json")

    def __init__(self):
        # Primary in-memory store  { candidate_id: candidate_dict }
        self._store: dict[str, dict] = {}

    # ── Write ─────────────────────────────────────────────────────────────────

    def save_candidate(self, info: dict, answers: list[dict] | None = None) -> str:
        """
        Upsert a candidate record.

        Parameters
        ----------
        info    : dict with keys name, email, phone, experience,
                  position, location, tech_stack
        answers : list of {"question": ..., "answer": ...} dicts

        Returns
        -------
        candidate_id : str  (UUID-4 hex)
        """
        # Derive a stable ID from email when available, else new UUID
        email = (info.get("email") or "").lower().strip()
        candidate_id = self._id_from_email(email) if email else self._new_id()

        record = {
            "id": candidate_id,
            "name":       info.get("name"),
            "email":      email or None,
            "phone":      info.get("phone"),
            "experience": info.get("experience"),
            "position":   info.get("position"),
            "location":   info.get("location"),
            "tech_stack": info.get("tech_stack"),   # may be list or string
            "answers":    answers or [],
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "status":     "screened",
        }
        self._store[candidate_id] = record
        self._snapshot()
        return candidate_id

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_candidate(self, candidate_id: str) -> dict | None:
        """Return a candidate record by ID, or None."""
        return self._store.get(candidate_id)

    def find_by_email(self, email: str) -> dict | None:
        """Return the first record matching the given email (case-insensitive)."""
        email = email.lower().strip()
        for record in self._store.values():
            if (record.get("email") or "").lower() == email:
                return record
        return None

    def list_candidates(self) -> list[dict]:
        """Return all candidate records sorted by submission time (newest first)."""
        return sorted(
            self._store.values(),
            key=lambda r: r.get("submitted_at", ""),
            reverse=True,
        )

    def count(self) -> int:
        return len(self._store)

    # ── Export ────────────────────────────────────────────────────────────────

    def export_json(self) -> str:
        """Return the full store as a formatted JSON string."""
        return json.dumps(self.list_candidates(), indent=2, ensure_ascii=False)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _new_id(self) -> str:
        return uuid.uuid4().hex[:12]

    def _id_from_email(self, email: str) -> str:
        # Deterministic ID: reuse same ID for same email across sessions
        import hashlib
        return hashlib.md5(email.encode()).hexdigest()[:12]

    def _snapshot(self) -> None:
        """
        Persist the current store to disk as a JSON file.
        Fails silently — in-memory data is always authoritative.
        """
        try:
            self._SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
            self._SNAPSHOT_PATH.write_text(
                self.export_json(), encoding="utf-8"
            )
        except Exception:
            pass
