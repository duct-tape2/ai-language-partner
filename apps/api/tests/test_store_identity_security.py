from __future__ import annotations

import re
import sys
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.store import ApiStore


LEGACY_LEARNER_ID = "oidc_361ca3397e29ceff"


def _upsert_external_identity(store: ApiStore, *, learner_id: str | None = None) -> dict:
    return store.upsert_external_identity_account(
        provider="oidc",
        subject="external-subject-123",
        email="learner@example.com",
        email_verified=True,
        profile={"name": "Learner"},
        learner_id=learner_id,
        password_hash="not-used-for-external-auth",
    )


def test_new_external_identity_uses_random_learner_id_and_remains_stable(tmp_path: Path) -> None:
    store = ApiStore(tmp_path / "identity.sqlite3")

    created = _upsert_external_identity(store)
    repeat = _upsert_external_identity(store)

    assert re.fullmatch(r"learner_[0-9a-f]{32}", created["learnerId"])
    assert created["learnerId"] != LEGACY_LEARNER_ID
    assert repeat["id"] == created["id"]
    assert repeat["learnerId"] == created["learnerId"]
    with store.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == 1


def test_existing_legacy_identity_keeps_its_deterministic_learner_id(tmp_path: Path) -> None:
    store = ApiStore(tmp_path / "legacy-identity.sqlite3")
    with store.connect() as conn:
        conn.execute(
            """
            INSERT INTO accounts (id, email, learner_id, password_hash, disabled_at, created_at, updated_at)
            VALUES ('acct_legacy', 'learner@example.com', ?, 'legacy-password-hash', NULL, '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00')
            """,
            (LEGACY_LEARNER_ID,),
        )
        conn.execute(
            """
            INSERT INTO account_identities
            (id, account_id, provider, subject, email, email_verified, profile_json, created_at, updated_at)
            VALUES ('acctid_legacy', 'acct_legacy', 'oidc', 'external-subject-123', 'learner@example.com', 1, '{}', '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00')
            """
        )

    account = _upsert_external_identity(store)

    assert account["id"] == "acct_legacy"
    assert account["learnerId"] == LEGACY_LEARNER_ID


def test_new_external_identity_preserves_explicit_learner_id(tmp_path: Path) -> None:
    store = ApiStore(tmp_path / "requested-identity.sqlite3")

    account = _upsert_external_identity(store, learner_id="requested learner")

    assert account["learnerId"] == "requested_learner"
