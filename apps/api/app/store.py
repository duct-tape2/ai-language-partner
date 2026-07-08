from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import sqlite3
import uuid
from contextlib import contextmanager
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Union

from .seed import COURSE_CATALOG, JLPT_GRAMMAR_POINTS, KOREAN_MISTAKE_PATTERNS, PERSONAS, PRACTICE_ROOMS


SCHEMA = """
CREATE TABLE IF NOT EXISTS personas (
  id TEXT PRIMARY KEY,
  data_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS practice_rooms (
  id TEXT PRIMARY KEY,
  persona_id TEXT NOT NULL,
  data_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
  id TEXT PRIMARY KEY,
  data_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS content_versions (
  id TEXT PRIMARY KEY,
  label TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  parent_version_id TEXT,
  branch_name TEXT,
  courses_json TEXT NOT NULL,
  practice_rooms_json TEXT NOT NULL,
  report_json TEXT NOT NULL,
  imported_counts_json TEXT NOT NULL,
  source TEXT NOT NULL,
  created_by TEXT,
  submitted_by TEXT,
  reviewed_by TEXT,
  review_note TEXT,
  created_at TEXT NOT NULL,
  submitted_at TEXT,
  reviewed_at TEXT,
  published_at TEXT
);

CREATE TABLE IF NOT EXISTS content_assignments (
  id TEXT PRIMARY KEY,
  version_id TEXT NOT NULL UNIQUE,
  assignee TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'todo',
  priority TEXT NOT NULL DEFAULT 'normal',
  note TEXT,
  due_at TEXT,
  created_by TEXT,
  updated_by TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  completed_at TEXT,
  FOREIGN KEY(version_id) REFERENCES content_versions(id)
);

CREATE TABLE IF NOT EXISTS content_releases (
  id TEXT PRIMARY KEY,
  version_id TEXT NOT NULL,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'planned',
  release_strategy TEXT NOT NULL DEFAULT 'immediate',
  rollout_percent INTEGER NOT NULL DEFAULT 100,
  catalog_scope TEXT NOT NULL DEFAULT 'incremental',
  scheduled_at TEXT,
  guardrails_json TEXT NOT NULL DEFAULT '{}',
  note TEXT,
  previous_published_version_id TEXT,
  imported_counts_json TEXT NOT NULL DEFAULT '{}',
  rollback_imported_counts_json TEXT NOT NULL DEFAULT '{}',
  created_by TEXT,
  applied_by TEXT,
  rolled_back_by TEXT,
  created_at TEXT NOT NULL,
  applied_at TEXT,
  rolled_back_at TEXT,
  rollback_note TEXT,
  FOREIGN KEY(version_id) REFERENCES content_versions(id),
  FOREIGN KEY(previous_published_version_id) REFERENCES content_versions(id)
);

CREATE INDEX IF NOT EXISTS idx_content_releases_status_created
ON content_releases (status, created_at);

CREATE INDEX IF NOT EXISTS idx_content_releases_version
ON content_releases (version_id, status);

CREATE TABLE IF NOT EXISTS content_operation_jobs (
  id TEXT PRIMARY KEY,
  job_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  priority TEXT NOT NULL DEFAULT 'normal',
  payload_json TEXT NOT NULL DEFAULT '{}',
  result_json TEXT NOT NULL DEFAULT '{}',
  error TEXT,
  created_by TEXT,
  claimed_by TEXT,
  canceled_by TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  claimed_at TEXT,
  completed_at TEXT,
  canceled_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_content_operation_jobs_status_priority
ON content_operation_jobs (status, priority, created_at);

CREATE TABLE IF NOT EXISTS content_scheduler_runs (
  id TEXT PRIMARY KEY,
  scheduler_key TEXT NOT NULL DEFAULT 'content_ops',
  status TEXT NOT NULL DEFAULT 'running',
  lease_owner TEXT NOT NULL,
  actor TEXT,
  started_at TEXT NOT NULL,
  heartbeat_at TEXT NOT NULL,
  completed_at TEXT,
  max_operation_jobs INTEGER NOT NULL DEFAULT 1,
  release_limit INTEGER NOT NULL DEFAULT 50,
  result_json TEXT NOT NULL DEFAULT '{}',
  error TEXT
);

CREATE INDEX IF NOT EXISTS idx_content_scheduler_runs_status_started
ON content_scheduler_runs (scheduler_key, status, started_at);

CREATE TABLE IF NOT EXISTS translation_memory (
  id TEXT PRIMARY KEY,
  source_language TEXT NOT NULL,
  target_language TEXT NOT NULL,
  source_text TEXT NOT NULL,
  target_text TEXT NOT NULL,
  tags_json TEXT NOT NULL,
  source_ref TEXT,
  quality INTEGER DEFAULT 100,
  created_by TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_translation_memory_pair
ON translation_memory (source_language, target_language, source_text, target_text);

CREATE TABLE IF NOT EXISTS accounts (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  learner_id TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  disabled_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS account_identities (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  provider TEXT NOT NULL,
  subject TEXT NOT NULL,
  email TEXT NOT NULL,
  email_verified INTEGER NOT NULL DEFAULT 0,
  profile_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(provider, subject),
  FOREIGN KEY(account_id) REFERENCES accounts(id)
);

CREATE TABLE IF NOT EXISTS enterprise_sso_connections (
  id TEXT PRIMARY KEY,
  provider TEXT NOT NULL,
  organization_name TEXT NOT NULL,
  domains_json TEXT NOT NULL,
  redirect_uris_json TEXT NOT NULL,
  required_email_domain TEXT,
  status TEXT NOT NULL DEFAULT 'enabled',
  created_by TEXT,
  updated_by TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS oauth_pkce_requests (
  id TEXT PRIMARY KEY,
  provider TEXT NOT NULL,
  enterprise_sso_connection_id TEXT,
  state_hash TEXT NOT NULL UNIQUE,
  redirect_uri TEXT NOT NULL,
  code_challenge TEXT NOT NULL,
  code_challenge_method TEXT NOT NULL DEFAULT 'S256',
  scope TEXT,
  nonce TEXT,
  learner_id TEXT,
  device_label TEXT,
  client_hash TEXT,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  consumed_at TEXT,
  FOREIGN KEY(enterprise_sso_connection_id) REFERENCES enterprise_sso_connections(id)
);

CREATE TABLE IF NOT EXISTS account_sessions (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  access_token_hash TEXT NOT NULL UNIQUE,
  refresh_token_hash TEXT NOT NULL UNIQUE,
  device_label TEXT,
  device_id_hash TEXT,
  access_expires_at TEXT NOT NULL,
  refresh_expires_at TEXT NOT NULL,
  revoked_at TEXT,
  created_at TEXT NOT NULL,
  last_used_at TEXT NOT NULL,
  FOREIGN KEY(account_id) REFERENCES accounts(id)
);

CREATE TABLE IF NOT EXISTS account_devices (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  device_id_hash TEXT NOT NULL,
  label TEXT,
  platform TEXT,
  trust_status TEXT NOT NULL DEFAULT 'untrusted',
  attestation_provider TEXT,
  attestation_verified INTEGER NOT NULL DEFAULT 0,
  attestation_subject_hash TEXT,
  evidence_json TEXT NOT NULL DEFAULT '{}',
  trusted_at TEXT,
  revoked_at TEXT,
  last_seen_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(account_id, device_id_hash),
  FOREIGN KEY(account_id) REFERENCES accounts(id)
);

CREATE INDEX IF NOT EXISTS idx_account_devices_account_status
ON account_devices (account_id, trust_status);

CREATE TABLE IF NOT EXISTS account_device_attestation_challenges (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  device_id_hash TEXT NOT NULL,
  provider TEXT NOT NULL,
  challenge_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  consumed_at TEXT,
  FOREIGN KEY(account_id) REFERENCES accounts(id)
);

CREATE INDEX IF NOT EXISTS idx_account_device_attestation_challenges_lookup
ON account_device_attestation_challenges (account_id, device_id_hash, provider, challenge_hash, consumed_at, expires_at);

CREATE TABLE IF NOT EXISTS auth_attempts (
  id TEXT PRIMARY KEY,
  purpose TEXT NOT NULL DEFAULT 'login',
  email_hash TEXT NOT NULL,
  client_hash TEXT NOT NULL,
  succeeded INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
  id TEXT PRIMARY KEY,
  learner_id TEXT DEFAULT 'local-dev',
  persona_id TEXT NOT NULL,
  practice_room_id TEXT NOT NULL,
  mode TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
  id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  role TEXT NOT NULL,
  input_type TEXT,
  text TEXT,
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_cards (
  id TEXT PRIMARY KEY,
  learner_id TEXT DEFAULT 'local-dev',
  conversation_id TEXT,
  front TEXT NOT NULL,
  back TEXT NOT NULL,
  example TEXT,
  tags_json TEXT NOT NULL,
  due_at TEXT,
  ease_factor REAL DEFAULT 2.5,
  interval_days INTEGER DEFAULT 0,
  review_count INTEGER DEFAULT 0,
  lapses INTEGER DEFAULT 0,
  memory_strength_days REAL DEFAULT 0.5,
  memory_difficulty REAL DEFAULT 0.65,
  last_review_quality INTEGER,
  last_reviewed_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS usage_records (
  id TEXT PRIMARY KEY,
  learner_id TEXT DEFAULT 'local-dev',
  conversation_id TEXT,
  practice_room_id TEXT,
  persona_id TEXT,
  llm_input_tokens INTEGER DEFAULT 0,
  llm_output_tokens INTEGER DEFAULT 0,
  stt_seconds REAL DEFAULT 0,
  tts_characters INTEGER DEFAULT 0,
  tts_seconds REAL DEFAULT 0,
  cache_hit INTEGER DEFAULT 0,
  provider_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics_events (
  id TEXT PRIMARY KEY,
  learner_id TEXT DEFAULT 'local-dev',
  event_name TEXT NOT NULL,
  user_id TEXT,
  session_id TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS xp_events (
  id TEXT PRIMARY KEY,
  learner_id TEXT NOT NULL,
  source TEXT NOT NULL,
  points INTEGER NOT NULL,
  day_key TEXT NOT NULL,
  idempotency_key TEXT UNIQUE,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_xp_events_learner_day
ON xp_events (learner_id, day_key);

CREATE INDEX IF NOT EXISTS idx_xp_events_day_points
ON xp_events (day_key, points);

CREATE TABLE IF NOT EXISTS achievement_awards (
  id TEXT PRIMARY KEY,
  learner_id TEXT NOT NULL,
  achievement_key TEXT NOT NULL,
  level INTEGER NOT NULL DEFAULT 1,
  awarded_at TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  UNIQUE(learner_id, achievement_key, level)
);

CREATE TABLE IF NOT EXISTS xp_abuse_flags (
  id TEXT PRIMARY KEY,
  learner_id TEXT NOT NULL,
  day_key TEXT NOT NULL,
  reason TEXT NOT NULL,
  severity TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',
  reviewed_by TEXT,
  resolution_note TEXT,
  resolved_at TEXT,
  UNIQUE(learner_id, day_key, reason)
);

CREATE TABLE IF NOT EXISTS reward_inventory (
  id TEXT PRIMARY KEY,
  learner_id TEXT NOT NULL,
  reward_key TEXT NOT NULL,
  reward_type TEXT NOT NULL,
  quantity INTEGER NOT NULL DEFAULT 0,
  metadata_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(learner_id, reward_key)
);

CREATE TABLE IF NOT EXISTS xp_boosts (
  id TEXT PRIMARY KEY,
  learner_id TEXT NOT NULL,
  reward_key TEXT NOT NULL,
  multiplier REAL NOT NULL,
  started_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  source TEXT NOT NULL,
  metadata_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_xp_boosts_learner_expires
ON xp_boosts (learner_id, expires_at);

CREATE TABLE IF NOT EXISTS friend_quests (
  id TEXT PRIMARY KEY,
  quest_key TEXT NOT NULL,
  learner_id TEXT NOT NULL,
  partner_learner_id TEXT NOT NULL,
  week_key TEXT NOT NULL,
  target_xp INTEGER NOT NULL,
  reward_key TEXT NOT NULL,
  reward_quantity INTEGER NOT NULL DEFAULT 1,
  claimed_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(learner_id, partner_learner_id, quest_key, week_key)
);

CREATE INDEX IF NOT EXISTS idx_friend_quests_learner_week
ON friend_quests (learner_id, week_key);

CREATE TABLE IF NOT EXISTS friend_invites (
  id TEXT PRIMARY KEY,
  requester_learner_id TEXT NOT NULL,
  addressee_learner_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  message TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  responded_at TEXT,
  UNIQUE(requester_learner_id, addressee_learner_id)
);

CREATE INDEX IF NOT EXISTS idx_friend_invites_addressee_status
ON friend_invites (addressee_learner_id, status);

CREATE TABLE IF NOT EXISTS friend_relationships (
  id TEXT PRIMARY KEY,
  learner_a_id TEXT NOT NULL,
  learner_b_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  removed_at TEXT,
  UNIQUE(learner_a_id, learner_b_id)
);

CREATE INDEX IF NOT EXISTS idx_friend_relationships_a_status
ON friend_relationships (learner_a_id, status);

CREATE INDEX IF NOT EXISTS idx_friend_relationships_b_status
ON friend_relationships (learner_b_id, status);

CREATE TABLE IF NOT EXISTS social_settings (
  learner_id TEXT PRIMARY KEY,
  discoverable INTEGER NOT NULL DEFAULT 1,
  allow_friend_invites INTEGER NOT NULL DEFAULT 1,
  show_weekly_xp INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS social_blocks (
  id TEXT PRIMARY KEY,
  blocker_learner_id TEXT NOT NULL,
  blocked_learner_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(blocker_learner_id, blocked_learner_id)
);

CREATE INDEX IF NOT EXISTS idx_social_blocks_blocked
ON social_blocks (blocked_learner_id);

CREATE TABLE IF NOT EXISTS reward_currency_events (
  id TEXT PRIMARY KEY,
  learner_id TEXT NOT NULL,
  currency_key TEXT NOT NULL,
  amount INTEGER NOT NULL,
  reason TEXT NOT NULL,
  source_ref TEXT,
  idempotency_key TEXT UNIQUE,
  metadata_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reward_currency_events_learner_currency
ON reward_currency_events (learner_id, currency_key);

CREATE TABLE IF NOT EXISTS reward_shop_items (
  reward_key TEXT PRIMARY KEY,
  price_currency TEXT NOT NULL DEFAULT 'gems',
  price_amount INTEGER NOT NULL DEFAULT 0,
  available INTEGER NOT NULL DEFAULT 1,
  daily_purchase_limit INTEGER,
  inventory_limit INTEGER,
  starts_at TEXT,
  ends_at TEXT,
  sort_order INTEGER NOT NULL DEFAULT 100,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  updated_by TEXT
);

CREATE TABLE IF NOT EXISTS reward_shop_purchases (
  id TEXT PRIMARY KEY,
  learner_id TEXT NOT NULL,
  reward_key TEXT NOT NULL,
  price_currency TEXT NOT NULL,
  price_amount INTEGER NOT NULL,
  day_key TEXT NOT NULL,
  metadata_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reward_shop_purchases_learner_day
ON reward_shop_purchases (learner_id, reward_key, day_key);

CREATE TABLE IF NOT EXISTS experiments (
  id TEXT PRIMARY KEY,
  key TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',
  variants_json TEXT NOT NULL,
  allocation_json TEXT NOT NULL,
  created_by TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experiment_assignments (
  id TEXT PRIMARY KEY,
  learner_id TEXT NOT NULL,
  experiment_key TEXT NOT NULL,
  variant_key TEXT NOT NULL,
  assigned_at TEXT NOT NULL,
  UNIQUE(learner_id, experiment_key),
  FOREIGN KEY(experiment_key) REFERENCES experiments(key)
);

CREATE TABLE IF NOT EXISTS experiment_events (
  id TEXT PRIMARY KEY,
  learner_id TEXT NOT NULL,
  experiment_key TEXT NOT NULL,
  variant_key TEXT NOT NULL,
  event_name TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(experiment_key) REFERENCES experiments(key)
);

CREATE TABLE IF NOT EXISTS experiment_decisions (
  id TEXT PRIMARY KEY,
  experiment_key TEXT NOT NULL,
  action TEXT NOT NULL,
  variant_key TEXT,
  status TEXT NOT NULL DEFAULT 'proposed',
  reason TEXT,
  minimum_exposed_learners INTEGER NOT NULL,
  analytics_snapshot_json TEXT NOT NULL,
  guardrail_json TEXT NOT NULL,
  created_by TEXT,
  created_at TEXT NOT NULL,
  applied_by TEXT,
  applied_at TEXT,
  apply_note TEXT,
  FOREIGN KEY(experiment_key) REFERENCES experiments(key)
);

CREATE INDEX IF NOT EXISTS idx_experiment_decisions_experiment
ON experiment_decisions (experiment_key, created_at DESC);

CREATE TABLE IF NOT EXISTS tts_cache (
  cache_key TEXT PRIMARY KEY,
  learner_id TEXT DEFAULT 'local-dev',
  text TEXT NOT NULL,
  persona_id TEXT NOT NULL,
  language TEXT NOT NULL,
  speed REAL,
  emotion TEXT,
  content_type TEXT DEFAULT 'audio/wav',
  audio_base64 TEXT NOT NULL,
  duration_ms INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  last_used_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dialogue_unmatched (
  id TEXT PRIMARY KEY,
  learner_id TEXT DEFAULT 'local-dev',
  persona_id TEXT NOT NULL,
  pack_version TEXT NOT NULL,
  node_id TEXT NOT NULL,
  utterance TEXT NOT NULL,
  stt_confidence REAL,
  status TEXT NOT NULL DEFAULT 'new',
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dialogue_unmatched_persona_status
ON dialogue_unmatched (persona_id, status, created_at);

CREATE TABLE IF NOT EXISTS learning_profiles (
  id TEXT PRIMARY KEY,
  native_language TEXT DEFAULT 'ko',
  target_language TEXT DEFAULT 'ja',
  level TEXT DEFAULT 'beginner',
  jlpt_level TEXT DEFAULT 'N5',
  goals_json TEXT NOT NULL,
  weak_tags_json TEXT NOT NULL,
  preferred_persona_id TEXT DEFAULT 'yui',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS grammar_points (
  id TEXT PRIMARY KEY,
  level TEXT NOT NULL,
  data_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS korean_mistake_patterns (
  id TEXT PRIMARY KEY,
  category TEXT NOT NULL,
  data_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id TEXT PRIMARY KEY,
  action TEXT NOT NULL,
  actor TEXT,
  target_type TEXT,
  target_id TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""

DEFAULT_EXPERIMENTS = [
    {
        "key": "daily_recommendation_copy_v1",
        "name": "Daily recommendation copy",
        "status": "running",
        "variants": [
            {
                "key": "control",
                "label": "Current recommendation copy",
                "weight": 50,
                "payload": {"headlineStyle": "neutral"},
            },
            {
                "key": "memory_pressure",
                "label": "Memory pressure copy",
                "weight": 50,
                "payload": {"headlineStyle": "weakness_repair"},
            },
        ],
        "allocation": {"unit": "learner", "saltVersion": "20260629"},
    },
    {
        "key": "practice_room_order_v1",
        "name": "Practice room ordering",
        "status": "running",
        "variants": [
            {
                "key": "control",
                "label": "Current room order",
                "weight": 50,
                "payload": {"sort": "catalog_default"},
            },
            {
                "key": "weakness_first",
                "label": "Weakness-first room order",
                "weight": 50,
                "payload": {"sort": "weakness_first"},
            },
        ],
        "allocation": {"unit": "learner", "saltVersion": "20260629"},
    },
]

DAILY_QUESTS = [
    {
        "key": "complete_practice_turn",
        "title": "Complete one practice turn",
        "metric": "source_count",
        "source": "practice_turn_completed",
        "target": 1,
        "rewardXp": 10,
    },
    {
        "key": "review_one_card",
        "title": "Review one card",
        "metric": "source_count",
        "source": "review_card_graded",
        "target": 1,
        "rewardXp": 10,
    },
    {
        "key": "earn_30_xp",
        "title": "Earn 30 XP",
        "metric": "xp_sum",
        "source": "*",
        "target": 30,
        "rewardXp": 15,
    },
]

ACHIEVEMENTS = [
    {
        "key": "first_steps",
        "title": "First Steps",
        "description": "Complete your first practice turn.",
        "metric": "source_count",
        "source": "practice_turn_completed",
        "target": 1,
        "level": 1,
        "rewardGems": 1,
    },
    {
        "key": "first_steps",
        "title": "First Steps",
        "description": "Complete 3 practice turns.",
        "metric": "source_count",
        "source": "practice_turn_completed",
        "target": 3,
        "level": 2,
        "rewardGems": 2,
    },
    {
        "key": "first_steps",
        "title": "First Steps",
        "description": "Complete 10 practice turns.",
        "metric": "source_count",
        "source": "practice_turn_completed",
        "target": 10,
        "level": 3,
        "rewardGems": 3,
    },
    {
        "key": "review_rookie",
        "title": "Review Rookie",
        "description": "Grade your first review card.",
        "metric": "source_count",
        "source": "review_card_graded",
        "target": 1,
        "level": 1,
        "rewardGems": 1,
    },
    {
        "key": "review_rookie",
        "title": "Review Rookie",
        "description": "Grade 5 review cards.",
        "metric": "source_count",
        "source": "review_card_graded",
        "target": 5,
        "level": 2,
        "rewardGems": 2,
    },
    {
        "key": "xp_rookie",
        "title": "XP Rookie",
        "description": "Earn 30 total XP.",
        "metric": "total_xp",
        "source": "*",
        "target": 30,
        "level": 1,
        "rewardGems": 1,
    },
    {
        "key": "xp_rookie",
        "title": "XP Rookie",
        "description": "Earn 100 total XP.",
        "metric": "total_xp",
        "source": "*",
        "target": 100,
        "level": 2,
        "rewardGems": 2,
    },
    {
        "key": "xp_rookie",
        "title": "XP Rookie",
        "description": "Earn 300 total XP.",
        "metric": "total_xp",
        "source": "*",
        "target": 300,
        "level": 3,
        "rewardGems": 3,
    },
    {
        "key": "quest_kickoff",
        "title": "Quest Kickoff",
        "description": "Complete all starter daily quests.",
        "metric": "quest_count",
        "source": "*",
        "target": 3,
        "level": 1,
        "rewardGems": 1,
    },
    {
        "key": "streak_starter",
        "title": "Streak Starter",
        "description": "Start a daily streak.",
        "metric": "streak_days",
        "source": "*",
        "target": 1,
        "level": 1,
        "rewardGems": 1,
    },
    {
        "key": "streak_starter",
        "title": "Streak Starter",
        "description": "Keep a 3-day streak.",
        "metric": "streak_days",
        "source": "*",
        "target": 3,
        "level": 2,
        "rewardGems": 2,
    },
    {
        "key": "social_starter",
        "title": "Social Starter",
        "description": "Add your first friend.",
        "metric": "friend_count",
        "source": "*",
        "target": 1,
        "level": 1,
        "rewardGems": 1,
    },
    {
        "key": "friend_quester",
        "title": "Friend Quester",
        "description": "Claim your first friend quest reward.",
        "metric": "friend_quest_claim_count",
        "source": "*",
        "target": 1,
        "level": 1,
        "rewardGems": 1,
    },
]

ACHIEVEMENT_MAX_LEVELS = {
    key: max(int(item["level"]) for item in ACHIEVEMENTS if item["key"] == key)
    for key in {item["key"] for item in ACHIEVEMENTS}
}

LEAGUE_TIERS = [
    {"key": "bronze", "name": "Bronze", "minWeeklyXp": 0, "nextKey": "silver"},
    {"key": "silver", "name": "Silver", "minWeeklyXp": 30, "nextKey": "gold"},
    {"key": "gold", "name": "Gold", "minWeeklyXp": 100, "nextKey": "sapphire"},
    {"key": "sapphire", "name": "Sapphire", "minWeeklyXp": 250, "nextKey": "ruby"},
    {"key": "ruby", "name": "Ruby", "minWeeklyXp": 500, "nextKey": None},
]

REWARD_CATALOG = {
    "xp_boost_2x_15m": {
        "key": "xp_boost_2x_15m",
        "type": "xp_boost",
        "title": "2x XP Boost",
        "description": "Double eligible XP for 15 minutes.",
        "multiplier": 2.0,
        "durationSeconds": 15 * 60,
    },
    "streak_freeze_1": {
        "key": "streak_freeze_1",
        "type": "streak_freeze",
        "title": "Streak Freeze",
        "description": "A one-use inventory item reserved for a future streak-freeze client flow.",
    },
}

REWARD_SHOP_CATALOG = [
    {"rewardKey": "xp_boost_2x_15m", "priceCurrency": "gems", "priceAmount": 2, "available": True},
    {"rewardKey": "streak_freeze_1", "priceCurrency": "gems", "priceAmount": 2, "available": True},
]

FRIEND_QUEST_TEMPLATES = [
    {
        "key": "weekly_partner_xp",
        "title": "Weekly Partner XP",
        "targetXp": 40,
        "rewardKey": "xp_boost_2x_15m",
        "rewardQuantity": 1,
    }
]


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def today_key() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def current_week_window() -> tuple[str, str, str]:
    today = dt.datetime.now(dt.timezone.utc).date()
    week_start = today - dt.timedelta(days=today.weekday())
    week_end = week_start + dt.timedelta(days=7)
    return week_start.isoformat(), week_end.isoformat(), week_start.isoformat()


def day_key_from_iso(value: Optional[str]) -> str:
    parsed = parse_iso(value)
    if parsed:
        return parsed.date().isoformat()
    return today_key()


def parse_iso(value: Optional[str]) -> Optional[dt.datetime]:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = dt.datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc)
    except ValueError:
        return None


def clamp_float(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def default_db_path() -> Path:
    configured = os.environ.get("AI_LANGUAGE_PARTNER_DB_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[1] / "data" / "language_partner.sqlite3"


def normalize_learner_id(value: Optional[str]) -> str:
    raw = (value or "local-dev").strip()
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_", ".", "@"} else "_" for ch in raw)
    return cleaned[:80] or "local-dev"


def normalize_experiment_key(value: Optional[str]) -> str:
    raw = (value or "").strip().lower()
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in raw)
    return cleaned[:80]


def normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def wilson_interval(successes: int, total: int, z_value: float = 1.96) -> Dict[str, Optional[float]]:
    if total <= 0:
        return {"lower": None, "upper": None}
    proportion = successes / total
    denominator = 1 + (z_value * z_value / total)
    centre = proportion + (z_value * z_value / (2 * total))
    margin = z_value * math.sqrt((proportion * (1 - proportion) + (z_value * z_value / (4 * total))) / total)
    return {
        "lower": round(max(0.0, (centre - margin) / denominator), 4),
        "upper": round(min(1.0, (centre + margin) / denominator), 4),
    }


def two_proportion_stats(
    baseline_converted: int,
    baseline_exposed: int,
    variant_converted: int,
    variant_exposed: int,
    alpha: float = 0.05,
) -> Dict[str, Any]:
    baseline_rate = baseline_converted / baseline_exposed if baseline_exposed else None
    variant_rate = variant_converted / variant_exposed if variant_exposed else None
    if baseline_rate is None or variant_rate is None:
        return {
            "absoluteLiftFromBaseline": None,
            "relativeLiftFromBaseline": None,
            "standardError": None,
            "zScore": None,
            "pValue": None,
            "confidenceInterval95": {"lower": None, "upper": None},
            "statisticallySignificant": False,
        }
    lift = variant_rate - baseline_rate
    relative_lift = (lift / baseline_rate) if baseline_rate > 0 else None
    pooled = (baseline_converted + variant_converted) / (baseline_exposed + variant_exposed)
    pooled_error = math.sqrt(pooled * (1 - pooled) * ((1 / baseline_exposed) + (1 / variant_exposed)))
    unpooled_error = math.sqrt(
        (baseline_rate * (1 - baseline_rate) / baseline_exposed)
        + (variant_rate * (1 - variant_rate) / variant_exposed)
    )
    if pooled_error <= 0:
        z_score = None
        p_value = None
    else:
        z_score = lift / pooled_error
        p_value = 2 * (1 - normal_cdf(abs(z_score)))
    ci = {
        "lower": round(lift - (1.96 * unpooled_error), 4) if unpooled_error > 0 else round(lift, 4),
        "upper": round(lift + (1.96 * unpooled_error), 4) if unpooled_error > 0 else round(lift, 4),
    }
    return {
        "absoluteLiftFromBaseline": round(lift, 4),
        "relativeLiftFromBaseline": round(relative_lift, 4) if relative_lift is not None else None,
        "standardError": round(pooled_error, 6) if pooled_error > 0 else None,
        "zScore": round(z_score, 4) if z_score is not None else None,
        "pValue": round(p_value, 6) if p_value is not None else None,
        "confidenceInterval95": ci,
        "statisticallySignificant": bool(p_value is not None and p_value <= alpha),
    }


def audit_subject_hash(value: str) -> str:
    digest = hashlib.sha256(normalize_learner_id(value).encode("utf-8")).hexdigest()[:16]
    return f"learner_hash_{digest}"


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _loads(value: Optional[str], default: Any = None) -> Any:
    if value is None:
        return default
    return json.loads(value)


def xp_daily_soft_limit() -> int:
    return int(os.environ.get("AI_LANGUAGE_PARTNER_XP_DAILY_SOFT_LIMIT", "1000"))


def xp_boosted_daily_soft_limit() -> int:
    return int(os.environ.get("AI_LANGUAGE_PARTNER_XP_BOOSTED_DAILY_SOFT_LIMIT", "180"))


def xp_duplicate_payload_soft_limit() -> int:
    return int(os.environ.get("AI_LANGUAGE_PARTNER_XP_DUPLICATE_PAYLOAD_SOFT_LIMIT", "8"))


def xp_daily_boost_activation_soft_limit() -> int:
    return int(os.environ.get("AI_LANGUAGE_PARTNER_XP_DAILY_BOOST_ACTIVATION_SOFT_LIMIT", "3"))


class ApiStore:
    def __init__(self, db_path: Optional[Union[Path, str]] = None):
        self.db_path = Path(db_path) if db_path is not None else default_db_path()
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    @contextmanager
    def connect(self) -> Iterable[sqlite3.Connection]:
        connection = sqlite3.connect(str(self.db_path), timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            self._migrate(conn)
            self._seed(conn)

    def _migrate(self, conn: sqlite3.Connection) -> None:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(review_cards)").fetchall()}
        migrations = {
            "learner_id": "ALTER TABLE review_cards ADD COLUMN learner_id TEXT DEFAULT 'local-dev'",
            "ease_factor": "ALTER TABLE review_cards ADD COLUMN ease_factor REAL DEFAULT 2.5",
            "interval_days": "ALTER TABLE review_cards ADD COLUMN interval_days INTEGER DEFAULT 0",
            "review_count": "ALTER TABLE review_cards ADD COLUMN review_count INTEGER DEFAULT 0",
            "lapses": "ALTER TABLE review_cards ADD COLUMN lapses INTEGER DEFAULT 0",
            "memory_strength_days": "ALTER TABLE review_cards ADD COLUMN memory_strength_days REAL DEFAULT 0.5",
            "memory_difficulty": "ALTER TABLE review_cards ADD COLUMN memory_difficulty REAL DEFAULT 0.65",
            "last_review_quality": "ALTER TABLE review_cards ADD COLUMN last_review_quality INTEGER",
            "last_reviewed_at": "ALTER TABLE review_cards ADD COLUMN last_reviewed_at TEXT",
        }
        for column, statement in migrations.items():
            if column not in columns:
                conn.execute(statement)
        for table in ["conversations", "usage_records", "analytics_events", "tts_cache"]:
            table_columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
            if "learner_id" not in table_columns:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN learner_id TEXT DEFAULT 'local-dev'")
            if table == "tts_cache" and "content_type" not in table_columns:
                conn.execute("ALTER TABLE tts_cache ADD COLUMN content_type TEXT DEFAULT 'audio/wav'")
        session_columns = {row["name"] for row in conn.execute("PRAGMA table_info(account_sessions)").fetchall()}
        if "device_id_hash" not in session_columns:
            conn.execute("ALTER TABLE account_sessions ADD COLUMN device_id_hash TEXT")
        oauth_pkce_columns = {row["name"] for row in conn.execute("PRAGMA table_info(oauth_pkce_requests)").fetchall()}
        if "enterprise_sso_connection_id" not in oauth_pkce_columns:
            conn.execute("ALTER TABLE oauth_pkce_requests ADD COLUMN enterprise_sso_connection_id TEXT")
        auth_attempt_columns = {row["name"] for row in conn.execute("PRAGMA table_info(auth_attempts)").fetchall()}
        if "purpose" not in auth_attempt_columns:
            conn.execute("ALTER TABLE auth_attempts ADD COLUMN purpose TEXT NOT NULL DEFAULT 'login'")
        content_version_columns = {row["name"] for row in conn.execute("PRAGMA table_info(content_versions)").fetchall()}
        content_version_migrations = {
            "created_by": "ALTER TABLE content_versions ADD COLUMN created_by TEXT",
            "submitted_by": "ALTER TABLE content_versions ADD COLUMN submitted_by TEXT",
            "reviewed_by": "ALTER TABLE content_versions ADD COLUMN reviewed_by TEXT",
            "review_note": "ALTER TABLE content_versions ADD COLUMN review_note TEXT",
            "submitted_at": "ALTER TABLE content_versions ADD COLUMN submitted_at TEXT",
            "reviewed_at": "ALTER TABLE content_versions ADD COLUMN reviewed_at TEXT",
            "parent_version_id": "ALTER TABLE content_versions ADD COLUMN parent_version_id TEXT",
            "branch_name": "ALTER TABLE content_versions ADD COLUMN branch_name TEXT",
        }
        for column, statement in content_version_migrations.items():
            if column not in content_version_columns:
                conn.execute(statement)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS content_operation_jobs (
              id TEXT PRIMARY KEY,
              job_type TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'queued',
              priority TEXT NOT NULL DEFAULT 'normal',
              payload_json TEXT NOT NULL DEFAULT '{}',
              result_json TEXT NOT NULL DEFAULT '{}',
              error TEXT,
              created_by TEXT,
              claimed_by TEXT,
              canceled_by TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              claimed_at TEXT,
              completed_at TEXT,
              canceled_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_content_operation_jobs_status_priority
            ON content_operation_jobs (status, priority, created_at)
            """
        )
        xp_flag_columns = {row["name"] for row in conn.execute("PRAGMA table_info(xp_abuse_flags)").fetchall()}
        xp_flag_migrations = {
            "status": "ALTER TABLE xp_abuse_flags ADD COLUMN status TEXT NOT NULL DEFAULT 'open'",
            "reviewed_by": "ALTER TABLE xp_abuse_flags ADD COLUMN reviewed_by TEXT",
            "resolution_note": "ALTER TABLE xp_abuse_flags ADD COLUMN resolution_note TEXT",
            "resolved_at": "ALTER TABLE xp_abuse_flags ADD COLUMN resolved_at TEXT",
        }
        for column, statement in xp_flag_migrations.items():
            if column not in xp_flag_columns:
                conn.execute(statement)
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_xp_abuse_flags_status_created
            ON xp_abuse_flags (status, created_at)
            """
        )
        shop_columns = {row["name"] for row in conn.execute("PRAGMA table_info(reward_shop_items)").fetchall()}
        shop_migrations = {
            "daily_purchase_limit": "ALTER TABLE reward_shop_items ADD COLUMN daily_purchase_limit INTEGER",
            "inventory_limit": "ALTER TABLE reward_shop_items ADD COLUMN inventory_limit INTEGER",
            "starts_at": "ALTER TABLE reward_shop_items ADD COLUMN starts_at TEXT",
            "ends_at": "ALTER TABLE reward_shop_items ADD COLUMN ends_at TEXT",
            "sort_order": "ALTER TABLE reward_shop_items ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 100",
            "updated_by": "ALTER TABLE reward_shop_items ADD COLUMN updated_by TEXT",
        }
        for column, statement in shop_migrations.items():
            if column not in shop_columns:
                conn.execute(statement)
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_reward_shop_purchases_learner_day
            ON reward_shop_purchases (learner_id, reward_key, day_key)
            """
        )

    def _seed(self, conn: sqlite3.Connection) -> None:
        created_at = now_iso()
        for persona in PERSONAS:
            conn.execute(
                """
                INSERT OR REPLACE INTO personas (id, data_json, created_at)
                VALUES (?, ?, COALESCE((SELECT created_at FROM personas WHERE id = ?), ?))
                """,
                (persona["id"], _json(persona), persona["id"], created_at),
            )
        for room in PRACTICE_ROOMS:
            conn.execute(
                """
                INSERT OR REPLACE INTO practice_rooms (id, persona_id, data_json, created_at)
                VALUES (?, ?, ?, COALESCE((SELECT created_at FROM practice_rooms WHERE id = ?), ?))
                """,
                (room["id"], room["personaId"], _json(room), room["id"], created_at),
            )
        for course in COURSE_CATALOG:
            conn.execute(
                """
                INSERT OR REPLACE INTO courses (id, data_json, created_at)
                VALUES (?, ?, COALESCE((SELECT created_at FROM courses WHERE id = ?), ?))
                """,
                (course["id"], _json(course), course["id"], created_at),
            )
        conn.execute(
            """
            INSERT OR IGNORE INTO learning_profiles
            (id, native_language, target_language, level, jlpt_level, goals_json, weak_tags_json, preferred_persona_id, created_at, updated_at)
            VALUES ('local-dev', 'ko', 'ja', 'beginner', 'N5', ?, ?, 'yui', ?, ?)
            """,
            (_json(["daily_speaking", "japanese_friend_conversation"]), _json(["감정표현", "동사시제"]), created_at, created_at),
        )
        for point in JLPT_GRAMMAR_POINTS:
            conn.execute(
                """
                INSERT OR REPLACE INTO grammar_points (id, level, data_json, created_at)
                VALUES (?, ?, ?, COALESCE((SELECT created_at FROM grammar_points WHERE id = ?), ?))
                """,
                (point["id"], point["level"], _json(point), point["id"], created_at),
            )
        for mistake in KOREAN_MISTAKE_PATTERNS:
            conn.execute(
                """
                INSERT OR REPLACE INTO korean_mistake_patterns (id, category, data_json, created_at)
                VALUES (?, ?, ?, COALESCE((SELECT created_at FROM korean_mistake_patterns WHERE id = ?), ?))
                """,
                (mistake["id"], mistake["category"], _json(mistake), mistake["id"], created_at),
            )
        self._upsert_translation_memory_entries(conn, self.translation_memory_entries_from_rooms(PRACTICE_ROOMS), created_by="seed")
        self._seed_reward_shop_items(conn)
        self._seed_experiments(conn)

    def _seed_reward_shop_items(self, conn: sqlite3.Connection) -> None:
        timestamp = now_iso()
        for order, shop_item in enumerate(REWARD_SHOP_CATALOG, start=10):
            conn.execute(
                """
                INSERT OR IGNORE INTO reward_shop_items
                (reward_key, price_currency, price_amount, available, daily_purchase_limit, inventory_limit,
                 starts_at, ends_at, sort_order, created_at, updated_at, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, 'seed')
                """,
                (
                    shop_item["rewardKey"],
                    shop_item.get("priceCurrency", "gems"),
                    int(shop_item.get("priceAmount", 0)),
                    int(bool(shop_item.get("available", True))),
                    shop_item.get("dailyPurchaseLimit"),
                    shop_item.get("inventoryLimit"),
                    order,
                    timestamp,
                    timestamp,
                ),
            )

    def _seed_experiments(self, conn: sqlite3.Connection) -> None:
        timestamp = now_iso()
        for experiment in DEFAULT_EXPERIMENTS:
            variants = self._normalize_experiment_variants(experiment["variants"])
            key = normalize_experiment_key(experiment["key"])
            conn.execute(
                """
                INSERT OR IGNORE INTO experiments
                (id, key, name, status, variants_json, allocation_json, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id("exp"),
                    key,
                    experiment["name"],
                    experiment["status"],
                    _json(variants),
                    _json(experiment.get("allocation") or {}),
                    "seed",
                    timestamp,
                    timestamp,
                ),
            )

    def list_personas(self) -> list[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT data_json FROM personas ORDER BY id").fetchall()
        return [_loads(row["data_json"], {}) for row in rows]

    def get_persona(self, persona_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute("SELECT data_json FROM personas WHERE id = ?", (persona_id,)).fetchone()
        return _loads(row["data_json"], {}) if row else None

    def list_practice_rooms(self) -> list[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT data_json FROM practice_rooms ORDER BY id").fetchall()
        return [_loads(row["data_json"], {}) for row in rows]

    def get_practice_room(self, room_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute("SELECT data_json FROM practice_rooms WHERE id = ?", (room_id,)).fetchone()
        return _loads(row["data_json"], {}) if row else None

    def list_courses(self) -> list[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT data_json FROM courses ORDER BY id").fetchall()
        return [_loads(row["data_json"], {}) for row in rows]

    def get_course(self, course_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute("SELECT data_json FROM courses WHERE id = ?", (course_id,)).fetchone()
        return _loads(row["data_json"], {}) if row else None

    def upsert_content_bundle(self, courses: list[Dict[str, Any]], practice_rooms: list[Dict[str, Any]]) -> Dict[str, int]:
        timestamp = now_iso()
        with self.connect() as conn:
            self._upsert_content_bundle_with_conn(conn, courses, practice_rooms, timestamp=timestamp)
        return {"courses": len(courses), "practiceRooms": len(practice_rooms)}

    def replace_content_bundle(self, courses: list[Dict[str, Any]], practice_rooms: list[Dict[str, Any]]) -> Dict[str, int]:
        timestamp = now_iso()
        with self.connect() as conn:
            self._replace_content_bundle_with_conn(conn, courses, practice_rooms, timestamp=timestamp)
        return {"courses": len(courses), "practiceRooms": len(practice_rooms)}

    def _replace_content_bundle_with_conn(
        self,
        conn: sqlite3.Connection,
        courses: list[Dict[str, Any]],
        practice_rooms: list[Dict[str, Any]],
        timestamp: Optional[str] = None,
    ) -> None:
        course_ids = {course["id"] for course in courses}
        room_ids = {room["id"] for room in practice_rooms}
        existing_course_ids = {row["id"] for row in conn.execute("SELECT id FROM courses").fetchall()}
        existing_room_ids = {row["id"] for row in conn.execute("SELECT id FROM practice_rooms").fetchall()}
        for course_id in sorted(existing_course_ids - course_ids):
            conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        for room_id in sorted(existing_room_ids - room_ids):
            conn.execute("DELETE FROM practice_rooms WHERE id = ?", (room_id,))
        self._upsert_content_bundle_with_conn(conn, courses, practice_rooms, timestamp=timestamp)

    def _upsert_content_bundle_with_conn(
        self,
        conn: sqlite3.Connection,
        courses: list[Dict[str, Any]],
        practice_rooms: list[Dict[str, Any]],
        timestamp: Optional[str] = None,
    ) -> None:
        current_timestamp = timestamp or now_iso()
        for room in practice_rooms:
            conn.execute(
                """
                INSERT OR REPLACE INTO practice_rooms (id, persona_id, data_json, created_at)
                VALUES (?, ?, ?, COALESCE((SELECT created_at FROM practice_rooms WHERE id = ?), ?))
                """,
                (room["id"], room["personaId"], _json(room), room["id"], current_timestamp),
            )
        for course in courses:
            conn.execute(
                """
                INSERT OR REPLACE INTO courses (id, data_json, created_at)
                VALUES (?, ?, COALESCE((SELECT created_at FROM courses WHERE id = ?), ?))
                """,
                (course["id"], _json(course), course["id"], current_timestamp),
            )
        self._upsert_translation_memory_entries(conn, self.translation_memory_entries_from_rooms(practice_rooms), created_by="content_import")

    def translation_memory_entries_from_rooms(self, practice_rooms: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        entries: list[Dict[str, Any]] = []
        for room in practice_rooms:
            if not isinstance(room, dict):
                continue
            source_text = str(room.get("primaryPhraseKo") or "").strip()
            primary_target = str(room.get("primaryPhraseJa") or "").strip()
            if not source_text or not primary_target:
                continue
            tags = [tag for tag in room.get("tags") or [] if isinstance(tag, str) and tag.strip()]
            source_ref = str(room.get("id") or "").strip() or None
            targets = [primary_target]
            for alternative in room.get("alternativePhrasesJa") or []:
                if isinstance(alternative, str) and alternative.strip() and alternative.strip() not in targets:
                    targets.append(alternative.strip())
            for target_text in targets:
                entries.append(
                    {
                        "sourceLanguage": "ko",
                        "targetLanguage": "ja",
                        "sourceText": source_text,
                        "targetText": target_text,
                        "tags": tags,
                        "sourceRef": source_ref,
                        "quality": 100,
                    }
                )
        return entries

    def _upsert_translation_memory_entries(
        self,
        conn: sqlite3.Connection,
        entries: list[Dict[str, Any]],
        created_by: str = "content_admin",
    ) -> int:
        timestamp = now_iso()
        written = 0
        for entry in entries:
            source_text = str(entry.get("sourceText") or "").strip()
            target_text = str(entry.get("targetText") or "").strip()
            if not source_text or not target_text:
                continue
            source_language = str(entry.get("sourceLanguage") or "ko").strip().lower()[:8] or "ko"
            target_language = str(entry.get("targetLanguage") or "ja").strip().lower()[:8] or "ja"
            tags = [tag.strip() for tag in entry.get("tags") or [] if isinstance(tag, str) and tag.strip()]
            quality = max(0, min(100, int(entry.get("quality", 100))))
            conn.execute(
                """
                INSERT INTO translation_memory
                (id, source_language, target_language, source_text, target_text, tags_json, source_ref, quality, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_language, target_language, source_text, target_text)
                DO UPDATE SET
                  tags_json = excluded.tags_json,
                  source_ref = COALESCE(excluded.source_ref, translation_memory.source_ref),
                  quality = MAX(translation_memory.quality, excluded.quality),
                  updated_at = excluded.updated_at
                """,
                (
                    new_id("tm"),
                    source_language,
                    target_language,
                    source_text,
                    target_text,
                    _json(tags),
                    entry.get("sourceRef"),
                    quality,
                    created_by,
                    timestamp,
                    timestamp,
                ),
            )
            written += 1
        return written

    def upsert_translation_memory_entries(
        self,
        entries: list[Dict[str, Any]],
        created_by: str = "content_admin",
    ) -> Dict[str, int]:
        with self.connect() as conn:
            written = self._upsert_translation_memory_entries(conn, entries, created_by=created_by)
        return {"entries": written}

    def list_translation_memory(
        self,
        query: Optional[str] = None,
        source_language: str = "ko",
        target_language: str = "ja",
        limit: int = 50,
    ) -> list[Dict[str, Any]]:
        normalized_query = (query or "").strip()
        with self.connect() as conn:
            normalized_source_language = (source_language or "ko").strip().lower()[:8] or "ko"
            normalized_target_language = (target_language or "ja").strip().lower()[:8] or "ja"
            params: list[Any] = [normalized_source_language, normalized_target_language]
            where = "WHERE source_language = ? AND target_language = ?"
            if normalized_query:
                where += " AND (source_text LIKE ? OR target_text LIKE ?)"
                like = f"%{normalized_query}%"
                params.extend([like, like])
            params.append(max(1, min(200, int(limit))))
            rows = conn.execute(
                f"""
                SELECT *
                FROM translation_memory
                {where}
                ORDER BY updated_at DESC, source_text ASC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._row_to_translation_memory(row) for row in rows]

    def suggest_translation_memory(
        self,
        source_text: str,
        source_language: str = "ko",
        target_language: str = "ja",
        limit: int = 5,
    ) -> list[Dict[str, Any]]:
        query = (source_text or "").strip()
        if not query:
            return []
        entries = self.list_translation_memory(source_language=source_language, target_language=target_language, limit=200)
        normalized_query = self._normalize_tm_text(query)
        scored: list[Dict[str, Any]] = []
        for entry in entries:
            normalized_source = self._normalize_tm_text(entry["sourceText"])
            exact = normalized_source == normalized_query
            contains = normalized_query in normalized_source or normalized_source in normalized_query
            score = SequenceMatcher(None, normalized_query, normalized_source).ratio()
            if exact:
                score = 1.0
            elif contains:
                score = max(score, 0.82)
            if score >= 0.45:
                suggested = dict(entry)
                suggested["similarityScore"] = round(score, 3)
                suggested["matchType"] = "exact" if exact else "fuzzy"
                scored.append(suggested)
        scored.sort(key=lambda item: (-float(item["similarityScore"]), -int(item.get("quality") or 0), item["sourceText"]))
        return scored[: max(1, min(20, int(limit)))]

    def _normalize_tm_text(self, value: str) -> str:
        return "".join(ch.lower() for ch in value.strip() if not ch.isspace())

    def _row_to_translation_memory(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "sourceLanguage": row["source_language"],
            "targetLanguage": row["target_language"],
            "sourceText": row["source_text"],
            "targetText": row["target_text"],
            "tags": _loads(row["tags_json"], []),
            "sourceRef": row["source_ref"],
            "quality": row["quality"],
            "createdBy": row["created_by"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }

    def create_content_version(
        self,
        courses: list[Dict[str, Any]],
        practice_rooms: list[Dict[str, Any]],
        report: Dict[str, Any],
        imported_counts: Dict[str, int],
        source: str,
        label: Optional[str] = None,
        status: str = "draft",
        created_by: Optional[str] = None,
        parent_version_id: Optional[str] = None,
        branch_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        timestamp = now_iso()
        normalized_status = status if status in {"draft", "in_review", "approved", "rejected", "published"} else "draft"
        published_at = timestamp if normalized_status == "published" else None
        version_id = new_id("contentver")
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO content_versions
                (id, label, status, parent_version_id, branch_name, courses_json, practice_rooms_json, report_json, imported_counts_json, source,
                 created_by, created_at, published_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    label,
                    normalized_status,
                    parent_version_id,
                    branch_name,
                    _json(courses),
                    _json(practice_rooms),
                    _json(report),
                    _json(imported_counts),
                    source,
                    created_by,
                    timestamp,
                    published_at,
                ),
            )
        created = self.get_content_version(version_id)
        if not created:
            raise RuntimeError("content version was not created")
        return created

    def create_content_branch(
        self,
        parent_version: Dict[str, Any],
        actor: str,
        label: Optional[str] = None,
        branch_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        parent_id = parent_version["id"]
        normalized_branch_name = (branch_name or f"branch-from-{parent_id}").strip()[:120]
        branch_label = label or f"Branch from {parent_id}"
        report = _loads(_json(parent_version.get("report") or {}), {})
        return self.create_content_version(
            parent_version["courses"],
            parent_version["practiceRooms"],
            report,
            {"courses": 0, "practiceRooms": 0},
            source="content_branch",
            label=branch_label,
            status="draft",
            created_by=actor,
            parent_version_id=parent_id,
            branch_name=normalized_branch_name,
        )

    def list_content_versions(self, limit: int = 50) -> list[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM content_versions
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (max(1, min(200, int(limit))),),
            ).fetchall()
        return [self._row_to_content_version(row, include_snapshot=False) for row in rows]

    def get_content_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM content_versions WHERE id = ?", (version_id,)).fetchone()
        return self._row_to_content_version(row, include_snapshot=True) if row else None

    def submit_content_version_for_review(self, version_id: str, actor: str, note: Optional[str] = None) -> Optional[Dict[str, Any]]:
        timestamp = now_iso()
        with self.connect() as conn:
            result = conn.execute(
                """
                UPDATE content_versions
                SET status = 'in_review', submitted_by = ?, submitted_at = ?, review_note = ?
                WHERE id = ? AND status IN ('draft', 'rejected')
                """,
                (actor, timestamp, note, version_id),
            )
        return self.get_content_version(version_id) if result.rowcount else None

    def approve_content_version(self, version_id: str, actor: str, note: Optional[str] = None) -> Optional[Dict[str, Any]]:
        timestamp = now_iso()
        with self.connect() as conn:
            result = conn.execute(
                """
                UPDATE content_versions
                SET status = 'approved', reviewed_by = ?, reviewed_at = ?, review_note = COALESCE(?, review_note)
                WHERE id = ? AND status = 'in_review'
                """,
                (actor, timestamp, note, version_id),
            )
        return self.get_content_version(version_id) if result.rowcount else None

    def reject_content_version(self, version_id: str, actor: str, note: Optional[str] = None) -> Optional[Dict[str, Any]]:
        timestamp = now_iso()
        with self.connect() as conn:
            result = conn.execute(
                """
                UPDATE content_versions
                SET status = 'rejected', reviewed_by = ?, reviewed_at = ?, review_note = COALESCE(?, review_note)
                WHERE id = ? AND status = 'in_review'
                """,
                (actor, timestamp, note, version_id),
            )
        return self.get_content_version(version_id) if result.rowcount else None

    def publish_content_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        version = self.get_content_version(version_id)
        if not version:
            return None
        imported_counts = self.upsert_content_bundle(version["courses"], version["practiceRooms"])
        published_at = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE content_versions
                SET status = 'published', published_at = ?, imported_counts_json = ?
                WHERE id = ?
                """,
                (published_at, _json(imported_counts), version_id),
            )
        return self.get_content_version(version_id)

    def create_content_release(
        self,
        version_id: str,
        title: str,
        release_strategy: str = "immediate",
        rollout_percent: int = 100,
        catalog_scope: str = "incremental",
        scheduled_at: Optional[str] = None,
        guardrails: Optional[Dict[str, Any]] = None,
        note: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        timestamp = now_iso()
        normalized_strategy = release_strategy if release_strategy in {"immediate", "scheduled", "canary"} else "immediate"
        normalized_scope = catalog_scope if catalog_scope in {"incremental", "full_catalog"} else "incremental"
        normalized_rollout = max(1, min(100, int(rollout_percent)))
        status = "scheduled" if normalized_strategy == "scheduled" else "planned"
        release_id = new_id("contentrel")
        with self.connect() as conn:
            if not conn.execute("SELECT 1 FROM content_versions WHERE id = ?", (version_id,)).fetchone():
                raise ValueError("content version not found")
            conn.execute(
                """
                INSERT INTO content_releases
                (id, version_id, title, status, release_strategy, rollout_percent, catalog_scope,
                 scheduled_at, guardrails_json, note, imported_counts_json, rollback_imported_counts_json,
                 created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    release_id,
                    version_id,
                    title.strip()[:160] or f"Release {version_id}",
                    status,
                    normalized_strategy,
                    normalized_rollout,
                    normalized_scope,
                    scheduled_at,
                    _json(guardrails or {}),
                    note,
                    _json({}),
                    _json({}),
                    created_by,
                    timestamp,
                ),
            )
        release = self.get_content_release(release_id)
        if not release:
            raise RuntimeError("content release was not created")
        return release

    def list_content_releases(self, status: Optional[str] = None, limit: int = 50) -> list[Dict[str, Any]]:
        filters = []
        params: list[Any] = []
        if status:
            filters.append("status = ?")
            params.append(status)
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        params.append(max(1, min(200, int(limit))))
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT *
                FROM content_releases
                {where}
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._row_to_content_release(row) for row in rows]

    def get_content_release(self, release_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM content_releases WHERE id = ?", (release_id,)).fetchone()
        return self._row_to_content_release(row) if row else None

    def apply_content_release(self, release_id: str, actor: Optional[str], force: bool = False) -> Optional[Dict[str, Any]]:
        timestamp = now_iso()
        with self.connect() as conn:
            release_row = conn.execute("SELECT * FROM content_releases WHERE id = ?", (release_id,)).fetchone()
            if not release_row:
                return None
            release = self._row_to_content_release(release_row)
            if release["status"] in {"applied", "rolled_back", "canceled"}:
                raise ValueError("content release is already finalized")
            scheduled_for = parse_iso(release.get("scheduledAt"))
            if scheduled_for and scheduled_for > dt.datetime.now(dt.timezone.utc) and not force:
                raise ValueError("content release is scheduled for a future time")
            version_row = conn.execute("SELECT * FROM content_versions WHERE id = ?", (release["versionId"],)).fetchone()
            if not version_row:
                raise ValueError("content version not found")
            version = self._row_to_content_version(version_row, include_snapshot=True)
            if version["status"] not in {"approved", "published"}:
                raise ValueError("content version must be approved before release")
            previous_version = self._latest_published_content_version_with_conn(conn, exclude_version_id=version["id"])
            imported_counts = {"courses": len(version["courses"]), "practiceRooms": len(version["practiceRooms"])}
            if release["catalogScope"] == "full_catalog":
                self._replace_content_bundle_with_conn(conn, version["courses"], version["practiceRooms"], timestamp=timestamp)
            else:
                self._upsert_content_bundle_with_conn(conn, version["courses"], version["practiceRooms"], timestamp=timestamp)
            conn.execute(
                """
                UPDATE content_versions
                SET status = 'published', published_at = ?, imported_counts_json = ?
                WHERE id = ?
                """,
                (timestamp, _json(imported_counts), version["id"]),
            )
            conn.execute(
                """
                UPDATE content_releases
                SET status = 'applied',
                    previous_published_version_id = ?,
                    imported_counts_json = ?,
                    applied_by = ?,
                    applied_at = ?
                WHERE id = ?
                """,
                (
                    previous_version["id"] if previous_version else None,
                    _json(imported_counts),
                    actor,
                    timestamp,
                    release_id,
                ),
            )
        applied = self.get_content_release(release_id)
        if applied:
            applied["version"] = self.get_content_version(applied["versionId"])
            applied["previousPublishedVersion"] = (
                self.get_content_version(applied["previousPublishedVersionId"]) if applied.get("previousPublishedVersionId") else None
            )
        return applied

    def run_due_content_releases(self, actor: Optional[str], limit: int = 50) -> Dict[str, Any]:
        ran_at = now_iso()
        now_dt = parse_iso(ran_at) or dt.datetime.now(dt.timezone.utc)
        capped_limit = max(1, min(200, int(limit)))
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM content_releases
                WHERE status IN ('planned', 'scheduled')
                ORDER BY COALESCE(scheduled_at, created_at) ASC, created_at ASC, id ASC
                LIMIT ?
                """,
                (capped_limit,),
            ).fetchall()
        pending = [self._row_to_content_release(row) for row in rows]
        applied: list[Dict[str, Any]] = []
        skipped: list[Dict[str, Any]] = []
        for release in pending:
            scheduled_for = parse_iso(release.get("scheduledAt"))
            if release["releaseStrategy"] == "scheduled" and not scheduled_for:
                skipped.append({"releaseId": release["id"], "reason": "missing_scheduled_at"})
                continue
            if scheduled_for and scheduled_for > now_dt:
                skipped.append({"releaseId": release["id"], "reason": "not_due", "scheduledAt": release["scheduledAt"]})
                continue
            try:
                applied_release = self.apply_content_release(release["id"], actor=actor, force=False)
            except ValueError as exc:
                skipped.append({"releaseId": release["id"], "reason": str(exc)})
                continue
            if applied_release:
                applied.append(applied_release)
        return {
            "ranAt": ran_at,
            "checkedCount": len(pending),
            "appliedCount": len(applied),
            "skippedCount": len(skipped),
            "appliedReleases": applied,
            "skipped": skipped,
        }

    def create_content_operation_job(
        self,
        job_type: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        normalized_type = job_type if job_type in {"validate_bundle", "import_bundle", "run_due_releases"} else "validate_bundle"
        normalized_priority = priority if priority in {"low", "normal", "high", "urgent"} else "normal"
        timestamp = now_iso()
        job_id = new_id("contentjob")
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO content_operation_jobs
                (id, job_type, status, priority, payload_json, result_json, created_by, created_at, updated_at)
                VALUES (?, ?, 'queued', ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    normalized_type,
                    normalized_priority,
                    _json(payload or {}),
                    _json({}),
                    created_by,
                    timestamp,
                    timestamp,
                ),
            )
        created = self.get_content_operation_job(job_id)
        if not created:
            raise RuntimeError("content operation job was not created")
        return created

    def list_content_operation_jobs(self, status: Optional[str] = None, limit: int = 50) -> list[Dict[str, Any]]:
        filters = []
        params: list[Any] = []
        if status:
            filters.append("status = ?")
            params.append(status)
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        params.append(max(1, min(200, int(limit))))
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT *
                FROM content_operation_jobs
                {where}
                ORDER BY
                  CASE priority
                    WHEN 'urgent' THEN 0
                    WHEN 'high' THEN 1
                    WHEN 'normal' THEN 2
                    ELSE 3
                  END,
                  created_at ASC,
                  id ASC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._row_to_content_operation_job(row) for row in rows]

    def get_content_operation_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM content_operation_jobs WHERE id = ?", (job_id,)).fetchone()
        return self._row_to_content_operation_job(row) if row else None

    def claim_next_content_operation_job(self, actor: Optional[str]) -> Optional[Dict[str, Any]]:
        timestamp = now_iso()
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM content_operation_jobs
                WHERE status = 'queued'
                ORDER BY
                  CASE priority
                    WHEN 'urgent' THEN 0
                    WHEN 'high' THEN 1
                    WHEN 'normal' THEN 2
                    ELSE 3
                  END,
                  created_at ASC,
                  id ASC
                LIMIT 1
                """
            ).fetchone()
            if not row:
                return None
            result = conn.execute(
                """
                UPDATE content_operation_jobs
                SET status = 'running', claimed_by = ?, claimed_at = ?, updated_at = ?
                WHERE id = ? AND status = 'queued'
                """,
                (actor, timestamp, timestamp, row["id"]),
            )
            if not result.rowcount:
                return None
        return self.get_content_operation_job(row["id"])

    def complete_content_operation_job(self, job_id: str, result_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        timestamp = now_iso()
        with self.connect() as conn:
            result = conn.execute(
                """
                UPDATE content_operation_jobs
                SET status = 'succeeded', result_json = ?, error = NULL, updated_at = ?, completed_at = ?
                WHERE id = ? AND status = 'running'
                """,
                (_json(result_payload), timestamp, timestamp, job_id),
            )
        return self.get_content_operation_job(job_id) if result.rowcount else None

    def fail_content_operation_job(self, job_id: str, error: str, result_payload: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        timestamp = now_iso()
        with self.connect() as conn:
            result = conn.execute(
                """
                UPDATE content_operation_jobs
                SET status = 'failed', result_json = ?, error = ?, updated_at = ?, completed_at = ?
                WHERE id = ? AND status = 'running'
                """,
                (_json(result_payload or {}), error[:1000], timestamp, timestamp, job_id),
            )
        return self.get_content_operation_job(job_id) if result.rowcount else None

    def cancel_content_operation_job(self, job_id: str, actor: Optional[str]) -> Optional[Dict[str, Any]]:
        timestamp = now_iso()
        with self.connect() as conn:
            result = conn.execute(
                """
                UPDATE content_operation_jobs
                SET status = 'canceled', canceled_by = ?, canceled_at = ?, updated_at = ?
                WHERE id = ? AND status = 'queued'
                """,
                (actor, timestamp, timestamp, job_id),
            )
        return self.get_content_operation_job(job_id) if result.rowcount else None

    def start_content_scheduler_run(
        self,
        scheduler_key: str,
        lease_owner: str,
        actor: Optional[str],
        max_operation_jobs: int = 1,
        release_limit: int = 50,
        lease_ttl_seconds: int = 300,
    ) -> Dict[str, Any]:
        timestamp = now_iso()
        now_dt = parse_iso(timestamp) or dt.datetime.now(dt.timezone.utc)
        stale_before = (now_dt - dt.timedelta(seconds=max(30, int(lease_ttl_seconds)))).isoformat().replace("+00:00", "Z")
        normalized_key = (scheduler_key or "content_ops").strip()[:80] or "content_ops"
        normalized_owner = (lease_owner or "local-scheduler").strip()[:120] or "local-scheduler"
        capped_jobs = max(0, min(20, int(max_operation_jobs)))
        capped_release_limit = max(1, min(200, int(release_limit)))
        run_id = new_id("schedrun")
        with self.connect() as conn:
            active = conn.execute(
                """
                SELECT *
                FROM content_scheduler_runs
                WHERE scheduler_key = ? AND status = 'running' AND heartbeat_at >= ?
                ORDER BY started_at DESC, id DESC
                LIMIT 1
                """,
                (normalized_key, stale_before),
            ).fetchone()
            if active:
                active_run = self._row_to_content_scheduler_run(active)
                raise ValueError(f"content scheduler already running: {active_run['id']}")
            conn.execute(
                """
                INSERT INTO content_scheduler_runs
                (id, scheduler_key, status, lease_owner, actor, started_at, heartbeat_at,
                 max_operation_jobs, release_limit, result_json)
                VALUES (?, ?, 'running', ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    normalized_key,
                    normalized_owner,
                    actor,
                    timestamp,
                    timestamp,
                    capped_jobs,
                    capped_release_limit,
                    _json({}),
                ),
            )
        run = self.get_content_scheduler_run(run_id)
        if not run:
            raise RuntimeError("content scheduler run was not created")
        return run

    def complete_content_scheduler_run(
        self,
        run_id: str,
        result_payload: Dict[str, Any],
        status: str = "succeeded",
        error: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        timestamp = now_iso()
        normalized_status = status if status in {"succeeded", "failed"} else "succeeded"
        with self.connect() as conn:
            result = conn.execute(
                """
                UPDATE content_scheduler_runs
                SET status = ?, result_json = ?, error = ?, heartbeat_at = ?, completed_at = ?
                WHERE id = ? AND status = 'running'
                """,
                (normalized_status, _json(result_payload), error[:1000] if error else None, timestamp, timestamp, run_id),
            )
        return self.get_content_scheduler_run(run_id) if result.rowcount else None

    def get_content_scheduler_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM content_scheduler_runs WHERE id = ?", (run_id,)).fetchone()
        return self._row_to_content_scheduler_run(row) if row else None

    def list_content_scheduler_runs(self, status: Optional[str] = None, limit: int = 50) -> list[Dict[str, Any]]:
        filters = []
        params: list[Any] = []
        if status:
            filters.append("status = ?")
            params.append(status)
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        params.append(max(1, min(200, int(limit))))
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT *
                FROM content_scheduler_runs
                {where}
                ORDER BY started_at DESC, id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._row_to_content_scheduler_run(row) for row in rows]

    def rollback_content_release(self, release_id: str, actor: Optional[str], note: Optional[str] = None) -> Optional[Dict[str, Any]]:
        timestamp = now_iso()
        with self.connect() as conn:
            release_row = conn.execute("SELECT * FROM content_releases WHERE id = ?", (release_id,)).fetchone()
            if not release_row:
                return None
            release = self._row_to_content_release(release_row)
            if release["status"] != "applied":
                raise ValueError("only applied content releases can be rolled back")
            previous_id = release.get("previousPublishedVersionId")
            if not previous_id:
                raise ValueError("content release has no previous published version to roll back to")
            previous_row = conn.execute("SELECT * FROM content_versions WHERE id = ?", (previous_id,)).fetchone()
            if not previous_row:
                raise ValueError("previous published content version not found")
            previous = self._row_to_content_version(previous_row, include_snapshot=True)
            imported_counts = {"courses": len(previous["courses"]), "practiceRooms": len(previous["practiceRooms"])}
            if release["catalogScope"] == "full_catalog":
                self._replace_content_bundle_with_conn(conn, previous["courses"], previous["practiceRooms"], timestamp=timestamp)
            else:
                self._upsert_content_bundle_with_conn(conn, previous["courses"], previous["practiceRooms"], timestamp=timestamp)
            conn.execute(
                """
                UPDATE content_versions
                SET status = 'published', published_at = ?, imported_counts_json = ?
                WHERE id = ?
                """,
                (timestamp, _json(imported_counts), previous["id"]),
            )
            conn.execute(
                """
                UPDATE content_releases
                SET status = 'rolled_back',
                    rollback_imported_counts_json = ?,
                    rolled_back_by = ?,
                    rolled_back_at = ?,
                    rollback_note = ?
                WHERE id = ?
                """,
                (_json(imported_counts), actor, timestamp, note, release_id),
            )
        rolled_back = self.get_content_release(release_id)
        if rolled_back:
            rolled_back["version"] = self.get_content_version(rolled_back["versionId"])
            rolled_back["previousPublishedVersion"] = self.get_content_version(rolled_back["previousPublishedVersionId"])
        return rolled_back

    def _latest_published_content_version_with_conn(
        self,
        conn: sqlite3.Connection,
        exclude_version_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if exclude_version_id:
            row = conn.execute(
                """
                SELECT *
                FROM content_versions
                WHERE status = 'published' AND published_at IS NOT NULL AND id != ?
                ORDER BY published_at DESC, created_at DESC, id DESC
                LIMIT 1
                """,
                (exclude_version_id,),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT *
                FROM content_versions
                WHERE status = 'published' AND published_at IS NOT NULL
                ORDER BY published_at DESC, created_at DESC, id DESC
                LIMIT 1
                """
            ).fetchone()
        return self._row_to_content_version(row, include_snapshot=True) if row else None

    def _row_to_content_release(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "versionId": row["version_id"],
            "title": row["title"],
            "status": row["status"],
            "releaseStrategy": row["release_strategy"],
            "rolloutPercent": row["rollout_percent"],
            "catalogScope": row["catalog_scope"],
            "scheduledAt": row["scheduled_at"],
            "guardrails": _loads(row["guardrails_json"], {}),
            "note": row["note"],
            "previousPublishedVersionId": row["previous_published_version_id"],
            "importedCounts": _loads(row["imported_counts_json"], {}),
            "rollbackImportedCounts": _loads(row["rollback_imported_counts_json"], {}),
            "createdBy": row["created_by"],
            "appliedBy": row["applied_by"],
            "rolledBackBy": row["rolled_back_by"],
            "createdAt": row["created_at"],
            "appliedAt": row["applied_at"],
            "rolledBackAt": row["rolled_back_at"],
            "rollbackNote": row["rollback_note"],
        }

    def _row_to_content_operation_job(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "jobType": row["job_type"],
            "status": row["status"],
            "priority": row["priority"],
            "payload": _loads(row["payload_json"], {}),
            "result": _loads(row["result_json"], {}),
            "error": row["error"],
            "createdBy": row["created_by"],
            "claimedBy": row["claimed_by"],
            "canceledBy": row["canceled_by"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
            "claimedAt": row["claimed_at"],
            "completedAt": row["completed_at"],
            "canceledAt": row["canceled_at"],
        }

    def _row_to_content_scheduler_run(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "schedulerKey": row["scheduler_key"],
            "status": row["status"],
            "leaseOwner": row["lease_owner"],
            "actor": row["actor"],
            "startedAt": row["started_at"],
            "heartbeatAt": row["heartbeat_at"],
            "completedAt": row["completed_at"],
            "maxOperationJobs": row["max_operation_jobs"],
            "releaseLimit": row["release_limit"],
            "result": _loads(row["result_json"], {}),
            "error": row["error"],
        }

    def _row_to_content_version(self, row: sqlite3.Row, include_snapshot: bool = False) -> Dict[str, Any]:
        courses = _loads(row["courses_json"], [])
        practice_rooms = _loads(row["practice_rooms_json"], [])
        version = {
            "id": row["id"],
            "label": row["label"],
            "status": row["status"],
            "parentVersionId": row["parent_version_id"],
            "branchName": row["branch_name"],
            "source": row["source"],
            "createdBy": row["created_by"],
            "submittedBy": row["submitted_by"],
            "reviewedBy": row["reviewed_by"],
            "reviewNote": row["review_note"],
            "createdAt": row["created_at"],
            "submittedAt": row["submitted_at"],
            "reviewedAt": row["reviewed_at"],
            "publishedAt": row["published_at"],
            "importedCounts": _loads(row["imported_counts_json"], {"courses": 0, "practiceRooms": 0}),
            "report": _loads(row["report_json"], {}),
            "snapshotCounts": {
                "courses": len(courses),
                "practiceRooms": len(practice_rooms),
            },
        }
        if include_snapshot:
            version["courses"] = courses
            version["practiceRooms"] = practice_rooms
        return version

    def upsert_content_assignment(
        self,
        version_id: str,
        assignee: str,
        actor: str,
        priority: str = "normal",
        due_at: Optional[str] = None,
        note: Optional[str] = None,
        status: str = "todo",
    ) -> Dict[str, Any]:
        timestamp = now_iso()
        normalized_assignee = (assignee or "").strip()[:120]
        if not normalized_assignee:
            raise ValueError("assignee is required")
        normalized_priority = priority if priority in {"low", "normal", "high", "urgent"} else "normal"
        normalized_status = status if status in {"todo", "in_progress", "blocked", "done"} else "todo"
        completed_at = timestamp if normalized_status == "done" else None
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO content_assignments
                (id, version_id, assignee, status, priority, note, due_at, created_by, updated_by, created_at, updated_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(version_id)
                DO UPDATE SET
                  assignee = excluded.assignee,
                  status = excluded.status,
                  priority = excluded.priority,
                  note = excluded.note,
                  due_at = excluded.due_at,
                  updated_by = excluded.updated_by,
                  updated_at = excluded.updated_at,
                  completed_at = excluded.completed_at
                """,
                (
                    new_id("contentasgn"),
                    version_id,
                    normalized_assignee,
                    normalized_status,
                    normalized_priority,
                    note,
                    due_at,
                    actor,
                    actor,
                    timestamp,
                    timestamp,
                    completed_at,
                ),
            )
        assignment = self.get_content_assignment_by_version(version_id)
        if not assignment:
            raise RuntimeError("content assignment was not created")
        return assignment

    def update_content_assignment_status(
        self,
        assignment_id: str,
        status: str,
        actor: str,
        note: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        timestamp = now_iso()
        normalized_status = status if status in {"todo", "in_progress", "blocked", "done"} else ""
        if not normalized_status:
            return None
        completed_at = timestamp if normalized_status == "done" else None
        with self.connect() as conn:
            result = conn.execute(
                """
                UPDATE content_assignments
                SET status = ?,
                    note = COALESCE(?, note),
                    updated_by = ?,
                    updated_at = ?,
                    completed_at = ?
                WHERE id = ?
                """,
                (normalized_status, note, actor, timestamp, completed_at, assignment_id),
            )
        return self.get_content_assignment(assignment_id) if result.rowcount else None

    def get_content_assignment(self, assignment_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT a.*, v.status AS version_status, v.label AS version_label, v.parent_version_id, v.branch_name
                FROM content_assignments a
                JOIN content_versions v ON v.id = a.version_id
                WHERE a.id = ?
                """,
                (assignment_id,),
            ).fetchone()
        return self._row_to_content_assignment(row) if row else None

    def get_content_assignment_by_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT a.*, v.status AS version_status, v.label AS version_label, v.parent_version_id, v.branch_name
                FROM content_assignments a
                JOIN content_versions v ON v.id = a.version_id
                WHERE a.version_id = ?
                """,
                (version_id,),
            ).fetchone()
        return self._row_to_content_assignment(row) if row else None

    def list_content_assignments(
        self,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
        limit: int = 50,
    ) -> list[Dict[str, Any]]:
        filters = []
        params: list[Any] = []
        if status:
            filters.append("a.status = ?")
            params.append(status)
        if assignee:
            filters.append("a.assignee = ?")
            params.append(assignee)
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        params.append(max(1, min(200, int(limit))))
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT a.*, v.status AS version_status, v.label AS version_label, v.parent_version_id, v.branch_name
                FROM content_assignments a
                JOIN content_versions v ON v.id = a.version_id
                {where}
                ORDER BY
                  CASE a.priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'normal' THEN 2 ELSE 3 END,
                  COALESCE(a.due_at, '9999-12-31T23:59:59Z') ASC,
                  a.updated_at DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._row_to_content_assignment(row) for row in rows]

    def _row_to_content_assignment(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "versionId": row["version_id"],
            "versionStatus": row["version_status"],
            "versionLabel": row["version_label"],
            "parentVersionId": row["parent_version_id"],
            "branchName": row["branch_name"],
            "assignee": row["assignee"],
            "status": row["status"],
            "priority": row["priority"],
            "note": row["note"],
            "dueAt": row["due_at"],
            "createdBy": row["created_by"],
            "updatedBy": row["updated_by"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
            "completedAt": row["completed_at"],
        }

    def _normalize_experiment_variants(self, variants: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        normalized: list[Dict[str, Any]] = []
        seen: set[str] = set()
        for item in variants or []:
            if not isinstance(item, dict):
                continue
            key = normalize_experiment_key(item.get("key"))
            if not key:
                continue
            if key in seen:
                raise ValueError(f"duplicate experiment variant key: {key}")
            seen.add(key)
            weight = max(0, min(1000, int(item.get("weight", 1))))
            normalized.append(
                {
                    "key": key,
                    "label": str(item.get("label") or key).strip()[:120],
                    "weight": weight,
                    "payload": item.get("payload") if isinstance(item.get("payload"), dict) else {},
                }
            )
        if not normalized:
            raise ValueError("at least one experiment variant is required")
        if sum(variant["weight"] for variant in normalized) <= 0:
            raise ValueError("at least one experiment variant must have positive weight")
        return normalized

    def upsert_experiment(
        self,
        key: str,
        name: str,
        status: str,
        variants: list[Dict[str, Any]],
        allocation: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        normalized_key = normalize_experiment_key(key)
        if not normalized_key:
            raise ValueError("experiment key is required")
        normalized_name = (name or normalized_key).strip()[:160] or normalized_key
        normalized_status = status if status in {"draft", "running", "paused", "archived"} else "draft"
        normalized_variants = self._normalize_experiment_variants(variants)
        timestamp = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO experiments
                (id, key, name, status, variants_json, allocation_json, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(key)
                DO UPDATE SET
                  name = excluded.name,
                  status = excluded.status,
                  variants_json = excluded.variants_json,
                  allocation_json = excluded.allocation_json,
                  updated_at = excluded.updated_at
                """,
                (
                    new_id("exp"),
                    normalized_key,
                    normalized_name,
                    normalized_status,
                    _json(normalized_variants),
                    _json(allocation or {}),
                    created_by,
                    timestamp,
                    timestamp,
                ),
            )
        experiment = self.get_experiment(normalized_key)
        if not experiment:
            raise RuntimeError("experiment was not created")
        return experiment

    def list_experiments(self, status: Optional[str] = None, limit: int = 100) -> list[Dict[str, Any]]:
        normalized_status = status if status in {"draft", "running", "paused", "archived"} else None
        params: list[Any] = []
        where = ""
        if normalized_status:
            where = "WHERE status = ?"
            params.append(normalized_status)
        params.append(max(1, min(200, int(limit))))
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT *
                FROM experiments
                {where}
                ORDER BY
                  CASE status WHEN 'running' THEN 0 WHEN 'draft' THEN 1 WHEN 'paused' THEN 2 ELSE 3 END,
                  key ASC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._row_to_experiment(row) for row in rows]

    def get_experiment(self, key: str) -> Optional[Dict[str, Any]]:
        normalized_key = normalize_experiment_key(key)
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM experiments WHERE key = ?", (normalized_key,)).fetchone()
        return self._row_to_experiment(row) if row else None

    def update_experiment_status(self, key: str, status: str) -> Optional[Dict[str, Any]]:
        normalized_key = normalize_experiment_key(key)
        normalized_status = status if status in {"draft", "running", "paused", "archived"} else ""
        if not normalized_key or not normalized_status:
            return None
        timestamp = now_iso()
        with self.connect() as conn:
            result = conn.execute(
                """
                UPDATE experiments
                SET status = ?, updated_at = ?
                WHERE key = ?
                """,
                (normalized_status, timestamp, normalized_key),
            )
        return self.get_experiment(normalized_key) if result.rowcount else None

    def list_experiment_assignments(
        self,
        learner_id: str = "local-dev",
        project_id: str = "ai-language-partner-mobile-shared-20260629-v1",
        log_exposure: bool = True,
    ) -> list[Dict[str, Any]]:
        learner_id = normalize_learner_id(learner_id)
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM experiments
                WHERE status = 'running'
                ORDER BY key ASC
                """
            ).fetchall()
            assignments = [
                self._assign_experiment_with_conn(conn, learner_id, self._row_to_experiment(row), project_id, log_exposure=log_exposure)
                for row in rows
            ]
        return [assignment for assignment in assignments if assignment]

    def record_experiment_event(
        self,
        learner_id: str,
        experiment_key: str,
        event_name: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        learner_id = normalize_learner_id(learner_id)
        normalized_key = normalize_experiment_key(experiment_key)
        normalized_event_name = self._normalize_experiment_event_name(event_name)
        if not normalized_key or not normalized_event_name:
            return None
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT a.*, e.name, e.status, e.variants_json
                FROM experiment_assignments a
                JOIN experiments e ON e.key = a.experiment_key
                WHERE a.learner_id = ? AND a.experiment_key = ?
                """,
                (learner_id, normalized_key),
            ).fetchone()
            if not row:
                return None
            experiment = {
                "key": normalized_key,
                "name": row["name"],
                "status": row["status"],
                "variants": _loads(row["variants_json"], []),
            }
            assignment = self._row_to_experiment_assignment(row, experiment)
            event = self._insert_experiment_event(
                conn,
                learner_id,
                normalized_key,
                assignment["variantKey"],
                normalized_event_name,
                payload or {},
            )
        event["assignment"] = assignment
        return event

    def experiment_analytics(self, experiment_key: str, minimum_exposed_learners: int = 30) -> Optional[Dict[str, Any]]:
        normalized_key = normalize_experiment_key(experiment_key)
        if not normalized_key:
            return None
        threshold = max(1, min(100000, int(minimum_exposed_learners)))
        with self.connect() as conn:
            experiment_row = conn.execute("SELECT * FROM experiments WHERE key = ?", (normalized_key,)).fetchone()
            if not experiment_row:
                return None
            experiment = self._row_to_experiment(experiment_row)
            assignment_rows = conn.execute(
                """
                SELECT
                  variant_key,
                  COUNT(*) AS assignment_count,
                  MIN(assigned_at) AS first_assigned_at,
                  MAX(assigned_at) AS last_assigned_at
                FROM experiment_assignments
                WHERE experiment_key = ?
                GROUP BY variant_key
                """,
                (normalized_key,),
            ).fetchall()
            event_rows = conn.execute(
                """
                SELECT
                  variant_key,
                  event_name,
                  COUNT(*) AS event_count,
                  COUNT(DISTINCT learner_id) AS learner_count,
                  MIN(created_at) AS first_event_at,
                  MAX(created_at) AS last_event_at
                FROM experiment_events
                WHERE experiment_key = ?
                GROUP BY variant_key, event_name
                """,
                (normalized_key,),
            ).fetchall()

        variant_map: Dict[str, Dict[str, Any]] = {}
        for variant in experiment.get("variants") or []:
            key = str(variant.get("key") or "")
            if key:
                variant_map[key] = {
                    "variantKey": key,
                    "variant": dict(variant),
                    "assignmentCount": 0,
                    "exposureEventCount": 0,
                    "exposedLearnerCount": 0,
                    "conversionEventCount": 0,
                    "convertedLearnerCount": 0,
                    "customEventCount": 0,
                    "eventCounts": {},
                    "uniqueLearnerEventCounts": {},
                    "assignmentExposureRate": 0.0,
                    "exposedConversionRate": 0.0,
                    "assignmentConversionRate": 0.0,
                    "conversionRateConfidenceInterval95": {"lower": None, "upper": None},
                    "baselineVariantKey": None,
                    "absoluteLiftFromBaseline": None,
                    "relativeLiftFromBaseline": None,
                    "standardError": None,
                    "zScore": None,
                    "pValue": None,
                    "confidenceInterval95": {"lower": None, "upper": None},
                    "statisticallySignificant": False,
                    "sampleSizeWarning": "insufficient_exposed_learners",
                    "firstAssignedAt": None,
                    "lastAssignedAt": None,
                    "firstEventAt": None,
                    "lastEventAt": None,
                }

        def ensure_variant(key: str) -> Dict[str, Any]:
            if key not in variant_map:
                variant_map[key] = {
                    "variantKey": key,
                    "variant": self._variant_by_key(experiment.get("variants") or [], key),
                    "assignmentCount": 0,
                    "exposureEventCount": 0,
                    "exposedLearnerCount": 0,
                    "conversionEventCount": 0,
                    "convertedLearnerCount": 0,
                    "customEventCount": 0,
                    "eventCounts": {},
                    "uniqueLearnerEventCounts": {},
                    "assignmentExposureRate": 0.0,
                    "exposedConversionRate": 0.0,
                    "assignmentConversionRate": 0.0,
                    "conversionRateConfidenceInterval95": {"lower": None, "upper": None},
                    "baselineVariantKey": None,
                    "absoluteLiftFromBaseline": None,
                    "relativeLiftFromBaseline": None,
                    "standardError": None,
                    "zScore": None,
                    "pValue": None,
                    "confidenceInterval95": {"lower": None, "upper": None},
                    "statisticallySignificant": False,
                    "sampleSizeWarning": "insufficient_exposed_learners",
                    "firstAssignedAt": None,
                    "lastAssignedAt": None,
                    "firstEventAt": None,
                    "lastEventAt": None,
                }
            return variant_map[key]

        for row in assignment_rows:
            summary = ensure_variant(row["variant_key"])
            summary["assignmentCount"] = int(row["assignment_count"] or 0)
            summary["firstAssignedAt"] = row["first_assigned_at"]
            summary["lastAssignedAt"] = row["last_assigned_at"]

        for row in event_rows:
            summary = ensure_variant(row["variant_key"])
            event_name = row["event_name"]
            event_count = int(row["event_count"] or 0)
            learner_count = int(row["learner_count"] or 0)
            summary["eventCounts"][event_name] = event_count
            summary["uniqueLearnerEventCounts"][event_name] = learner_count
            if event_name == "exposure":
                summary["exposureEventCount"] = event_count
                summary["exposedLearnerCount"] = learner_count
            elif event_name == "conversion":
                summary["conversionEventCount"] = event_count
                summary["convertedLearnerCount"] = learner_count
            else:
                summary["customEventCount"] += event_count
            first_event_at = row["first_event_at"]
            last_event_at = row["last_event_at"]
            if first_event_at and (not summary["firstEventAt"] or first_event_at < summary["firstEventAt"]):
                summary["firstEventAt"] = first_event_at
            if last_event_at and (not summary["lastEventAt"] or last_event_at > summary["lastEventAt"]):
                summary["lastEventAt"] = last_event_at

        summaries = list(variant_map.values())
        for summary in summaries:
            assignments = int(summary["assignmentCount"])
            exposed = int(summary["exposedLearnerCount"])
            converted = int(summary["convertedLearnerCount"])
            summary["assignmentExposureRate"] = round(exposed / assignments, 4) if assignments else 0.0
            summary["exposedConversionRate"] = round(converted / exposed, 4) if exposed else 0.0
            summary["assignmentConversionRate"] = round(converted / assignments, 4) if assignments else 0.0
            summary["conversionRateConfidenceInterval95"] = wilson_interval(converted, exposed)
            summary["decisionEligible"] = exposed >= threshold
            summary["sampleSizeWarning"] = None if summary["decisionEligible"] else "insufficient_exposed_learners"

        variant_order = [variant.get("key") for variant in experiment.get("variants") or []]
        control_key = "control" if "control" in variant_order else (variant_order[0] if variant_order else None)
        control_summary = next((summary for summary in summaries if summary["variantKey"] == control_key), None)
        if control_summary:
            for summary in summaries:
                summary["baselineVariantKey"] = control_summary["variantKey"]
                if summary["variantKey"] == control_summary["variantKey"]:
                    summary["absoluteLiftFromBaseline"] = 0.0
                    summary["relativeLiftFromBaseline"] = 0.0
                    summary["standardError"] = None
                    summary["zScore"] = None
                    summary["pValue"] = None
                    summary["confidenceInterval95"] = {"lower": 0.0, "upper": 0.0}
                    summary["statisticallySignificant"] = False
                else:
                    summary.update(
                        two_proportion_stats(
                            int(control_summary["convertedLearnerCount"]),
                            int(control_summary["exposedLearnerCount"]),
                            int(summary["convertedLearnerCount"]),
                            int(summary["exposedLearnerCount"]),
                        )
                    )

        summaries.sort(key=lambda item: (-(item["exposedConversionRate"]), -(item["convertedLearnerCount"]), item["variantKey"]))
        best_observed = summaries[0]["variantKey"] if summaries and summaries[0]["exposedLearnerCount"] > 0 else None
        eligible = [summary for summary in summaries if summary["decisionEligible"]]
        decision_ready = len(eligible) >= 2
        significant_candidates = [
            summary
            for summary in eligible
            if summary["variantKey"] != control_key and summary.get("statisticallySignificant") and (summary.get("absoluteLiftFromBaseline") or 0) > 0
        ]
        winner = significant_candidates[0]["variantKey"] if decision_ready and significant_candidates else None
        totals = {
            "assignmentCount": sum(int(item["assignmentCount"]) for item in summaries),
            "exposureEventCount": sum(int(item["exposureEventCount"]) for item in summaries),
            "exposedLearnerCount": sum(int(item["exposedLearnerCount"]) for item in summaries),
            "conversionEventCount": sum(int(item["conversionEventCount"]) for item in summaries),
            "convertedLearnerCount": sum(int(item["convertedLearnerCount"]) for item in summaries),
            "customEventCount": sum(int(item["customEventCount"]) for item in summaries),
        }
        statistical_tests = [summary for summary in summaries if summary.get("baselineVariantKey") and summary["variantKey"] != summary.get("baselineVariantKey")]
        significant_positive = [
            summary["variantKey"]
            for summary in statistical_tests
            if summary.get("statisticallySignificant") and (summary.get("absoluteLiftFromBaseline") or 0) > 0
        ]
        decision_recommendation = "collect_more_data"
        if decision_ready and winner:
            decision_recommendation = "promote_winner"
        elif decision_ready:
            decision_recommendation = "no_statistically_significant_winner"
        return {
            "experiment": experiment,
            "minimumExposedLearners": threshold,
            "statisticalSignificanceAlpha": 0.05,
            "controlVariantKey": control_key,
            "totals": totals,
            "variants": summaries,
            "bestObservedVariantKey": best_observed,
            "decisionReady": decision_ready,
            "winnerVariantKey": winner,
            "decisionRecommendation": decision_recommendation,
            "significantPositiveVariantKeys": significant_positive,
            "analysisNotes": [
                "Rates use distinct learners, while event counts remain raw event volume.",
                "winnerVariantKey is only populated after at least two variants meet minimumExposedLearners and a positive variant is statistically significant versus the control variant.",
                "pValue uses a two-sided two-proportion z-test on distinct exposed learners and distinct converted learners; confidence intervals are approximate and should not replace product review.",
            ],
        }

    def create_experiment_decision(
        self,
        experiment_key: str,
        action: str,
        variant_key: Optional[str],
        analytics_snapshot: Dict[str, Any],
        guardrail: Dict[str, Any],
        minimum_exposed_learners: int,
        created_by: Optional[str],
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        normalized_key = normalize_experiment_key(experiment_key)
        normalized_action = action if action in {"collect_more_data", "promote_variant", "pause", "archive", "no_winner"} else "collect_more_data"
        normalized_variant = normalize_experiment_key(variant_key) if variant_key else None
        timestamp = now_iso()
        decision_id = new_id("expdec")
        with self.connect() as conn:
            if not conn.execute("SELECT 1 FROM experiments WHERE key = ?", (normalized_key,)).fetchone():
                raise ValueError("experiment not found")
            conn.execute(
                """
                INSERT INTO experiment_decisions
                (id, experiment_key, action, variant_key, status, reason, minimum_exposed_learners,
                 analytics_snapshot_json, guardrail_json, created_by, created_at)
                VALUES (?, ?, ?, ?, 'proposed', ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision_id,
                    normalized_key,
                    normalized_action,
                    normalized_variant,
                    (reason or "").strip()[:1000] or None,
                    int(minimum_exposed_learners),
                    _json(analytics_snapshot),
                    _json(guardrail),
                    created_by,
                    timestamp,
                ),
            )
        decision = self.get_experiment_decision(decision_id)
        if not decision:
            raise RuntimeError("experiment decision was not created")
        return decision

    def get_experiment_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM experiment_decisions WHERE id = ?", (decision_id,)).fetchone()
        return self._row_to_experiment_decision(row) if row else None

    def list_experiment_decisions(self, experiment_key: str, limit: int = 50) -> list[Dict[str, Any]]:
        normalized_key = normalize_experiment_key(experiment_key)
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM experiment_decisions
                WHERE experiment_key = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (normalized_key, max(1, min(200, int(limit)))),
            ).fetchall()
        return [self._row_to_experiment_decision(row) for row in rows]

    def apply_experiment_decision(self, decision_id: str, actor: Optional[str], note: Optional[str] = None) -> Optional[Dict[str, Any]]:
        timestamp = now_iso()
        with self.connect() as conn:
            decision_row = conn.execute("SELECT * FROM experiment_decisions WHERE id = ?", (decision_id,)).fetchone()
            if not decision_row:
                return None
            decision = self._row_to_experiment_decision(decision_row)
            if decision["status"] != "proposed":
                raise ValueError("experiment decision has already been applied")
            experiment_row = conn.execute("SELECT * FROM experiments WHERE key = ?", (decision["experimentKey"],)).fetchone()
            if not experiment_row:
                raise ValueError("experiment not found")
            experiment = self._row_to_experiment(experiment_row)
            variants = [dict(variant) for variant in experiment.get("variants") or []]
            allocation = dict(experiment.get("allocation") or {})
            status = experiment["status"]
            action = decision["action"]
            variant_key = decision.get("variantKey")
            if action == "promote_variant":
                if not variant_key or variant_key not in {variant["key"] for variant in variants}:
                    raise ValueError("decision variant is not part of the experiment")
                variants = [
                    {**variant, "weight": 1000 if variant["key"] == variant_key else 0}
                    for variant in variants
                ]
                status = "running"
                allocation["decision"] = {
                    "decisionId": decision_id,
                    "action": action,
                    "rolloutVariantKey": variant_key,
                    "rolloutPolicy": "winner_variant_weight_locked",
                    "appliedAt": timestamp,
                    "appliedBy": actor,
                }
            elif action in {"pause", "no_winner"}:
                status = "paused"
                allocation["decision"] = {
                    "decisionId": decision_id,
                    "action": action,
                    "appliedAt": timestamp,
                    "appliedBy": actor,
                }
            elif action == "archive":
                status = "archived"
                allocation["decision"] = {
                    "decisionId": decision_id,
                    "action": action,
                    "appliedAt": timestamp,
                    "appliedBy": actor,
                }
            else:
                allocation["decision"] = {
                    "decisionId": decision_id,
                    "action": "collect_more_data",
                    "appliedAt": timestamp,
                    "appliedBy": actor,
                }
            conn.execute(
                """
                UPDATE experiments
                SET status = ?, variants_json = ?, allocation_json = ?, updated_at = ?
                WHERE key = ?
                """,
                (status, _json(variants), _json(allocation), timestamp, decision["experimentKey"]),
            )
            conn.execute(
                """
                UPDATE experiment_decisions
                SET status = 'applied', applied_by = ?, applied_at = ?, apply_note = ?
                WHERE id = ?
                """,
                (actor, timestamp, (note or "").strip()[:1000] or None, decision_id),
            )
        applied = self.get_experiment_decision(decision_id)
        if not applied:
            return None
        applied["experimentAfterApply"] = self.get_experiment(applied["experimentKey"])
        return applied

    def _row_to_experiment_decision(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "experimentKey": row["experiment_key"],
            "action": row["action"],
            "variantKey": row["variant_key"],
            "status": row["status"],
            "reason": row["reason"],
            "minimumExposedLearners": int(row["minimum_exposed_learners"]),
            "analyticsSnapshot": _loads(row["analytics_snapshot_json"], {}),
            "guardrail": _loads(row["guardrail_json"], {}),
            "createdBy": row["created_by"],
            "createdAt": row["created_at"],
            "appliedBy": row["applied_by"],
            "appliedAt": row["applied_at"],
            "applyNote": row["apply_note"],
        }

    def _assign_experiment_with_conn(
        self,
        conn: sqlite3.Connection,
        learner_id: str,
        experiment: Dict[str, Any],
        project_id: str,
        log_exposure: bool = True,
    ) -> Optional[Dict[str, Any]]:
        if experiment["status"] != "running":
            return None
        variants = experiment.get("variants") or []
        valid_variant_keys = {variant["key"] for variant in variants}
        row = conn.execute(
            """
            SELECT *
            FROM experiment_assignments
            WHERE learner_id = ? AND experiment_key = ?
            """,
            (learner_id, experiment["key"]),
        ).fetchone()
        timestamp = now_iso()
        if row and row["variant_key"] in valid_variant_keys:
            assignment = self._row_to_experiment_assignment(row, experiment)
        else:
            variant_key = self._choose_experiment_variant(learner_id, experiment, project_id)
            if row:
                conn.execute(
                    """
                    UPDATE experiment_assignments
                    SET variant_key = ?, assigned_at = ?
                    WHERE learner_id = ? AND experiment_key = ?
                    """,
                    (variant_key, timestamp, learner_id, experiment["key"]),
                )
                assignment_id = row["id"]
            else:
                assignment_id = new_id("expasgn")
                conn.execute(
                    """
                    INSERT INTO experiment_assignments
                    (id, learner_id, experiment_key, variant_key, assigned_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (assignment_id, learner_id, experiment["key"], variant_key, timestamp),
                )
            assignment = {
                "id": assignment_id,
                "learnerId": learner_id,
                "experimentKey": experiment["key"],
                "experimentName": experiment["name"],
                "experimentStatus": experiment["status"],
                "variantKey": variant_key,
                "variant": self._variant_by_key(variants, variant_key),
                "assignedAt": timestamp,
            }
        if log_exposure:
            event = self._insert_experiment_event(
                conn,
                learner_id,
                experiment["key"],
                assignment["variantKey"],
                "exposure",
                {"source": "experiment_assignments_fetch"},
            )
            assignment["exposureEventId"] = event["id"]
        return assignment

    def _choose_experiment_variant(self, learner_id: str, experiment: Dict[str, Any], project_id: str) -> str:
        variants = experiment.get("variants") or []
        total_weight = sum(max(0, int(variant.get("weight") or 0)) for variant in variants)
        if total_weight <= 0:
            return variants[0]["key"]
        digest = hashlib.sha256(f"{project_id}:{learner_id}:{experiment['key']}".encode("utf-8")).hexdigest()
        bucket = int(digest[:12], 16) % total_weight
        running = 0
        for variant in variants:
            running += max(0, int(variant.get("weight") or 0))
            if bucket < running:
                return variant["key"]
        return variants[-1]["key"]

    def _variant_by_key(self, variants: list[Dict[str, Any]], variant_key: str) -> Dict[str, Any]:
        for variant in variants:
            if variant.get("key") == variant_key:
                return dict(variant)
        return {"key": variant_key, "label": variant_key, "weight": 0, "payload": {}}

    def _normalize_experiment_event_name(self, event_name: str) -> str:
        cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in (event_name or "").strip().lower())
        return cleaned[:80]

    def _insert_experiment_event(
        self,
        conn: sqlite3.Connection,
        learner_id: str,
        experiment_key: str,
        variant_key: str,
        event_name: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        event = {
            "id": new_id("expevt"),
            "learnerId": learner_id,
            "experimentKey": experiment_key,
            "variantKey": variant_key,
            "eventName": event_name,
            "payload": payload,
            "createdAt": now_iso(),
        }
        conn.execute(
            """
            INSERT INTO experiment_events
            (id, learner_id, experiment_key, variant_key, event_name, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["id"],
                learner_id,
                experiment_key,
                variant_key,
                event_name,
                _json(payload),
                event["createdAt"],
            ),
        )
        return event

    def _row_to_experiment(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "key": row["key"],
            "name": row["name"],
            "status": row["status"],
            "variants": _loads(row["variants_json"], []),
            "allocation": _loads(row["allocation_json"], {}),
            "createdBy": row["created_by"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }

    def _row_to_experiment_assignment(self, row: sqlite3.Row, experiment: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "learnerId": row["learner_id"],
            "experimentKey": row["experiment_key"],
            "experimentName": experiment.get("name"),
            "experimentStatus": experiment.get("status"),
            "variantKey": row["variant_key"],
            "variant": self._variant_by_key(experiment.get("variants") or [], row["variant_key"]),
            "assignedAt": row["assigned_at"],
        }

    def create_account(self, email: str, learner_id: str, password_hash: str) -> Dict[str, Any]:
        normalized_learner = normalize_learner_id(learner_id)
        now = now_iso()
        account = {
            "id": new_id("acct"),
            "email": email.strip().lower(),
            "learnerId": normalized_learner,
            "createdAt": now,
            "updatedAt": now,
            "disabledAt": None,
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO accounts (id, email, learner_id, password_hash, disabled_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, NULL, ?, ?)
                """,
                (account["id"], account["email"], account["learnerId"], password_hash, now, now),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO learning_profiles
                (id, native_language, target_language, level, jlpt_level, goals_json, weak_tags_json, preferred_persona_id, created_at, updated_at)
                VALUES (?, 'ko', 'ja', 'beginner', 'N5', ?, ?, 'yui', ?, ?)
                """,
                (
                    account["learnerId"],
                    _json(["daily_speaking", "japanese_friend_conversation"]),
                    _json(["감정표현", "동사시제"]),
                    now,
                    now,
                ),
            )
        return account

    def upsert_external_identity_account(
        self,
        provider: str,
        subject: str,
        email: str,
        email_verified: bool,
        profile: Dict[str, Any],
        learner_id: Optional[str],
        password_hash: str,
    ) -> Dict[str, Any]:
        normalized_provider = provider.strip().lower()
        normalized_subject = subject.strip()
        normalized_email = email.strip().lower()
        normalized_learner = normalize_learner_id(learner_id or f"{normalized_provider}_{hashlib.sha256(normalized_subject.encode('utf-8')).hexdigest()[:16]}")
        now = now_iso()
        with self.connect() as conn:
            identity_row = conn.execute(
                """
                SELECT i.*, a.email AS account_email, a.learner_id, a.disabled_at, a.created_at AS account_created_at, a.updated_at AS account_updated_at
                FROM account_identities i
                JOIN accounts a ON a.id = i.account_id
                WHERE i.provider = ? AND i.subject = ?
                """,
                (normalized_provider, normalized_subject),
            ).fetchone()
            if identity_row:
                conn.execute(
                    """
                    UPDATE account_identities
                    SET email = ?, email_verified = ?, profile_json = ?, updated_at = ?
                    WHERE provider = ? AND subject = ?
                    """,
                    (
                        normalized_email,
                        int(email_verified),
                        _json(profile),
                        now,
                        normalized_provider,
                        normalized_subject,
                    ),
                )
                account_id = identity_row["account_id"]
            else:
                account_row = conn.execute("SELECT * FROM accounts WHERE email = ?", (normalized_email,)).fetchone()
                if account_row and account_row["disabled_at"]:
                    raise sqlite3.IntegrityError("disabled account cannot be linked")
                if account_row:
                    account_id = account_row["id"]
                else:
                    account_id = new_id("acct")
                    conn.execute(
                        """
                        INSERT INTO accounts (id, email, learner_id, password_hash, disabled_at, created_at, updated_at)
                        VALUES (?, ?, ?, ?, NULL, ?, ?)
                        """,
                        (account_id, normalized_email, normalized_learner, password_hash, now, now),
                    )
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO learning_profiles
                        (id, native_language, target_language, level, jlpt_level, goals_json, weak_tags_json, preferred_persona_id, created_at, updated_at)
                        VALUES (?, 'ko', 'ja', 'beginner', 'N5', ?, ?, 'yui', ?, ?)
                        """,
                        (
                            normalized_learner,
                            _json(["daily_speaking", "japanese_friend_conversation"]),
                            _json(["감정표현", "동사시제"]),
                            now,
                            now,
                        ),
                    )
                conn.execute(
                    """
                    INSERT INTO account_identities
                    (id, account_id, provider, subject, email, email_verified, profile_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_id("acctid"),
                        account_id,
                        normalized_provider,
                        normalized_subject,
                        normalized_email,
                        int(email_verified),
                        _json(profile),
                        now,
                        now,
                    ),
                )
            row = conn.execute(
                """
                SELECT a.*,
                  (SELECT provider FROM account_identities i WHERE i.account_id = a.id ORDER BY i.updated_at DESC LIMIT 1) AS identity_provider
                FROM accounts a
                WHERE a.id = ?
                """,
                (account_id,),
            ).fetchone()
        if not row:
            raise RuntimeError("external identity account was not created")
        return self._row_to_account(row, include_password_hash=False)

    def _row_to_enterprise_sso_connection(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "provider": row["provider"],
            "organizationName": row["organization_name"],
            "domains": _loads(row["domains_json"], []),
            "redirectUris": _loads(row["redirect_uris_json"], []),
            "requiredEmailDomain": row["required_email_domain"],
            "status": row["status"],
            "enabled": row["status"] == "enabled",
            "createdBy": row["created_by"],
            "updatedBy": row["updated_by"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }

    def upsert_enterprise_sso_connection(
        self,
        connection_id: str,
        provider: str,
        organization_name: str,
        domains: list[str],
        redirect_uris: list[str],
        required_email_domain: Optional[str] = None,
        status: str = "enabled",
        actor: str = "admin",
    ) -> Dict[str, Any]:
        normalized_id = normalize_experiment_key(connection_id) or "default"
        normalized_provider = provider.strip().lower()
        normalized_domains = sorted(
            {
                domain.strip().lower().lstrip("@")
                for domain in domains
                if isinstance(domain, str) and domain.strip()
            }
        )
        normalized_redirects = []
        for uri in redirect_uris:
            if isinstance(uri, str) and uri.strip() and uri.strip() not in normalized_redirects:
                normalized_redirects.append(uri.strip())
        normalized_required_domain = required_email_domain.strip().lower().lstrip("@") if required_email_domain else None
        normalized_status = status if status in {"enabled", "disabled"} else "enabled"
        now = now_iso()
        with self.connect() as conn:
            existing = conn.execute("SELECT id FROM enterprise_sso_connections WHERE id = ?", (normalized_id,)).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE enterprise_sso_connections
                    SET provider = ?,
                        organization_name = ?,
                        domains_json = ?,
                        redirect_uris_json = ?,
                        required_email_domain = ?,
                        status = ?,
                        updated_by = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        normalized_provider,
                        organization_name.strip()[:160] or normalized_id,
                        _json(normalized_domains),
                        _json(normalized_redirects),
                        normalized_required_domain,
                        normalized_status,
                        actor,
                        now,
                        normalized_id,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO enterprise_sso_connections
                    (id, provider, organization_name, domains_json, redirect_uris_json, required_email_domain,
                     status, created_by, updated_by, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        normalized_id,
                        normalized_provider,
                        organization_name.strip()[:160] or normalized_id,
                        _json(normalized_domains),
                        _json(normalized_redirects),
                        normalized_required_domain,
                        normalized_status,
                        actor,
                        actor,
                        now,
                        now,
                    ),
                )
            row = conn.execute("SELECT * FROM enterprise_sso_connections WHERE id = ?", (normalized_id,)).fetchone()
        return self._row_to_enterprise_sso_connection(row)

    def list_enterprise_sso_connections(self, include_disabled: bool = True) -> list[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM enterprise_sso_connections
                WHERE (? = 1 OR status = 'enabled')
                ORDER BY organization_name ASC, id ASC
                """,
                (int(include_disabled),),
            ).fetchall()
        return [self._row_to_enterprise_sso_connection(row) for row in rows]

    def get_enterprise_sso_connection(self, connection_id: str, enabled_only: bool = False) -> Optional[Dict[str, Any]]:
        normalized_id = normalize_experiment_key(connection_id)
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM enterprise_sso_connections
                WHERE id = ?
                  AND (? = 0 OR status = 'enabled')
                """,
                (normalized_id, int(enabled_only)),
            ).fetchone()
        return self._row_to_enterprise_sso_connection(row) if row else None

    def find_enterprise_sso_connection_for_email(self, email: str) -> Optional[Dict[str, Any]]:
        normalized_email = email.strip().lower()
        _, _, domain = normalized_email.rpartition("@")
        if not domain:
            return None
        for connection in self.list_enterprise_sso_connections(include_disabled=False):
            if domain in set(connection.get("domains") or []):
                return connection
        return None

    def create_oauth_pkce_request(
        self,
        provider: str,
        state_hash: str,
        redirect_uri: str,
        code_challenge: str,
        code_challenge_method: str,
        expires_at: str,
        scope: Optional[str] = None,
        nonce: Optional[str] = None,
        learner_id: Optional[str] = None,
        device_label: Optional[str] = None,
        client_hash: Optional[str] = None,
        enterprise_sso_connection_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        created_at = now_iso()
        request = {
            "id": new_id("oauthpkce"),
            "provider": provider.strip().lower(),
            "enterpriseSsoConnectionId": enterprise_sso_connection_id,
            "stateHash": state_hash,
            "redirectUri": redirect_uri,
            "codeChallenge": code_challenge,
            "codeChallengeMethod": code_challenge_method,
            "scope": scope,
            "nonce": nonce,
            "learnerId": normalize_learner_id(learner_id) if learner_id else None,
            "deviceLabel": device_label,
            "clientHash": client_hash,
            "createdAt": created_at,
            "expiresAt": expires_at,
            "consumedAt": None,
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO oauth_pkce_requests
                (id, provider, enterprise_sso_connection_id, state_hash, redirect_uri, code_challenge, code_challenge_method, scope, nonce,
                 learner_id, device_label, client_hash, created_at, expires_at, consumed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    request["id"],
                    request["provider"],
                    request["enterpriseSsoConnectionId"],
                    request["stateHash"],
                    request["redirectUri"],
                    request["codeChallenge"],
                    request["codeChallengeMethod"],
                    request["scope"],
                    request["nonce"],
                    request["learnerId"],
                    request["deviceLabel"],
                    request["clientHash"],
                    request["createdAt"],
                    request["expiresAt"],
                ),
            )
        return request

    def consume_oauth_pkce_request(
        self,
        provider: str,
        state_hash: str,
        now: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        current = now or now_iso()
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM oauth_pkce_requests
                WHERE provider = ?
                  AND state_hash = ?
                  AND consumed_at IS NULL
                  AND expires_at > ?
                """,
                (provider.strip().lower(), state_hash, current),
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE oauth_pkce_requests SET consumed_at = ? WHERE id = ? AND consumed_at IS NULL",
                    (current, row["id"]),
                )
        return self._row_to_oauth_pkce_request(row) if row else None

    def _row_to_oauth_pkce_request(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "provider": row["provider"],
            "enterpriseSsoConnectionId": row["enterprise_sso_connection_id"] if "enterprise_sso_connection_id" in row.keys() else None,
            "stateHash": row["state_hash"],
            "redirectUri": row["redirect_uri"],
            "codeChallenge": row["code_challenge"],
            "codeChallengeMethod": row["code_challenge_method"],
            "scope": row["scope"],
            "nonce": row["nonce"],
            "learnerId": row["learner_id"],
            "deviceLabel": row["device_label"],
            "clientHash": row["client_hash"],
            "createdAt": row["created_at"],
            "expiresAt": row["expires_at"],
            "consumedAt": row["consumed_at"],
        }

    def get_account_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT a.*,
                  (SELECT provider FROM account_identities i WHERE i.account_id = a.id ORDER BY i.updated_at DESC LIMIT 1) AS identity_provider
                FROM accounts a
                WHERE a.email = ?
                """,
                (email.strip().lower(),),
            ).fetchone()
        return self._row_to_account(row, include_password_hash=True) if row else None

    def get_account_by_id(self, account_id: str, include_password_hash: bool = False) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT a.*,
                  (SELECT provider FROM account_identities i WHERE i.account_id = a.id ORDER BY i.updated_at DESC LIMIT 1) AS identity_provider
                FROM accounts a
                WHERE a.id = ?
                """,
                (account_id,),
            ).fetchone()
        return self._row_to_account(row, include_password_hash=include_password_hash) if row else None

    def _row_to_account(self, row: sqlite3.Row, include_password_hash: bool = False) -> Dict[str, Any]:
        identity_provider = row["identity_provider"] if "identity_provider" in row.keys() else None
        account = {
            "id": row["id"],
            "email": row["email"],
            "learnerId": row["learner_id"],
            "disabledAt": row["disabled_at"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
            "authProvider": "oidc" if identity_provider else "password",
            "identityProvider": identity_provider,
        }
        if include_password_hash:
            account["passwordHash"] = row["password_hash"]
        return account

    def _row_to_account_device(self, row: sqlite3.Row, current_device_id_hash: Optional[str] = None) -> Dict[str, Any]:
        trust_status = row["trust_status"] or "untrusted"
        return {
            "id": row["id"],
            "accountId": row["account_id"],
            "deviceIdHash": row["device_id_hash"],
            "deviceLabel": row["label"],
            "platform": row["platform"],
            "trustStatus": trust_status,
            "trusted": trust_status == "trusted",
            "attestationProvider": row["attestation_provider"],
            "attestationVerified": bool(row["attestation_verified"]),
            "attestationSubjectHash": row["attestation_subject_hash"],
            "evidence": _loads(row["evidence_json"], {}),
            "trustedAt": row["trusted_at"],
            "revokedAt": row["revoked_at"],
            "lastSeenAt": row["last_seen_at"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
            "isCurrent": bool(current_device_id_hash and row["device_id_hash"] == current_device_id_hash),
        }

    def get_account_device_by_hash(self, account_id: str, device_id_hash: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM account_devices
                WHERE account_id = ? AND device_id_hash = ?
                """,
                (account_id, device_id_hash),
            ).fetchone()
        return self._row_to_account_device(row) if row else None

    def create_account_device_attestation_challenge(
        self,
        account_id: str,
        device_id_hash: str,
        provider: str,
        challenge_hash: str,
        expires_at: str,
    ) -> Dict[str, Any]:
        now = now_iso()
        normalized_provider = provider.strip().lower()[:80] or "signed_challenge"
        challenge = {
            "id": new_id("attchal"),
            "accountId": account_id,
            "deviceIdHash": device_id_hash,
            "provider": normalized_provider,
            "challengeHash": challenge_hash,
            "createdAt": now,
            "expiresAt": expires_at,
            "consumedAt": None,
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO account_device_attestation_challenges
                (id, account_id, device_id_hash, provider, challenge_hash, created_at, expires_at, consumed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    challenge["id"],
                    challenge["accountId"],
                    challenge["deviceIdHash"],
                    challenge["provider"],
                    challenge["challengeHash"],
                    challenge["createdAt"],
                    challenge["expiresAt"],
                ),
            )
        return challenge

    def consume_account_device_attestation_challenge(
        self,
        account_id: str,
        device_id_hash: str,
        provider: str,
        challenge_id: str,
        challenge_hash: str,
        now: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        current = now or now_iso()
        normalized_provider = provider.strip().lower()[:80] or "signed_challenge"
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM account_device_attestation_challenges
                WHERE id = ?
                  AND account_id = ?
                  AND device_id_hash = ?
                  AND provider = ?
                  AND challenge_hash = ?
                  AND consumed_at IS NULL
                  AND expires_at > ?
                """,
                (challenge_id, account_id, device_id_hash, normalized_provider, challenge_hash, current),
            ).fetchone()
            if row:
                conn.execute(
                    """
                    UPDATE account_device_attestation_challenges
                    SET consumed_at = ?
                    WHERE id = ? AND consumed_at IS NULL
                    """,
                    (current, row["id"]),
                )
        return self._row_to_device_attestation_challenge(row) if row else None

    def _row_to_device_attestation_challenge(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "accountId": row["account_id"],
            "deviceIdHash": row["device_id_hash"],
            "provider": row["provider"],
            "challengeHash": row["challenge_hash"],
            "createdAt": row["created_at"],
            "expiresAt": row["expires_at"],
            "consumedAt": row["consumed_at"],
        }

    def upsert_account_device(
        self,
        account_id: str,
        device_id_hash: str,
        label: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = now_iso()
        normalized_platform = platform.strip().lower()[:80] if platform else None
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM account_devices
                WHERE account_id = ? AND device_id_hash = ?
                """,
                (account_id, device_id_hash),
            ).fetchone()
            if row:
                conn.execute(
                    """
                    UPDATE account_devices
                    SET label = COALESCE(?, label),
                        platform = COALESCE(?, platform),
                        last_seen_at = ?,
                        updated_at = ?
                    WHERE account_id = ? AND device_id_hash = ?
                    """,
                    (label, normalized_platform, now, now, account_id, device_id_hash),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO account_devices
                    (id, account_id, device_id_hash, label, platform, trust_status, attestation_provider,
                     attestation_verified, attestation_subject_hash, evidence_json, trusted_at, revoked_at,
                     last_seen_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, 'untrusted', NULL, 0, NULL, '{}', NULL, NULL, ?, ?, ?)
                    """,
                    (new_id("dev"), account_id, device_id_hash, label, normalized_platform, now, now, now),
                )
            updated = conn.execute(
                """
                SELECT *
                FROM account_devices
                WHERE account_id = ? AND device_id_hash = ?
                """,
                (account_id, device_id_hash),
            ).fetchone()
        return self._row_to_account_device(updated)

    def mark_account_device_trusted(
        self,
        account_id: str,
        device_id_hash: str,
        label: Optional[str] = None,
        platform: Optional[str] = None,
        attestation_provider: Optional[str] = None,
        attestation_subject_hash: Optional[str] = None,
        attestation_verified: bool = False,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        now = now_iso()
        normalized_platform = platform.strip().lower()[:80] if platform else None
        normalized_provider = attestation_provider.strip().lower()[:80] if attestation_provider else "account_session"
        payload = evidence or {}
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM account_devices
                WHERE account_id = ? AND device_id_hash = ?
                """,
                (account_id, device_id_hash),
            ).fetchone()
            if row and row["trust_status"] == "revoked":
                return None
            if row:
                conn.execute(
                    """
                    UPDATE account_devices
                    SET label = COALESCE(?, label),
                        platform = COALESCE(?, platform),
                        trust_status = 'trusted',
                        attestation_provider = ?,
                        attestation_verified = ?,
                        attestation_subject_hash = ?,
                        evidence_json = ?,
                        trusted_at = COALESCE(trusted_at, ?),
                        last_seen_at = ?,
                        updated_at = ?
                    WHERE account_id = ? AND device_id_hash = ? AND trust_status != 'revoked'
                    """,
                    (
                        label,
                        normalized_platform,
                        normalized_provider,
                        int(attestation_verified),
                        attestation_subject_hash,
                        _json(payload),
                        now,
                        now,
                        now,
                        account_id,
                        device_id_hash,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO account_devices
                    (id, account_id, device_id_hash, label, platform, trust_status, attestation_provider,
                     attestation_verified, attestation_subject_hash, evidence_json, trusted_at, revoked_at,
                     last_seen_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, 'trusted', ?, ?, ?, ?, ?, NULL, ?, ?, ?)
                    """,
                    (
                        new_id("dev"),
                        account_id,
                        device_id_hash,
                        label,
                        normalized_platform,
                        normalized_provider,
                        int(attestation_verified),
                        attestation_subject_hash,
                        _json(payload),
                        now,
                        now,
                        now,
                        now,
                    ),
                )
            updated = conn.execute(
                """
                SELECT *
                FROM account_devices
                WHERE account_id = ? AND device_id_hash = ?
                """,
                (account_id, device_id_hash),
            ).fetchone()
        return self._row_to_account_device(updated) if updated else None

    def list_account_devices(
        self,
        account_id: str,
        include_revoked: bool = False,
        current_device_id_hash: Optional[str] = None,
    ) -> list[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM account_devices
                WHERE account_id = ?
                  AND (? = 1 OR trust_status != 'revoked')
                ORDER BY last_seen_at DESC, updated_at DESC, created_at DESC
                """,
                (account_id, int(include_revoked)),
            ).fetchall()
        return [self._row_to_account_device(row, current_device_id_hash=current_device_id_hash) for row in rows]

    def revoke_account_device(self, account_id: str, device_id: str) -> Optional[Dict[str, Any]]:
        revoked_at = now_iso()
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM account_devices
                WHERE account_id = ? AND id = ?
                """,
                (account_id, device_id),
            ).fetchone()
            if not row:
                return None
            conn.execute(
                """
                UPDATE account_devices
                SET trust_status = 'revoked',
                    revoked_at = COALESCE(revoked_at, ?),
                    updated_at = ?
                WHERE account_id = ? AND id = ?
                """,
                (revoked_at, revoked_at, account_id, device_id),
            )
            session_result = conn.execute(
                """
                UPDATE account_sessions
                SET revoked_at = ?
                WHERE account_id = ?
                  AND device_id_hash = ?
                  AND revoked_at IS NULL
                """,
                (revoked_at, account_id, row["device_id_hash"]),
            )
            updated = conn.execute(
                """
                SELECT *
                FROM account_devices
                WHERE account_id = ? AND id = ?
                """,
                (account_id, device_id),
            ).fetchone()
        device = self._row_to_account_device(updated)
        device["revokedSessionCount"] = int(session_result.rowcount)
        return device

    def create_account_session(
        self,
        account_id: str,
        access_token_hash: str,
        refresh_token_hash: str,
        access_expires_at: str,
        refresh_expires_at: str,
        device_label: Optional[str] = None,
        device_id_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = now_iso()
        session = {
            "id": new_id("sess"),
            "accountId": account_id,
            "deviceLabel": device_label,
            "deviceBound": bool(device_id_hash),
            "deviceIdHash": device_id_hash,
            "accessExpiresAt": access_expires_at,
            "refreshExpiresAt": refresh_expires_at,
            "revokedAt": None,
            "createdAt": now,
            "lastUsedAt": now,
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO account_sessions
                (id, account_id, access_token_hash, refresh_token_hash, device_label, device_id_hash,
                 access_expires_at, refresh_expires_at, revoked_at, created_at, last_used_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
                """,
                (
                    session["id"],
                    account_id,
                    access_token_hash,
                    refresh_token_hash,
                    device_label,
                    device_id_hash,
                    access_expires_at,
                    refresh_expires_at,
                    now,
                    now,
                ),
            )
        return session

    def get_session_by_access_hash(
        self,
        token_hash: str,
        now: Optional[str] = None,
        device_id_hash: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        current = now or now_iso()
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT s.*, a.email, a.learner_id, a.disabled_at,
                  (SELECT provider FROM account_identities i WHERE i.account_id = a.id ORDER BY i.updated_at DESC LIMIT 1) AS identity_provider,
                  d.id AS device_record_id,
                  d.trust_status AS device_trust_status,
                  d.attestation_provider AS device_attestation_provider,
                  d.attestation_verified AS device_attestation_verified,
                  d.evidence_json AS device_evidence_json,
                  d.trusted_at AS device_trusted_at,
                  d.revoked_at AS device_revoked_at
                FROM account_sessions s
                JOIN accounts a ON a.id = s.account_id
                LEFT JOIN account_devices d ON d.account_id = s.account_id AND d.device_id_hash = s.device_id_hash
                WHERE s.access_token_hash = ?
                  AND s.revoked_at IS NULL
                  AND a.disabled_at IS NULL
                  AND s.access_expires_at > ?
                  AND (s.device_id_hash IS NULL OR s.device_id_hash = ?)
                  AND (s.device_id_hash IS NULL OR d.trust_status IS NULL OR d.trust_status != 'revoked')
                """,
                (token_hash, current, device_id_hash),
            ).fetchone()
            if row:
                conn.execute("UPDATE account_sessions SET last_used_at = ? WHERE id = ?", (current, row["id"]))
                if row["device_id_hash"]:
                    conn.execute(
                        """
                        UPDATE account_devices
                        SET last_seen_at = ?, updated_at = ?
                        WHERE account_id = ? AND device_id_hash = ? AND trust_status != 'revoked'
                        """,
                        (current, current, row["account_id"], row["device_id_hash"]),
                    )
        return self._row_to_session(row) if row else None

    def get_session_by_refresh_hash(
        self,
        token_hash: str,
        now: Optional[str] = None,
        device_id_hash: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        current = now or now_iso()
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT s.*, a.email, a.learner_id, a.disabled_at,
                  (SELECT provider FROM account_identities i WHERE i.account_id = a.id ORDER BY i.updated_at DESC LIMIT 1) AS identity_provider,
                  d.id AS device_record_id,
                  d.trust_status AS device_trust_status,
                  d.attestation_provider AS device_attestation_provider,
                  d.attestation_verified AS device_attestation_verified,
                  d.evidence_json AS device_evidence_json,
                  d.trusted_at AS device_trusted_at,
                  d.revoked_at AS device_revoked_at
                FROM account_sessions s
                JOIN accounts a ON a.id = s.account_id
                LEFT JOIN account_devices d ON d.account_id = s.account_id AND d.device_id_hash = s.device_id_hash
                WHERE s.refresh_token_hash = ?
                  AND s.revoked_at IS NULL
                  AND a.disabled_at IS NULL
                  AND s.refresh_expires_at > ?
                  AND (s.device_id_hash IS NULL OR s.device_id_hash = ?)
                  AND (s.device_id_hash IS NULL OR d.trust_status IS NULL OR d.trust_status != 'revoked')
                """,
                (token_hash, current, device_id_hash),
            ).fetchone()
            if row:
                conn.execute("UPDATE account_sessions SET last_used_at = ? WHERE id = ?", (current, row["id"]))
                if row["device_id_hash"]:
                    conn.execute(
                        """
                        UPDATE account_devices
                        SET last_seen_at = ?, updated_at = ?
                        WHERE account_id = ? AND device_id_hash = ? AND trust_status != 'revoked'
                        """,
                        (current, current, row["account_id"], row["device_id_hash"]),
                    )
        return self._row_to_session(row) if row else None

    def get_any_session_by_refresh_hash(self, token_hash: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT s.*, a.email, a.learner_id, a.disabled_at,
                  (SELECT provider FROM account_identities i WHERE i.account_id = a.id ORDER BY i.updated_at DESC LIMIT 1) AS identity_provider,
                  d.id AS device_record_id,
                  d.trust_status AS device_trust_status,
                  d.attestation_provider AS device_attestation_provider,
                  d.attestation_verified AS device_attestation_verified,
                  d.evidence_json AS device_evidence_json,
                  d.trusted_at AS device_trusted_at,
                  d.revoked_at AS device_revoked_at
                FROM account_sessions s
                JOIN accounts a ON a.id = s.account_id
                LEFT JOIN account_devices d ON d.account_id = s.account_id AND d.device_id_hash = s.device_id_hash
                WHERE s.refresh_token_hash = ?
                """,
                (token_hash,),
            ).fetchone()
        return self._row_to_session(row) if row else None

    def list_account_sessions(self, account_id: str, include_revoked: bool = False) -> list[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT s.*, a.email, a.learner_id, a.disabled_at,
                  (SELECT provider FROM account_identities i WHERE i.account_id = a.id ORDER BY i.updated_at DESC LIMIT 1) AS identity_provider,
                  d.id AS device_record_id,
                  d.trust_status AS device_trust_status,
                  d.attestation_provider AS device_attestation_provider,
                  d.attestation_verified AS device_attestation_verified,
                  d.evidence_json AS device_evidence_json,
                  d.trusted_at AS device_trusted_at,
                  d.revoked_at AS device_revoked_at
                FROM account_sessions s
                JOIN accounts a ON a.id = s.account_id
                LEFT JOIN account_devices d ON d.account_id = s.account_id AND d.device_id_hash = s.device_id_hash
                WHERE s.account_id = ?
                  AND (? = 1 OR s.revoked_at IS NULL)
                ORDER BY s.last_used_at DESC, s.created_at DESC
                """,
                (account_id, int(include_revoked)),
            ).fetchall()
        return [self._row_to_session(row) for row in rows]

    def revoke_session(self, session_id: str) -> bool:
        revoked_at = now_iso()
        with self.connect() as conn:
            result = conn.execute(
                "UPDATE account_sessions SET revoked_at = ? WHERE id = ? AND revoked_at IS NULL",
                (revoked_at, session_id),
            )
        return result.rowcount > 0

    def revoke_account_session(self, account_id: str, session_id: str) -> bool:
        revoked_at = now_iso()
        with self.connect() as conn:
            result = conn.execute(
                """
                UPDATE account_sessions
                SET revoked_at = ?
                WHERE account_id = ? AND id = ? AND revoked_at IS NULL
                """,
                (revoked_at, account_id, session_id),
            )
        return result.rowcount > 0

    def revoke_account_sessions(self, account_id: str, except_session_id: Optional[str] = None) -> int:
        revoked_at = now_iso()
        with self.connect() as conn:
            if except_session_id:
                result = conn.execute(
                    """
                    UPDATE account_sessions
                    SET revoked_at = ?
                    WHERE account_id = ? AND id != ? AND revoked_at IS NULL
                    """,
                    (revoked_at, account_id, except_session_id),
                )
            else:
                result = conn.execute(
                    """
                    UPDATE account_sessions
                    SET revoked_at = ?
                    WHERE account_id = ? AND revoked_at IS NULL
                    """,
                    (revoked_at, account_id),
                )
        return int(result.rowcount)

    def update_account_password(self, account_id: str, password_hash: str) -> bool:
        updated_at = now_iso()
        with self.connect() as conn:
            result = conn.execute(
                "UPDATE accounts SET password_hash = ?, updated_at = ? WHERE id = ? AND disabled_at IS NULL",
                (password_hash, updated_at, account_id),
            )
        return result.rowcount > 0

    def disable_account(self, account_id: str) -> bool:
        disabled_at = now_iso()
        with self.connect() as conn:
            result = conn.execute(
                "UPDATE accounts SET disabled_at = ?, updated_at = ? WHERE id = ? AND disabled_at IS NULL",
                (disabled_at, disabled_at, account_id),
            )
            conn.execute(
                """
                UPDATE account_sessions
                SET revoked_at = ?
                WHERE account_id = ? AND revoked_at IS NULL
                """,
                (disabled_at, account_id),
            )
        return result.rowcount > 0

    def record_auth_attempt(self, email_hash: str, client_hash: str, succeeded: bool, purpose: str = "login") -> Dict[str, Any]:
        normalized_purpose = purpose if purpose in {"login", "register"} else "login"
        attempt = {
            "id": new_id("authtry"),
            "purpose": normalized_purpose,
            "emailHash": email_hash,
            "clientHash": client_hash,
            "succeeded": bool(succeeded),
            "createdAt": now_iso(),
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO auth_attempts (id, purpose, email_hash, client_hash, succeeded, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (attempt["id"], normalized_purpose, email_hash, client_hash, int(attempt["succeeded"]), attempt["createdAt"]),
            )
        return attempt

    def count_failed_auth_attempts(self, email_hash: str, client_hash: str, since_iso: str) -> int:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM auth_attempts
                WHERE succeeded = 0
                  AND purpose = 'login'
                  AND created_at >= ?
                  AND (email_hash = ? OR client_hash = ?)
                """,
                (since_iso, email_hash, client_hash),
            ).fetchone()
        return int(row["count"] if row else 0)

    def count_distinct_failed_login_emails_by_client(self, client_hash: str, since_iso: str) -> int:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(DISTINCT email_hash) AS count
                FROM auth_attempts
                WHERE succeeded = 0
                  AND purpose = 'login'
                  AND created_at >= ?
                  AND client_hash = ?
                """,
                (since_iso, client_hash),
            ).fetchone()
        return int(row["count"] if row else 0)

    def count_auth_attempts(self, email_hash: str, client_hash: str, since_iso: str, purpose: Optional[str] = None) -> int:
        with self.connect() as conn:
            purpose_clause = "AND purpose = ?" if purpose else ""
            params: tuple[Any, ...]
            if purpose:
                params = (since_iso, purpose, email_hash, client_hash)
            else:
                params = (since_iso, email_hash, client_hash)
            row = conn.execute(
                f"""
                SELECT COUNT(*) AS count
                FROM auth_attempts
                WHERE created_at >= ?
                  {purpose_clause}
                  AND (email_hash = ? OR client_hash = ?)
                """,
                params,
            ).fetchone()
        return int(row["count"] if row else 0)

    def clear_failed_auth_attempts(self, email_hash: str, client_hash: str) -> int:
        with self.connect() as conn:
            result = conn.execute(
                """
                DELETE FROM auth_attempts
                WHERE succeeded = 0
                  AND purpose = 'login'
                  AND (email_hash = ? OR client_hash = ?)
                """,
                (email_hash, client_hash),
            )
        return int(result.rowcount)

    def _row_to_session(self, row: sqlite3.Row) -> Dict[str, Any]:
        identity_provider = row["identity_provider"] if "identity_provider" in row.keys() else None
        row_keys = set(row.keys())
        device_bound = bool(row["device_id_hash"])
        device_status = row["device_trust_status"] if "device_trust_status" in row_keys else None
        if not device_bound:
            device_status = "not_bound"
        elif not device_status:
            device_status = "untracked"
        device_evidence = _loads(row["device_evidence_json"], {}) if "device_evidence_json" in row_keys and row["device_evidence_json"] else {}
        return {
            "id": row["id"],
            "accountId": row["account_id"],
            "email": row["email"],
            "learnerId": row["learner_id"],
            "authProvider": "oidc" if identity_provider else "password",
            "identityProvider": identity_provider,
            "deviceLabel": row["device_label"],
            "deviceBound": device_bound,
            "deviceIdHash": row["device_id_hash"],
            "deviceTrust": {
                "deviceId": row["device_record_id"] if "device_record_id" in row_keys else None,
                "status": device_status,
                "trusted": device_status == "trusted",
                "attestationProvider": row["device_attestation_provider"] if "device_attestation_provider" in row_keys else None,
                "attestationVerified": bool(row["device_attestation_verified"]) if "device_attestation_verified" in row_keys else False,
                "evidence": device_evidence,
                "trustedAt": row["device_trusted_at"] if "device_trusted_at" in row_keys else None,
                "revokedAt": row["device_revoked_at"] if "device_revoked_at" in row_keys else None,
            },
            "accessExpiresAt": row["access_expires_at"],
            "refreshExpiresAt": row["refresh_expires_at"],
            "revokedAt": row["revoked_at"],
            "createdAt": row["created_at"],
            "lastUsedAt": row["last_used_at"],
        }

    def create_conversation(self, persona_id: str, practice_room_id: str, mode: str, learner_id: str = "local-dev") -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        conversation = {
            "id": new_id("conv"),
            "learnerId": learner_id,
            "personaId": persona_id,
            "practiceRoomId": practice_room_id,
            "mode": mode,
            "createdAt": now_iso(),
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO conversations (id, learner_id, persona_id, practice_room_id, mode, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    conversation["id"],
                    conversation["learnerId"],
                    conversation["personaId"],
                    conversation["practiceRoomId"],
                    conversation["mode"],
                    conversation["createdAt"],
                ),
            )
        return conversation

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "learnerId": row["learner_id"] or "local-dev",
            "personaId": row["persona_id"],
            "practiceRoomId": row["practice_room_id"],
            "mode": row["mode"],
            "createdAt": row["created_at"],
        }

    def add_message(
        self,
        conversation_id: str,
        role: str,
        text: str,
        input_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        message = {
            "id": new_id("msg"),
            "conversationId": conversation_id,
            "role": role,
            "inputType": input_type,
            "text": text,
            "metadata": metadata or {},
            "createdAt": now_iso(),
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO messages (id, conversation_id, role, input_type, text, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message["id"],
                    message["conversationId"],
                    message["role"],
                    message["inputType"],
                    message["text"],
                    _json(message["metadata"]),
                    message["createdAt"],
                ),
            )
        return message

    def save_review_card(
        self,
        card: Dict[str, Any],
        conversation_id: Optional[str] = None,
        learner_id: str = "local-dev",
    ) -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        saved = {
            "id": card.get("id") or new_id("card"),
            "learnerId": learner_id,
            "front": card["front"],
            "back": card["back"],
            "example": card.get("example"),
            "tags": list(card.get("tags") or []),
            "dueAt": card.get("dueAt") or (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "easeFactor": float(card.get("easeFactor") or 2.5),
            "intervalDays": int(card.get("intervalDays") or 0),
            "reviewCount": int(card.get("reviewCount") or 0),
            "lapses": int(card.get("lapses") or 0),
            "memoryStrengthDays": clamp_float(float(card.get("memoryStrengthDays") or 0.5), 0.25, 365.0),
            "memoryDifficulty": clamp_float(float(card.get("memoryDifficulty") or 0.65), 0.05, 0.95),
            "lastReviewQuality": card.get("lastReviewQuality"),
            "lastReviewedAt": card.get("lastReviewedAt"),
        }
        timestamp = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO review_cards
                (id, learner_id, conversation_id, front, back, example, tags_json, due_at, ease_factor, interval_days,
                 review_count, lapses, memory_strength_days, memory_difficulty, last_review_quality, last_reviewed_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM review_cards WHERE id = ?), ?), ?)
                """,
                (
                    saved["id"],
                    saved["learnerId"],
                    conversation_id,
                    saved["front"],
                    saved["back"],
                    saved["example"],
                    _json(saved["tags"]),
                    saved["dueAt"],
                    saved["easeFactor"],
                    saved["intervalDays"],
                    saved["reviewCount"],
                    saved["lapses"],
                    saved["memoryStrengthDays"],
                    saved["memoryDifficulty"],
                    saved["lastReviewQuality"],
                    saved["lastReviewedAt"],
                    saved["id"],
                    timestamp,
                    timestamp,
                ),
            )
        return saved

    def list_review_cards(self, learner_id: str = "local-dev") -> list[Dict[str, Any]]:
        learner_id = normalize_learner_id(learner_id)
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, learner_id, front, back, example, tags_json, due_at, ease_factor, interval_days, review_count, lapses,
                       memory_strength_days, memory_difficulty, last_review_quality, last_reviewed_at
                FROM review_cards
                WHERE learner_id = ?
                ORDER BY created_at DESC
                """,
                (learner_id,),
            ).fetchall()
        return [self._row_to_review_card(row) for row in rows]

    def list_due_review_cards(self, limit: int = 20, learner_id: str = "local-dev") -> list[Dict[str, Any]]:
        learner_id = normalize_learner_id(learner_id)
        now = now_iso()
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, learner_id, front, back, example, tags_json, due_at, ease_factor, interval_days, review_count, lapses,
                       memory_strength_days, memory_difficulty, last_review_quality, last_reviewed_at
                FROM review_cards
                WHERE learner_id = ? AND (due_at IS NULL OR due_at <= ? OR review_count = 0)
                ORDER BY due_at ASC, created_at DESC
                LIMIT ?
                """,
                (learner_id, now, int(limit)),
            ).fetchall()
        return [self._row_to_review_card(row) for row in rows]

    def get_review_card(self, card_id: str, learner_id: str = "local-dev") -> Optional[Dict[str, Any]]:
        learner_id = normalize_learner_id(learner_id)
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id, learner_id, front, back, example, tags_json, due_at, ease_factor, interval_days, review_count, lapses,
                       memory_strength_days, memory_difficulty, last_review_quality, last_reviewed_at
                FROM review_cards
                WHERE id = ? AND learner_id = ?
                """,
                (card_id, learner_id),
            ).fetchone()
        return self._row_to_review_card(row) if row else None

    def grade_review_card(self, card_id: str, quality: int, learner_id: str = "local-dev") -> Optional[Dict[str, Any]]:
        learner_id = normalize_learner_id(learner_id)
        card = self.get_review_card(card_id, learner_id=learner_id)
        if not card:
            return None
        bounded = max(0, min(5, int(quality)))
        ease = float(card.get("easeFactor") or 2.5)
        interval = int(card.get("intervalDays") or 0)
        review_count = int(card.get("reviewCount") or 0)
        lapses = int(card.get("lapses") or 0)
        memory_strength = float(card.get("memoryStrengthDays") or 0.5)
        memory_difficulty = float(card.get("memoryDifficulty") or 0.65)
        if bounded < 3:
            interval = 1
            review_count = 0
            lapses += 1
            memory_strength = clamp_float(memory_strength * (0.45 + bounded * 0.08), 0.25, 365.0)
            memory_difficulty = clamp_float(memory_difficulty + 0.08 + (3 - bounded) * 0.04, 0.05, 0.95)
        else:
            if review_count == 0:
                interval = 1
            elif review_count == 1:
                interval = 6
            else:
                interval = max(1, round(interval * ease))
            review_count += 1
            quality_bonus = (bounded - 2) / 3
            memory_strength = clamp_float(memory_strength * (1.35 + quality_bonus * 0.75) + review_count * 0.15, 1.0, 365.0)
            memory_difficulty = clamp_float(memory_difficulty - 0.03 * quality_bonus, 0.05, 0.95)
        ease = max(1.3, ease + (0.1 - (5 - bounded) * (0.08 + (5 - bounded) * 0.02)))
        reviewed_at = now_iso()
        due_at = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=interval)).isoformat(timespec="seconds").replace("+00:00", "Z")
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE review_cards
                SET ease_factor = ?, interval_days = ?, review_count = ?, lapses = ?,
                    memory_strength_days = ?, memory_difficulty = ?, last_review_quality = ?,
                    last_reviewed_at = ?, due_at = ?, updated_at = ?
                WHERE id = ? AND learner_id = ?
                """,
                (
                    round(ease, 2),
                    interval,
                    review_count,
                    lapses,
                    round(memory_strength, 2),
                    round(memory_difficulty, 2),
                    bounded,
                    reviewed_at,
                    due_at,
                    reviewed_at,
                    card_id,
                    learner_id,
                ),
            )
        updated = self.get_review_card(card_id, learner_id=learner_id)
        self.track_event(
            "review_card_graded",
            learner_id=learner_id,
            payload={
                "reviewCardId": card_id,
                "quality": bounded,
                "nextDueAt": due_at,
                "memoryStrengthDays": round(memory_strength, 2),
                "memoryDifficulty": round(memory_difficulty, 2),
            },
        )
        self.record_xp_event(
            learner_id=learner_id,
            source="review_card_graded",
            points=5 + bounded,
            payload={"reviewCardId": card_id, "quality": bounded},
            idempotency_key=f"review_card_graded:{card_id}:{reviewed_at}",
        )
        return updated

    def _row_to_review_card(self, row: sqlite3.Row) -> Dict[str, Any]:
        memory = self._memory_estimate(
            review_count=int(row["review_count"] or 0),
            last_reviewed_at=row["last_reviewed_at"],
            memory_strength_days=float(row["memory_strength_days"] or 0.5),
            memory_difficulty=float(row["memory_difficulty"] or 0.65),
        )
        return {
            "id": row["id"],
            "learnerId": row["learner_id"] or "local-dev",
            "front": row["front"],
            "back": row["back"],
            "example": row["example"],
            "tags": _loads(row["tags_json"], []),
            "dueAt": row["due_at"],
            "easeFactor": float(row["ease_factor"] or 2.5),
            "intervalDays": int(row["interval_days"] or 0),
            "reviewCount": int(row["review_count"] or 0),
            "lapses": int(row["lapses"] or 0),
            "memoryStrengthDays": round(float(row["memory_strength_days"] or 0.5), 2),
            "memoryDifficulty": round(float(row["memory_difficulty"] or 0.65), 2),
            "lastReviewQuality": row["last_review_quality"],
            "recallProbability": memory["recallProbability"],
            "recallRisk": memory["recallRisk"],
            "daysSinceReview": memory["daysSinceReview"],
            "lastReviewedAt": row["last_reviewed_at"],
        }

    def _memory_estimate(
        self,
        review_count: int,
        last_reviewed_at: Optional[str],
        memory_strength_days: float,
        memory_difficulty: float,
    ) -> Dict[str, Any]:
        if review_count <= 0 or not last_reviewed_at:
            return {
                "recallProbability": 0.0,
                "recallRisk": "new",
                "daysSinceReview": None,
            }
        parsed = parse_iso(last_reviewed_at)
        if not parsed:
            return {
                "recallProbability": 0.0,
                "recallRisk": "unknown",
                "daysSinceReview": None,
            }
        elapsed_days = max(0.0, (dt.datetime.now(dt.timezone.utc) - parsed).total_seconds() / 86400)
        half_life = max(0.25, float(memory_strength_days))
        recall = clamp_float(math.pow(2, -elapsed_days / half_life) * (1 - float(memory_difficulty) * 0.08), 0.0, 1.0)
        if recall < 0.55:
            risk = "high"
        elif recall < 0.8:
            risk = "medium"
        else:
            risk = "low"
        return {
            "recallProbability": round(recall, 3),
            "recallRisk": risk,
            "daysSinceReview": round(elapsed_days, 2),
        }

    def record_usage(
        self,
        usage: Dict[str, Any],
        conversation_id: Optional[str] = None,
        practice_room_id: Optional[str] = None,
        persona_id: Optional[str] = None,
        provider: Optional[Dict[str, Any]] = None,
        learner_id: str = "local-dev",
    ) -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        record = {
            "id": new_id("usage"),
            "learnerId": learner_id,
            "conversationId": conversation_id,
            "practiceRoomId": practice_room_id,
            "personaId": persona_id,
            "llmInputTokens": int(usage.get("llmInputTokens") or 0),
            "llmOutputTokens": int(usage.get("llmOutputTokens") or 0),
            "sttSeconds": float(usage.get("sttSeconds") or 0),
            "ttsCharacters": int(usage.get("ttsCharacters") or 0),
            "ttsSeconds": float(usage.get("ttsSeconds") or 0),
            "cacheHit": bool(usage.get("cacheHit") or False),
            "createdAt": now_iso(),
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO usage_records
                (id, learner_id, conversation_id, practice_room_id, persona_id, llm_input_tokens, llm_output_tokens,
                 stt_seconds, tts_characters, tts_seconds, cache_hit, provider_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["id"],
                    learner_id,
                    conversation_id,
                    practice_room_id,
                    persona_id,
                    record["llmInputTokens"],
                    record["llmOutputTokens"],
                    record["sttSeconds"],
                    record["ttsCharacters"],
                    record["ttsSeconds"],
                    int(record["cacheHit"]),
                    _json(provider or {}),
                    record["createdAt"],
                ),
            )
        return record

    def get_tts_cache(self, cache_key: str, learner_id: str = "local-dev") -> Optional[Dict[str, Any]]:
        learner_id = normalize_learner_id(learner_id)
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM tts_cache WHERE cache_key = ? AND learner_id = ?", (cache_key, learner_id)).fetchone()
            if row:
                conn.execute("UPDATE tts_cache SET last_used_at = ? WHERE cache_key = ?", (now_iso(), cache_key))
        if not row:
            return None
        return {
            "audioBase64": row["audio_base64"],
            "durationMs": row["duration_ms"],
            "contentType": row["content_type"] or "audio/wav",
            "audioUrl": f"data:{row['content_type'] or 'audio/wav'};base64," + row["audio_base64"],
        }

    def save_tts_cache(
        self,
        cache_key: str,
        text: str,
        persona_id: str,
        language: str,
        speed: Optional[float],
        emotion: Optional[str],
        audio_base64: str,
        duration_ms: int,
        content_type: str = "audio/wav",
        learner_id: str = "local-dev",
    ) -> None:
        learner_id = normalize_learner_id(learner_id)
        timestamp = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO tts_cache
                (cache_key, learner_id, text, persona_id, language, speed, emotion, content_type, audio_base64, duration_ms, created_at, last_used_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM tts_cache WHERE cache_key = ?), ?), ?)
                """,
                (cache_key, learner_id, text, persona_id, language, speed, emotion, content_type, audio_base64, duration_ms, cache_key, timestamp, timestamp),
            )

    def log_dialogue_unmatched(
        self,
        persona_id: str,
        pack_version: str,
        node_id: str,
        utterance: str,
        stt_confidence: Optional[float] = None,
        learner_id: str = "local-dev",
    ) -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        timestamp = now_iso()
        record = {
            "id": new_id("du"),
            "learnerId": learner_id,
            "personaId": persona_id,
            "packVersion": pack_version,
            "nodeId": node_id,
            "utterance": utterance,
            "sttConfidence": stt_confidence,
            "status": "new",
            "createdAt": timestamp,
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO dialogue_unmatched
                (id, learner_id, persona_id, pack_version, node_id, utterance, stt_confidence, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["id"],
                    learner_id,
                    persona_id,
                    pack_version,
                    node_id,
                    utterance,
                    stt_confidence,
                    record["status"],
                    timestamp,
                ),
            )
        return record

    def list_dialogue_unmatched(self, limit: int = 100, status: str = "new") -> list[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM dialogue_unmatched
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (status, int(limit)),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "learnerId": row["learner_id"],
                "personaId": row["persona_id"],
                "packVersion": row["pack_version"],
                "nodeId": row["node_id"],
                "utterance": row["utterance"],
                "sttConfidence": row["stt_confidence"],
                "status": row["status"],
                "createdAt": row["created_at"],
            }
            for row in rows
        ]

    def track_event(
        self,
        event_name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        learner_id: str = "local-dev",
    ) -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        event = {
            "id": new_id("evt"),
            "learnerId": learner_id,
            "eventName": event_name,
            "userId": user_id,
            "sessionId": session_id,
            "payload": payload or {},
            "createdAt": now_iso(),
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO analytics_events (id, learner_id, event_name, user_id, session_id, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (event["id"], learner_id, event["eventName"], user_id, session_id, _json(event["payload"]), event["createdAt"]),
            )
        return event

    def record_xp_event(
        self,
        learner_id: str,
        source: str,
        points: int,
        payload: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        timestamp = created_at or now_iso()
        base_points = max(0, int(points))
        event_payload = dict(payload or {})
        event = {
            "id": new_id("xp"),
            "learnerId": learner_id,
            "source": (source or "manual").strip()[:80] or "manual",
            "points": base_points,
            "dayKey": day_key_from_iso(timestamp),
            "idempotencyKey": idempotency_key,
            "payload": event_payload,
            "createdAt": timestamp,
        }
        with self.connect() as conn:
            if idempotency_key:
                existing = conn.execute(
                    "SELECT * FROM xp_events WHERE idempotency_key = ?",
                    (idempotency_key,),
                ).fetchone()
                if existing:
                    return self._row_to_xp_event(existing)
            active_boost = self._active_xp_boost_for_conn(conn, learner_id=learner_id, timestamp=timestamp)
            if active_boost and base_points > 0:
                boosted_points = int(round(base_points * float(active_boost["multiplier"])))
                event["points"] = max(base_points, boosted_points)
                event_payload = dict(event_payload)
                event_payload["xpBoostApplied"] = {
                    "boostId": active_boost["id"],
                    "rewardKey": active_boost["rewardKey"],
                    "multiplier": active_boost["multiplier"],
                    "basePoints": base_points,
                    "bonusPoints": event["points"] - base_points,
                    "expiresAt": active_boost["expiresAt"],
                }
                event["payload"] = event_payload
            conn.execute(
                """
                INSERT INTO xp_events
                (id, learner_id, source, points, day_key, idempotency_key, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["id"],
                    learner_id,
                    event["source"],
                    event["points"],
                    event["dayKey"],
                    idempotency_key,
                    _json(event["payload"]),
                    timestamp,
                ),
            )
            earned_gems = max(0, int(event["points"]) // 10)
            if earned_gems > 0:
                self._record_reward_currency_for_conn(
                    conn,
                    learner_id=learner_id,
                    currency_key="gems",
                    amount=earned_gems,
                    reason="xp_earned",
                    source_ref=event["id"],
                    idempotency_key=f"xp_gems:{event['id']}",
                    metadata={"xpEventId": event["id"], "xpPoints": event["points"], "source": event["source"]},
                    created_at=timestamp,
                )
        self.refresh_achievement_awards(learner_id=learner_id)
        self.flag_xp_anomalies(learner_id=learner_id, day_key=event["dayKey"])
        return event

    def gamification_summary(self, learner_id: str = "local-dev") -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        return {
            "xp": self.xp_summary(learner_id=learner_id),
            "streak": self.streak_summary(learner_id=learner_id),
            "dailyQuests": self.daily_quests(learner_id=learner_id),
            "friends": self.friends_summary(learner_id=learner_id),
            "friendQuests": self.list_friend_quests(learner_id=learner_id)["friendQuests"],
            "rewardInventory": self.reward_inventory_summary(learner_id=learner_id),
            "activeXpBoosts": self.active_xp_boosts(learner_id=learner_id),
            "weeklyLeaderboard": self.weekly_leaderboard(learner_id=learner_id, limit=20),
            "league": self.league_status(learner_id=learner_id),
            "achievements": self.achievements_summary(learner_id=learner_id),
            "xpAbuseFlags": self.list_xp_abuse_flags(learner_id=learner_id, limit=20),
        }

    def xp_summary(self, learner_id: str = "local-dev") -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        today = dt.datetime.now(dt.timezone.utc).date()
        week_start = today - dt.timedelta(days=today.weekday())
        with self.connect() as conn:
            totals = conn.execute(
                """
                SELECT
                  COALESCE(SUM(points), 0) AS total_xp,
                  COALESCE(SUM(CASE WHEN day_key = ? THEN points ELSE 0 END), 0) AS today_xp,
                  COALESCE(SUM(CASE WHEN day_key >= ? THEN points ELSE 0 END), 0) AS week_xp,
                  COUNT(*) AS event_count
                FROM xp_events
                WHERE learner_id = ?
                """,
                (today.isoformat(), week_start.isoformat(), learner_id),
            ).fetchone()
        return {
            "learnerId": learner_id,
            "todayXp": int(totals["today_xp"] or 0),
            "weekXp": int(totals["week_xp"] or 0),
            "totalXp": int(totals["total_xp"] or 0),
            "eventCount": int(totals["event_count"] or 0),
            "weekStart": week_start.isoformat(),
        }

    def streak_summary(self, learner_id: str = "local-dev") -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT day_key
                FROM xp_events
                WHERE learner_id = ?
                ORDER BY day_key ASC
                """,
                (learner_id,),
            ).fetchall()
        active_dates = [dt.date.fromisoformat(row["day_key"]) for row in rows]
        if not active_dates:
            return {
                "learnerId": learner_id,
                "currentStreak": 0,
                "longestStreak": 0,
                "activeDays": 0,
                "lastActiveDate": None,
                "isActiveToday": False,
            }
        longest = 1
        run = 1
        for previous, current in zip(active_dates, active_dates[1:]):
            if current == previous + dt.timedelta(days=1):
                run += 1
            else:
                run = 1
            longest = max(longest, run)
        current_streak = 1
        for previous, current in zip(reversed(active_dates[:-1]), reversed(active_dates[1:])):
            if current == previous + dt.timedelta(days=1):
                current_streak += 1
            else:
                break
        today = dt.datetime.now(dt.timezone.utc).date()
        return {
            "learnerId": learner_id,
            "currentStreak": current_streak,
            "longestStreak": longest,
            "activeDays": len(active_dates),
            "lastActiveDate": active_dates[-1].isoformat(),
            "isActiveToday": active_dates[-1] == today,
        }

    def daily_quests(self, learner_id: str = "local-dev") -> list[Dict[str, Any]]:
        learner_id = normalize_learner_id(learner_id)
        day_key = today_key()
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM xp_events
                WHERE learner_id = ? AND day_key = ?
                ORDER BY created_at ASC, id ASC
                """,
                (learner_id, day_key),
            ).fetchall()
        events = [self._row_to_xp_event(row) for row in rows]
        quests: list[Dict[str, Any]] = []
        for quest in DAILY_QUESTS:
            progress = 0
            completed_at = None
            if quest["metric"] == "source_count":
                matching = [event for event in events if event["source"] == quest["source"]]
                progress = len(matching)
                if progress >= quest["target"]:
                    completed_at = matching[quest["target"] - 1]["createdAt"]
            elif quest["metric"] == "xp_sum":
                running = 0
                for event in events:
                    running += int(event["points"])
                    if running >= quest["target"] and completed_at is None:
                        completed_at = event["createdAt"]
                progress = running
            quests.append(
                {
                    "key": quest["key"],
                    "title": quest["title"],
                    "metric": quest["metric"],
                    "source": quest["source"],
                    "target": quest["target"],
                    "progress": min(progress, quest["target"]),
                    "rawProgress": progress,
                    "rewardXp": quest["rewardXp"],
                    "completed": progress >= quest["target"],
                    "completedAt": completed_at,
                    "dayKey": day_key,
                }
            )
        return quests

    def friend_pair(self, learner_id: str, other_learner_id: str) -> tuple[str, str]:
        first = normalize_learner_id(learner_id)
        second = normalize_learner_id(other_learner_id)
        return tuple(sorted([first, second]))  # type: ignore[return-value]

    def friends_summary(self, learner_id: str = "local-dev") -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        with self.connect() as conn:
            friend_rows = conn.execute(
                """
                SELECT *
                FROM friend_relationships
                WHERE status = 'active' AND (learner_a_id = ? OR learner_b_id = ?)
                ORDER BY updated_at DESC, id ASC
                """,
                (learner_id, learner_id),
            ).fetchall()
            incoming_rows = conn.execute(
                """
                SELECT *
                FROM friend_invites
                WHERE addressee_learner_id = ? AND status = 'pending'
                ORDER BY created_at DESC, id ASC
                """,
                (learner_id,),
            ).fetchall()
            outgoing_rows = conn.execute(
                """
                SELECT *
                FROM friend_invites
                WHERE requester_learner_id = ? AND status = 'pending'
                ORDER BY created_at DESC, id ASC
                """,
                (learner_id,),
            ).fetchall()
        return {
            "learnerId": learner_id,
            "friends": [self._row_to_friend_relationship(row, learner_id=learner_id) for row in friend_rows],
            "incomingInvites": [self._row_to_friend_invite(row) for row in incoming_rows],
            "outgoingInvites": [self._row_to_friend_invite(row) for row in outgoing_rows],
            "friendCount": len(friend_rows),
        }

    def social_settings(self, learner_id: str = "local-dev") -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        with self.connect() as conn:
            row = self._ensure_social_settings_for_conn(conn, learner_id)
            return self._row_to_social_settings(row)

    def update_social_settings(
        self,
        learner_id: str = "local-dev",
        discoverable: bool = True,
        allow_friend_invites: bool = True,
        show_weekly_xp: bool = True,
    ) -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        timestamp = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO social_settings
                (learner_id, discoverable, allow_friend_invites, show_weekly_xp, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(learner_id)
                DO UPDATE SET
                  discoverable = excluded.discoverable,
                  allow_friend_invites = excluded.allow_friend_invites,
                  show_weekly_xp = excluded.show_weekly_xp,
                  updated_at = excluded.updated_at
                """,
                (learner_id, int(discoverable), int(allow_friend_invites), int(show_weekly_xp), timestamp, timestamp),
            )
            row = conn.execute("SELECT * FROM social_settings WHERE learner_id = ?", (learner_id,)).fetchone()
        return self._row_to_social_settings(row)

    def list_social_blocks(self, learner_id: str = "local-dev") -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM social_blocks
                WHERE blocker_learner_id = ?
                ORDER BY created_at DESC, blocked_learner_id ASC
                """,
                (learner_id,),
            ).fetchall()
        return {"learnerId": learner_id, "blocks": [self._row_to_social_block(row) for row in rows], "count": len(rows)}

    def block_learner(self, learner_id: str, blocked_learner_id: str) -> Dict[str, Any]:
        blocker = normalize_learner_id(learner_id)
        blocked = normalize_learner_id(blocked_learner_id)
        if blocker == blocked:
            return {"block": None, "blocked": False, "reason": "cannot_block_self"}
        learner_a, learner_b = self.friend_pair(blocker, blocked)
        timestamp = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO social_blocks
                (id, blocker_learner_id, blocked_learner_id, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (new_id("socialblock"), blocker, blocked, timestamp),
            )
            conn.execute(
                """
                UPDATE friend_invites
                SET status = 'blocked', updated_at = ?, responded_at = ?
                WHERE status = 'pending'
                  AND ((requester_learner_id = ? AND addressee_learner_id = ?)
                    OR (requester_learner_id = ? AND addressee_learner_id = ?))
                """,
                (timestamp, timestamp, blocker, blocked, blocked, blocker),
            )
            conn.execute(
                """
                UPDATE friend_relationships
                SET status = 'removed', removed_at = ?, updated_at = ?
                WHERE learner_a_id = ? AND learner_b_id = ? AND status = 'active'
                """,
                (timestamp, timestamp, learner_a, learner_b),
            )
            row = conn.execute(
                "SELECT * FROM social_blocks WHERE blocker_learner_id = ? AND blocked_learner_id = ?",
                (blocker, blocked),
            ).fetchone()
        return {"block": self._row_to_social_block(row), "blocked": True, "reason": "blocked"}

    def unblock_learner(self, learner_id: str, blocked_learner_id: str) -> Dict[str, Any]:
        blocker = normalize_learner_id(learner_id)
        blocked = normalize_learner_id(blocked_learner_id)
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT * FROM social_blocks WHERE blocker_learner_id = ? AND blocked_learner_id = ?",
                (blocker, blocked),
            ).fetchone()
            conn.execute(
                "DELETE FROM social_blocks WHERE blocker_learner_id = ? AND blocked_learner_id = ?",
                (blocker, blocked),
            )
        return {"unblocked": bool(existing), "learnerId": blocker, "blockedLearnerId": blocked}

    def social_discovery(
        self,
        learner_id: str = "local-dev",
        limit: int = 10,
        target_language: Optional[str] = None,
    ) -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        bounded_limit = max(1, min(50, int(limit)))
        week_start, week_end, _ = current_week_window()
        profile = self.get_profile(learner_id)
        learner_target_language = (target_language or profile.get("targetLanguage") or "").strip().lower()
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT learner_id, COALESCE(SUM(points), 0) AS week_xp, COUNT(*) AS event_count, MAX(created_at) AS last_active_at
                FROM xp_events
                WHERE learner_id != ? AND day_key >= ? AND day_key < ?
                GROUP BY learner_id
                ORDER BY week_xp DESC, event_count DESC, learner_id ASC
                LIMIT 300
                """,
                (learner_id, week_start, week_end),
            ).fetchall()
            relationship_rows = conn.execute(
                """
                SELECT learner_a_id, learner_b_id, status
                FROM friend_relationships
                WHERE status = 'active'
                """
            ).fetchall()
            pending_rows = conn.execute(
                """
                SELECT requester_learner_id, addressee_learner_id
                FROM friend_invites
                WHERE status = 'pending'
                """
            ).fetchall()
            block_rows = conn.execute(
                """
                SELECT blocker_learner_id, blocked_learner_id
                FROM social_blocks
                WHERE blocker_learner_id = ? OR blocked_learner_id = ?
                """,
                (learner_id, learner_id),
            ).fetchall()
            settings_rows = conn.execute("SELECT * FROM social_settings").fetchall()
        settings_by_id = {row["learner_id"]: self._row_to_social_settings(row) for row in settings_rows}
        friend_ids: set[str] = set()
        all_friend_ids: Dict[str, set[str]] = {}
        for row in relationship_rows:
            a = row["learner_a_id"]
            b = row["learner_b_id"]
            all_friend_ids.setdefault(a, set()).add(b)
            all_friend_ids.setdefault(b, set()).add(a)
            if a == learner_id:
                friend_ids.add(b)
            elif b == learner_id:
                friend_ids.add(a)
        pending_ids = {
            row["addressee_learner_id"] if row["requester_learner_id"] == learner_id else row["requester_learner_id"]
            for row in pending_rows
            if row["requester_learner_id"] == learner_id or row["addressee_learner_id"] == learner_id
        }
        blocked_ids = {
            row["blocked_learner_id"] if row["blocker_learner_id"] == learner_id else row["blocker_learner_id"]
            for row in block_rows
        }
        candidates = []
        excluded_private = 0
        excluded_blocked = 0
        excluded_connected = 0
        for row in rows:
            candidate_id = row["learner_id"]
            if candidate_id in friend_ids or candidate_id in pending_ids:
                excluded_connected += 1
                continue
            if candidate_id in blocked_ids:
                excluded_blocked += 1
                continue
            settings = settings_by_id.get(candidate_id) or self._default_social_settings(candidate_id)
            if not settings["discoverable"] or not settings["allowFriendInvites"]:
                excluded_private += 1
                continue
            candidate_profile = self.get_profile(candidate_id)
            if learner_target_language and (candidate_profile.get("targetLanguage") or "").lower() != learner_target_language:
                continue
            mutual = sorted(all_friend_ids.get(learner_id, set()) & all_friend_ids.get(candidate_id, set()))
            week_xp = int(row["week_xp"] or 0)
            language_match = candidate_profile.get("targetLanguage") == profile.get("targetLanguage")
            level_match = candidate_profile.get("level") == profile.get("level") or candidate_profile.get("jlptLevel") == profile.get("jlptLevel")
            mutual_friend_count = len(mutual)
            score = week_xp / 1000.0 + (0.4 if language_match else 0.0) + (0.2 if level_match else 0.0) + min(0.3, mutual_friend_count * 0.1)
            reason_codes = []
            if language_match:
                reason_codes.append("target_language_match")
            if level_match:
                reason_codes.append("level_match")
            if mutual_friend_count:
                reason_codes.append("mutual_friends")
            if week_xp >= 30:
                reason_codes.append("active_this_week")
            if not reason_codes:
                reason_codes.append("discoverable_learner")
            candidates.append(
                {
                    "learnerId": candidate_id,
                    "score": round(score, 4),
                    "reasonCodes": reason_codes,
                    "weekXp": week_xp if settings["showWeeklyXp"] else None,
                    "eventCount": int(row["event_count"] or 0),
                    "lastActiveAt": row["last_active_at"],
                    "profile": {
                        "nativeLanguage": candidate_profile.get("nativeLanguage"),
                        "targetLanguage": candidate_profile.get("targetLanguage"),
                        "level": candidate_profile.get("level"),
                        "jlptLevel": candidate_profile.get("jlptLevel"),
                    },
                    "mutualFriendCount": mutual_friend_count,
                    "mutualFriendLearnerIds": mutual[:5],
                    "canInvite": True,
                    "friendQuestEligible": True,
                }
            )
        candidates.sort(key=lambda item: (-float(item["score"]), -(item["weekXp"] or 0), item["learnerId"]))
        return {
            "learnerId": learner_id,
            "weekStart": week_start,
            "weekEnd": week_end,
            "candidates": candidates[:bounded_limit],
            "count": min(len(candidates), bounded_limit),
            "excludedFriendOrPendingCount": excluded_connected,
            "excludedBlockedCount": excluded_blocked,
            "excludedPrivateCount": excluded_private,
        }

    def friend_recommendations(self, learner_id: str = "local-dev", limit: int = 10) -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        bounded_limit = max(1, min(50, int(limit)))
        week_start, week_end, _ = current_week_window()
        profile = self.get_profile(learner_id)
        with self.connect() as conn:
            learner_week = conn.execute(
                """
                SELECT COALESCE(SUM(points), 0) AS week_xp
                FROM xp_events
                WHERE learner_id = ? AND day_key >= ? AND day_key < ?
                """,
                (learner_id, week_start, week_end),
            ).fetchone()
            learner_source_rows = conn.execute(
                """
                SELECT source
                FROM xp_events
                WHERE learner_id = ? AND day_key >= ? AND day_key < ?
                GROUP BY source
                """,
                (learner_id, week_start, week_end),
            ).fetchall()
            friend_rows = conn.execute(
                """
                SELECT learner_a_id, learner_b_id
                FROM friend_relationships
                WHERE status = 'active' AND (learner_a_id = ? OR learner_b_id = ?)
                """,
                (learner_id, learner_id),
            ).fetchall()
            pending_rows = conn.execute(
                """
                SELECT requester_learner_id, addressee_learner_id
                FROM friend_invites
                WHERE status = 'pending' AND (requester_learner_id = ? OR addressee_learner_id = ?)
                """,
                (learner_id, learner_id),
            ).fetchall()
            candidate_rows = conn.execute(
                """
                SELECT learner_id, COALESCE(SUM(points), 0) AS week_xp, COUNT(*) AS event_count, MAX(created_at) AS last_active_at
                FROM xp_events
                WHERE learner_id != ? AND day_key >= ? AND day_key < ?
                GROUP BY learner_id
                ORDER BY week_xp DESC, event_count DESC, learner_id ASC
                LIMIT 200
                """,
                (learner_id, week_start, week_end),
            ).fetchall()
            candidate_source_rows = conn.execute(
                """
                SELECT learner_id, source
                FROM xp_events
                WHERE learner_id != ? AND day_key >= ? AND day_key < ?
                GROUP BY learner_id, source
                """,
                (learner_id, week_start, week_end),
            ).fetchall()
            block_rows = conn.execute(
                """
                SELECT blocker_learner_id, blocked_learner_id
                FROM social_blocks
                WHERE blocker_learner_id = ? OR blocked_learner_id = ?
                """,
                (learner_id, learner_id),
            ).fetchall()
            settings_rows = conn.execute("SELECT * FROM social_settings").fetchall()
        friend_ids = {
            row["learner_b_id"] if row["learner_a_id"] == learner_id else row["learner_a_id"]
            for row in friend_rows
        }
        pending_ids = {
            row["addressee_learner_id"] if row["requester_learner_id"] == learner_id else row["requester_learner_id"]
            for row in pending_rows
        }
        social_blocked_ids = {
            row["blocked_learner_id"] if row["blocker_learner_id"] == learner_id else row["blocker_learner_id"]
            for row in block_rows
        }
        settings_by_id = {row["learner_id"]: self._row_to_social_settings(row) for row in settings_rows}
        blocked_ids = friend_ids | pending_ids | social_blocked_ids | {learner_id}
        learner_sources = {row["source"] for row in learner_source_rows}
        candidate_sources: Dict[str, set[str]] = {}
        for row in candidate_source_rows:
            candidate_sources.setdefault(row["learner_id"], set()).add(row["source"])
        learner_xp = int(learner_week["week_xp"] or 0) if learner_week else 0
        recommendations = []
        excluded_private = 0
        excluded_blocked = 0
        for row in candidate_rows:
            candidate_id = row["learner_id"]
            if candidate_id in blocked_ids:
                if candidate_id in social_blocked_ids:
                    excluded_blocked += 1
                continue
            settings = settings_by_id.get(candidate_id) or self._default_social_settings(candidate_id)
            if not settings["discoverable"] or not settings["allowFriendInvites"]:
                excluded_private += 1
                continue
            candidate_profile = self.get_profile(candidate_id)
            candidate_xp = int(row["week_xp"] or 0)
            max_xp = max(1, learner_xp, candidate_xp)
            xp_similarity = 1.0 - min(1.0, abs(candidate_xp - learner_xp) / max_xp)
            language_match = candidate_profile.get("targetLanguage") == profile.get("targetLanguage")
            level_match = candidate_profile.get("level") == profile.get("level")
            jlpt_match = candidate_profile.get("jlptLevel") == profile.get("jlptLevel")
            shared_sources = sorted(learner_sources & candidate_sources.get(candidate_id, set()))
            source_union = learner_sources | candidate_sources.get(candidate_id, set())
            source_similarity = len(shared_sources) / max(1, len(source_union))
            score = (
                (0.35 if language_match else 0.0)
                + (0.15 if level_match else 0.0)
                + (0.10 if jlpt_match else 0.0)
                + (0.25 * xp_similarity)
                + (0.15 * source_similarity)
            )
            reason_codes = []
            if language_match:
                reason_codes.append("target_language_match")
            if level_match or jlpt_match:
                reason_codes.append("level_match")
            if xp_similarity >= 0.5:
                reason_codes.append("similar_weekly_xp")
            if shared_sources:
                reason_codes.append("shared_practice_sources")
            if not reason_codes:
                reason_codes.append("active_this_week")
            recommendations.append(
                {
                    "learnerId": candidate_id,
                    "score": round(score, 4),
                    "reasonCodes": reason_codes,
                    "weekXp": candidate_xp,
                    "eventCount": int(row["event_count"] or 0),
                    "lastActiveAt": row["last_active_at"],
                    "profile": {
                        "nativeLanguage": candidate_profile.get("nativeLanguage"),
                        "targetLanguage": candidate_profile.get("targetLanguage"),
                        "level": candidate_profile.get("level"),
                        "jlptLevel": candidate_profile.get("jlptLevel"),
                    },
                    "sharedSources": shared_sources,
                    "alreadyFriend": False,
                    "pendingInvite": False,
                }
            )
        recommendations.sort(key=lambda item: (-float(item["score"]), -int(item["weekXp"]), item["learnerId"]))
        return {
            "learnerId": learner_id,
            "weekStart": week_start,
            "weekEnd": week_end,
            "recommendations": recommendations[:bounded_limit],
            "count": min(len(recommendations), bounded_limit),
            "excludedFriendCount": len(friend_ids),
            "excludedPendingInviteCount": len(pending_ids),
            "excludedBlockedCount": excluded_blocked,
            "excludedPrivateCount": excluded_private,
        }

    def create_friend_invite(
        self,
        learner_id: str,
        friend_learner_id: str,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        requester = normalize_learner_id(learner_id)
        addressee = normalize_learner_id(friend_learner_id)
        if requester == addressee:
            return {"invite": None, "relationship": None, "created": False, "reason": "cannot_invite_self"}
        learner_a, learner_b = self.friend_pair(requester, addressee)
        timestamp = now_iso()
        with self.connect() as conn:
            block = conn.execute(
                """
                SELECT *
                FROM social_blocks
                WHERE (blocker_learner_id = ? AND blocked_learner_id = ?)
                   OR (blocker_learner_id = ? AND blocked_learner_id = ?)
                """,
                (requester, addressee, addressee, requester),
            ).fetchone()
            if block:
                return {"invite": None, "relationship": None, "created": False, "reason": "blocked"}
            addressee_settings = self._ensure_social_settings_for_conn(conn, addressee)
            settings = self._row_to_social_settings(addressee_settings)
            if not settings["allowFriendInvites"]:
                return {"invite": None, "relationship": None, "created": False, "reason": "invite_not_allowed"}
            relationship = conn.execute(
                """
                SELECT *
                FROM friend_relationships
                WHERE learner_a_id = ? AND learner_b_id = ? AND status = 'active'
                """,
                (learner_a, learner_b),
            ).fetchone()
            if relationship:
                return {
                    "invite": None,
                    "relationship": self._row_to_friend_relationship(relationship, learner_id=requester),
                    "created": False,
                    "reason": "already_friends",
                }
            reverse = conn.execute(
                """
                SELECT *
                FROM friend_invites
                WHERE requester_learner_id = ? AND addressee_learner_id = ? AND status = 'pending'
                """,
                (addressee, requester),
            ).fetchone()
            if reverse:
                return {"invite": self._row_to_friend_invite(reverse), "relationship": None, "created": False, "reason": "reverse_invite_pending"}
            existing = conn.execute(
                """
                SELECT *
                FROM friend_invites
                WHERE requester_learner_id = ? AND addressee_learner_id = ?
                """,
                (requester, addressee),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE friend_invites
                    SET status = 'pending', message = ?, updated_at = ?, responded_at = NULL
                    WHERE id = ?
                    """,
                    ((message or "").strip()[:240] or None, timestamp, existing["id"]),
                )
                invite_id = existing["id"]
            else:
                invite_id = new_id("friendinvite")
                conn.execute(
                    """
                    INSERT INTO friend_invites
                    (id, requester_learner_id, addressee_learner_id, status, message, created_at, updated_at)
                    VALUES (?, ?, ?, 'pending', ?, ?, ?)
                    """,
                    (invite_id, requester, addressee, (message or "").strip()[:240] or None, timestamp, timestamp),
                )
            invite = conn.execute("SELECT * FROM friend_invites WHERE id = ?", (invite_id,)).fetchone()
        return {"invite": self._row_to_friend_invite(invite), "relationship": None, "created": True, "reason": "created"}

    def accept_friend_invite(self, learner_id: str, invite_id: str) -> Optional[Dict[str, Any]]:
        addressee = normalize_learner_id(learner_id)
        timestamp = now_iso()
        with self.connect() as conn:
            invite = conn.execute(
                """
                SELECT *
                FROM friend_invites
                WHERE id = ? AND addressee_learner_id = ?
                """,
                (invite_id, addressee),
            ).fetchone()
            if not invite:
                return None
            if invite["status"] != "pending":
                learner_a, learner_b = self.friend_pair(invite["requester_learner_id"], invite["addressee_learner_id"])
                relationship = conn.execute(
                    "SELECT * FROM friend_relationships WHERE learner_a_id = ? AND learner_b_id = ?",
                    (learner_a, learner_b),
                ).fetchone()
                return {
                    "invite": self._row_to_friend_invite(invite),
                    "relationship": self._row_to_friend_relationship(relationship, learner_id=addressee) if relationship else None,
                    "accepted": invite["status"] == "accepted",
                    "alreadyResponded": True,
                }
            learner_a, learner_b = self.friend_pair(invite["requester_learner_id"], invite["addressee_learner_id"])
            conn.execute(
                """
                INSERT INTO friend_relationships
                (id, learner_a_id, learner_b_id, status, created_at, updated_at)
                VALUES (?, ?, ?, 'active', ?, ?)
                ON CONFLICT(learner_a_id, learner_b_id)
                DO UPDATE SET
                  status = 'active',
                  removed_at = NULL,
                  updated_at = excluded.updated_at
                """,
                (new_id("friendrel"), learner_a, learner_b, timestamp, timestamp),
            )
            conn.execute(
                """
                UPDATE friend_invites
                SET status = 'accepted', updated_at = ?, responded_at = ?
                WHERE id = ?
                """,
                (timestamp, timestamp, invite_id),
            )
            updated_invite = conn.execute("SELECT * FROM friend_invites WHERE id = ?", (invite_id,)).fetchone()
            relationship = conn.execute(
                "SELECT * FROM friend_relationships WHERE learner_a_id = ? AND learner_b_id = ?",
                (learner_a, learner_b),
            ).fetchone()
        self.refresh_achievement_awards(learner_id=invite["requester_learner_id"])
        self.refresh_achievement_awards(learner_id=addressee)
        return {
            "invite": self._row_to_friend_invite(updated_invite),
            "relationship": self._row_to_friend_relationship(relationship, learner_id=addressee),
            "accepted": True,
            "alreadyResponded": False,
        }

    def remove_friend(self, learner_id: str, friend_learner_id: str) -> Optional[Dict[str, Any]]:
        learner_id = normalize_learner_id(learner_id)
        friend_id = normalize_learner_id(friend_learner_id)
        learner_a, learner_b = self.friend_pair(learner_id, friend_id)
        timestamp = now_iso()
        with self.connect() as conn:
            relationship = conn.execute(
                "SELECT * FROM friend_relationships WHERE learner_a_id = ? AND learner_b_id = ?",
                (learner_a, learner_b),
            ).fetchone()
            if not relationship:
                return None
            conn.execute(
                """
                UPDATE friend_relationships
                SET status = 'removed', removed_at = ?, updated_at = ?
                WHERE learner_a_id = ? AND learner_b_id = ?
                """,
                (timestamp, timestamp, learner_a, learner_b),
            )
            updated = conn.execute(
                "SELECT * FROM friend_relationships WHERE learner_a_id = ? AND learner_b_id = ?",
                (learner_a, learner_b),
            ).fetchone()
        return {"relationship": self._row_to_friend_relationship(updated, learner_id=learner_id), "removed": True}

    def list_friend_quests(
        self,
        learner_id: str = "local-dev",
        partner_learner_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        week_start, week_end, week_key = current_week_window()
        partner = normalize_learner_id(partner_learner_id) if partner_learner_id else self.suggest_friend_partner(learner_id)
        if partner == learner_id:
            partner = f"{learner_id}_partner"
        ensured = self.ensure_friend_quest(learner_id=learner_id, partner_learner_id=partner)
        with self.connect() as conn:
            params: list[Any] = [learner_id, week_key]
            partner_filter = ""
            if partner_learner_id:
                partner_filter = " AND partner_learner_id = ?"
                params.append(partner)
            rows = conn.execute(
                f"""
                SELECT *
                FROM friend_quests
                WHERE learner_id = ? AND week_key = ?{partner_filter}
                ORDER BY created_at ASC, id ASC
                """,
                params,
            ).fetchall()
            quests = [self._friend_quest_from_row(conn, row, week_start, week_end) for row in rows]
        return {
            "friendQuests": quests,
            "suggestedPartnerLearnerId": ensured["partnerLearnerId"],
            "weekStart": week_start,
            "weekEnd": week_end,
        }

    def suggest_friend_partner(self, learner_id: str) -> str:
        learner_id = normalize_learner_id(learner_id)
        week_start, week_end, _ = current_week_window()
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT learner_id, COALESCE(SUM(points), 0) AS xp
                FROM xp_events
                WHERE learner_id != ? AND day_key >= ? AND day_key < ?
                GROUP BY learner_id
                ORDER BY xp DESC, learner_id ASC
                LIMIT 1
                """,
                (learner_id, week_start, week_end),
            ).fetchone()
        if row:
            return normalize_learner_id(row["learner_id"])
        digest = hashlib.sha256(learner_id.encode("utf-8")).hexdigest()[:8]
        return f"friend_{digest}"

    def ensure_friend_quest(self, learner_id: str, partner_learner_id: str) -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        partner = normalize_learner_id(partner_learner_id)
        if partner == learner_id:
            partner = f"{learner_id}_partner"
        week_start, week_end, week_key = current_week_window()
        template = FRIEND_QUEST_TEMPLATES[0]
        timestamp = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO friend_quests
                (id, quest_key, learner_id, partner_learner_id, week_key, target_xp, reward_key, reward_quantity, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id("friendquest"),
                    template["key"],
                    learner_id,
                    partner,
                    week_key,
                    int(template["targetXp"]),
                    template["rewardKey"],
                    int(template["rewardQuantity"]),
                    timestamp,
                    timestamp,
                ),
            )
            row = conn.execute(
                """
                SELECT *
                FROM friend_quests
                WHERE learner_id = ? AND partner_learner_id = ? AND quest_key = ? AND week_key = ?
                """,
                (learner_id, partner, template["key"], week_key),
            ).fetchone()
            return self._friend_quest_from_row(conn, row, week_start, week_end)

    def claim_friend_quest_reward(self, learner_id: str, quest_id: str) -> Optional[Dict[str, Any]]:
        learner_id = normalize_learner_id(learner_id)
        week_start, week_end, _ = current_week_window()
        claimed_now = False
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM friend_quests WHERE id = ? AND learner_id = ?",
                (quest_id, learner_id),
            ).fetchone()
            if not row:
                return None
            quest = self._friend_quest_from_row(conn, row, week_start, week_end)
            if not quest["completed"]:
                return {"quest": quest, "rewardItem": None, "claimed": False, "alreadyClaimed": False}
            already_claimed = bool(row["claimed_at"])
            if not already_claimed:
                timestamp = now_iso()
                conn.execute(
                    "UPDATE friend_quests SET claimed_at = ?, updated_at = ? WHERE id = ?",
                    (timestamp, timestamp, quest_id),
                )
                self._add_reward_inventory_for_conn(
                    conn,
                    learner_id=learner_id,
                    reward_key=row["reward_key"],
                    quantity=int(row["reward_quantity"] or 1),
                    metadata={"source": "friend_quest", "questId": quest_id, "partnerLearnerId": row["partner_learner_id"]},
                )
                row = conn.execute("SELECT * FROM friend_quests WHERE id = ?", (quest_id,)).fetchone()
                quest = self._friend_quest_from_row(conn, row, week_start, week_end)
                claimed_now = True
            reward_item = conn.execute(
                "SELECT * FROM reward_inventory WHERE learner_id = ? AND reward_key = ?",
                (learner_id, row["reward_key"]),
            ).fetchone()
            result = {
                "quest": quest,
                "rewardItem": self._row_to_reward_item(reward_item) if reward_item else None,
                "claimed": True,
                "alreadyClaimed": already_claimed,
            }
        if claimed_now:
            self.refresh_achievement_awards(learner_id=learner_id)
        return result

    def reward_inventory_summary(self, learner_id: str = "local-dev") -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        return {
            "items": self.list_reward_inventory(learner_id=learner_id),
            "activeXpBoosts": self.active_xp_boosts(learner_id=learner_id),
            "catalog": list(REWARD_CATALOG.values()),
            "balances": self.reward_currency_balances(learner_id=learner_id),
        }

    def list_reward_inventory(self, learner_id: str = "local-dev") -> list[Dict[str, Any]]:
        learner_id = normalize_learner_id(learner_id)
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM reward_inventory
                WHERE learner_id = ?
                ORDER BY updated_at DESC, reward_key ASC
                """,
                (learner_id,),
            ).fetchall()
        return [self._row_to_reward_item(row) for row in rows]

    def reward_currency_balances(self, learner_id: str = "local-dev") -> list[Dict[str, Any]]:
        learner_id = normalize_learner_id(learner_id)
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT currency_key, COALESCE(SUM(amount), 0) AS balance
                FROM reward_currency_events
                WHERE learner_id = ?
                GROUP BY currency_key
                ORDER BY currency_key ASC
                """,
                (learner_id,),
            ).fetchall()
        balances = [{"currencyKey": row["currency_key"], "balance": int(row["balance"] or 0)} for row in rows]
        if not any(item["currencyKey"] == "gems" for item in balances):
            balances.append({"currencyKey": "gems", "balance": 0})
        return balances

    def reward_currency_balance(self, learner_id: str, currency_key: str) -> int:
        learner_id = normalize_learner_id(learner_id)
        key = (currency_key or "gems").strip().lower()[:40] or "gems"
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(amount), 0) AS balance
                FROM reward_currency_events
                WHERE learner_id = ? AND currency_key = ?
                """,
                (learner_id, key),
            ).fetchone()
        return int(row["balance"] or 0)

    def reward_shop(self, learner_id: str = "local-dev") -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        balances = self.reward_currency_balances(learner_id=learner_id)
        balances_by_key = {item["currencyKey"]: item["balance"] for item in balances}
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM reward_shop_items
                ORDER BY sort_order ASC, reward_key ASC
                """
            ).fetchall()
            items = [self._row_to_reward_shop_item(conn, row, learner_id, balances_by_key) for row in rows]
        return {"items": items, "balances": balances}

    def list_admin_reward_shop_items(self) -> Dict[str, Any]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM reward_shop_items
                ORDER BY sort_order ASC, reward_key ASC
                """
            ).fetchall()
        return {"items": [self._row_to_reward_shop_policy(row) for row in rows], "count": len(rows), "catalog": list(REWARD_CATALOG.values())}

    def upsert_reward_shop_item(
        self,
        reward_key: str,
        price_currency: Optional[str] = None,
        price_amount: Optional[int] = None,
        available: Optional[bool] = None,
        daily_purchase_limit: Optional[int] = None,
        inventory_limit: Optional[int] = None,
        starts_at: Optional[str] = None,
        ends_at: Optional[str] = None,
        sort_order: Optional[int] = None,
        updated_by: str = "admin",
    ) -> Dict[str, Any]:
        key = (reward_key or "").strip()
        if key not in REWARD_CATALOG:
            raise ValueError("Unknown reward key")
        currency = (price_currency or "gems").strip().lower()[:40] or "gems"
        price = 0 if price_amount is None else max(0, int(price_amount))
        daily_limit = None if daily_purchase_limit is None else max(0, int(daily_purchase_limit))
        inventory_cap = None if inventory_limit is None else max(0, int(inventory_limit))
        order = 100 if sort_order is None else int(sort_order)
        normalized_starts_at = starts_at.strip() if starts_at and starts_at.strip() else None
        normalized_ends_at = ends_at.strip() if ends_at and ends_at.strip() else None
        if normalized_starts_at and parse_iso(normalized_starts_at) is None:
            raise ValueError("startsAt must be an ISO timestamp")
        if normalized_ends_at and parse_iso(normalized_ends_at) is None:
            raise ValueError("endsAt must be an ISO timestamp")
        timestamp = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO reward_shop_items
                (reward_key, price_currency, price_amount, available, daily_purchase_limit, inventory_limit,
                 starts_at, ends_at, sort_order, created_at, updated_at, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(reward_key)
                DO UPDATE SET
                  price_currency = excluded.price_currency,
                  price_amount = excluded.price_amount,
                  available = excluded.available,
                  daily_purchase_limit = excluded.daily_purchase_limit,
                  inventory_limit = excluded.inventory_limit,
                  starts_at = excluded.starts_at,
                  ends_at = excluded.ends_at,
                  sort_order = excluded.sort_order,
                  updated_at = excluded.updated_at,
                  updated_by = excluded.updated_by
                """,
                (
                    key,
                    currency,
                    price,
                    int(bool(available) if available is not None else True),
                    daily_limit,
                    inventory_cap,
                    normalized_starts_at,
                    normalized_ends_at,
                    order,
                    timestamp,
                    timestamp,
                    updated_by[:120],
                ),
            )
            row = conn.execute("SELECT * FROM reward_shop_items WHERE reward_key = ?", (key,)).fetchone()
        return self._row_to_reward_shop_policy(row)

    def purchase_reward(self, learner_id: str, reward_key: str) -> Optional[Dict[str, Any]]:
        learner_id = normalize_learner_id(learner_id)
        key = (reward_key or "").strip()
        reward = REWARD_CATALOG.get(key)
        if not reward:
            return None
        timestamp = now_iso()
        with self.connect() as conn:
            shop_row = conn.execute("SELECT * FROM reward_shop_items WHERE reward_key = ?", (key,)).fetchone()
            if not shop_row:
                return None
            balances_by_key = {
                row["currency_key"]: int(row["balance"] or 0)
                for row in conn.execute(
                    """
                    SELECT currency_key, COALESCE(SUM(amount), 0) AS balance
                    FROM reward_currency_events
                    WHERE learner_id = ?
                    GROUP BY currency_key
                    """,
                    (learner_id,),
                ).fetchall()
            }
            shop_item = self._row_to_reward_shop_item(conn, shop_row, learner_id, balances_by_key, timestamp=timestamp)
            currency_key = shop_item["priceCurrency"]
            price = int(shop_item["priceAmount"])
            balance_row = conn.execute(
                """
                SELECT COALESCE(SUM(amount), 0) AS balance
                FROM reward_currency_events
                WHERE learner_id = ? AND currency_key = ?
                """,
                (learner_id, currency_key),
            ).fetchone()
            balance = int(balance_row["balance"] or 0)
            if not shop_item["active"]:
                return {"purchased": False, "reason": "reward_unavailable", "shop": self.reward_shop(learner_id=learner_id), "inventoryItem": None}
            if shop_item["remainingDailyPurchases"] is not None and int(shop_item["remainingDailyPurchases"]) <= 0:
                return {"purchased": False, "reason": "daily_purchase_limit_reached", "shop": self.reward_shop(learner_id=learner_id), "inventoryItem": None}
            if shop_item["remainingInventory"] is not None and int(shop_item["remainingInventory"]) <= 0:
                return {"purchased": False, "reason": "inventory_limit_reached", "shop": self.reward_shop(learner_id=learner_id), "inventoryItem": None}
            if balance < price:
                return {"purchased": False, "reason": "insufficient_balance", "shop": self.reward_shop(learner_id=learner_id), "inventoryItem": None}
            purchase_id = new_id("purchase")
            self._record_reward_currency_for_conn(
                conn,
                learner_id=learner_id,
                currency_key=currency_key,
                amount=-price,
                reason="reward_shop_purchase",
                source_ref=purchase_id,
                idempotency_key=f"reward_shop_purchase:{purchase_id}",
                metadata={"rewardKey": key, "priceAmount": price},
                created_at=timestamp,
            )
            conn.execute(
                """
                INSERT INTO reward_shop_purchases
                (id, learner_id, reward_key, price_currency, price_amount, day_key, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    purchase_id,
                    learner_id,
                    key,
                    currency_key,
                    price,
                    day_key_from_iso(timestamp),
                    _json({"source": "reward_shop", "rewardKey": key, "priceCurrency": currency_key, "priceAmount": price}),
                    timestamp,
                ),
            )
            self._add_reward_inventory_for_conn(
                conn,
                learner_id=learner_id,
                reward_key=key,
                quantity=1,
                metadata={"source": "reward_shop", "purchaseId": purchase_id, "priceCurrency": currency_key, "priceAmount": price},
            )
            item = conn.execute(
                "SELECT * FROM reward_inventory WHERE learner_id = ? AND reward_key = ?",
                (learner_id, key),
            ).fetchone()
        return {
            "purchased": True,
            "reason": "purchased",
            "inventoryItem": self._row_to_reward_item(item),
            "shop": self.reward_shop(learner_id=learner_id),
        }

    def activate_xp_boost(self, learner_id: str, reward_key: str) -> Optional[Dict[str, Any]]:
        learner_id = normalize_learner_id(learner_id)
        key = (reward_key or "").strip()
        reward = REWARD_CATALOG.get(key)
        if not reward or reward.get("type") != "xp_boost":
            return None
        timestamp = now_iso()
        expires_at = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=int(reward["durationSeconds"]))).isoformat(timespec="seconds").replace("+00:00", "Z")
        with self.connect() as conn:
            item = conn.execute(
                "SELECT * FROM reward_inventory WHERE learner_id = ? AND reward_key = ?",
                (learner_id, key),
            ).fetchone()
            if not item or int(item["quantity"] or 0) <= 0:
                return {"activeBoost": None, "inventory": self.reward_inventory_summary(learner_id=learner_id), "activated": False}
            conn.execute(
                """
                UPDATE reward_inventory
                SET quantity = quantity - 1, updated_at = ?
                WHERE learner_id = ? AND reward_key = ? AND quantity > 0
                """,
                (timestamp, learner_id, key),
            )
            boost = {
                "id": new_id("boost"),
                "learnerId": learner_id,
                "rewardKey": key,
                "multiplier": float(reward["multiplier"]),
                "startedAt": timestamp,
                "expiresAt": expires_at,
                "source": "reward_inventory",
                "metadata": {"rewardTitle": reward["title"]},
            }
            conn.execute(
                """
                INSERT INTO xp_boosts
                (id, learner_id, reward_key, multiplier, started_at, expires_at, source, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    boost["id"],
                    learner_id,
                    key,
                    boost["multiplier"],
                    timestamp,
                    expires_at,
                    boost["source"],
                    _json(boost["metadata"]),
                ),
            )
        self.flag_xp_anomalies(learner_id=learner_id, day_key=today_key())
        return {"activeBoost": boost, "inventory": self.reward_inventory_summary(learner_id=learner_id), "activated": True}

    def active_xp_boosts(self, learner_id: str = "local-dev") -> list[Dict[str, Any]]:
        learner_id = normalize_learner_id(learner_id)
        timestamp = now_iso()
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM xp_boosts
                WHERE learner_id = ? AND expires_at > ?
                ORDER BY multiplier DESC, expires_at ASC
                """,
                (learner_id, timestamp),
            ).fetchall()
        return [self._row_to_xp_boost(row) for row in rows]

    def _active_xp_boost_for_conn(self, conn: sqlite3.Connection, learner_id: str, timestamp: str) -> Optional[Dict[str, Any]]:
        row = conn.execute(
            """
            SELECT *
            FROM xp_boosts
            WHERE learner_id = ? AND expires_at > ?
            ORDER BY multiplier DESC, expires_at ASC
            LIMIT 1
            """,
            (learner_id, timestamp),
        ).fetchone()
        return self._row_to_xp_boost(row) if row else None

    def _record_reward_currency_for_conn(
        self,
        conn: sqlite3.Connection,
        learner_id: str,
        currency_key: str,
        amount: int,
        reason: str,
        source_ref: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
    ) -> None:
        if int(amount) == 0:
            return
        key = (currency_key or "gems").strip().lower()[:40] or "gems"
        timestamp = created_at or now_iso()
        conn.execute(
            """
            INSERT OR IGNORE INTO reward_currency_events
            (id, learner_id, currency_key, amount, reason, source_ref, idempotency_key, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("currency"),
                learner_id,
                key,
                int(amount),
                (reason or "manual").strip()[:80] or "manual",
                source_ref,
                idempotency_key,
                _json(metadata or {}),
                timestamp,
            ),
        )

    def _add_reward_inventory_for_conn(
        self,
        conn: sqlite3.Connection,
        learner_id: str,
        reward_key: str,
        quantity: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        reward = REWARD_CATALOG.get(reward_key)
        if not reward:
            return
        timestamp = now_iso()
        conn.execute(
            """
            INSERT INTO reward_inventory
            (id, learner_id, reward_key, reward_type, quantity, metadata_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(learner_id, reward_key)
            DO UPDATE SET
              quantity = reward_inventory.quantity + excluded.quantity,
              metadata_json = excluded.metadata_json,
              updated_at = excluded.updated_at
            """,
            (
                new_id("reward"),
                learner_id,
                reward_key,
                reward["type"],
                max(0, int(quantity)),
                _json(metadata or {}),
                timestamp,
                timestamp,
            ),
        )

    def _friend_quest_from_row(
        self,
        conn: sqlite3.Connection,
        row: sqlite3.Row,
        week_start: str,
        week_end: str,
    ) -> Dict[str, Any]:
        learner_xp = self._weekly_xp_for_learner_conn(conn, row["learner_id"], week_start, week_end)
        partner_xp = self._weekly_xp_for_learner_conn(conn, row["partner_learner_id"], week_start, week_end)
        combined_xp = learner_xp + partner_xp
        target = int(row["target_xp"] or 1)
        reward = dict(REWARD_CATALOG.get(row["reward_key"], {"key": row["reward_key"], "type": "unknown", "title": row["reward_key"]}))
        reward["quantity"] = int(row["reward_quantity"] or 1)
        completed = combined_xp >= target
        claimed = bool(row["claimed_at"])
        return {
            "id": row["id"],
            "key": row["quest_key"],
            "title": next((item["title"] for item in FRIEND_QUEST_TEMPLATES if item["key"] == row["quest_key"]), row["quest_key"]),
            "learnerId": row["learner_id"],
            "partnerLearnerId": row["partner_learner_id"],
            "weekKey": row["week_key"],
            "weekStart": week_start,
            "weekEnd": week_end,
            "targetXp": target,
            "learnerXp": learner_xp,
            "partnerXp": partner_xp,
            "combinedXp": combined_xp,
            "progress": min(combined_xp, target),
            "progressRatio": round(clamp_float(combined_xp / max(1, target), 0.0, 1.0), 3),
            "completed": completed,
            "claimed": claimed,
            "claimedAt": row["claimed_at"],
            "reward": reward,
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }

    def _weekly_xp_for_learner_conn(self, conn: sqlite3.Connection, learner_id: str, week_start: str, week_end: str) -> int:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(points), 0) AS xp
            FROM xp_events
            WHERE learner_id = ? AND day_key >= ? AND day_key < ?
            """,
            (learner_id, week_start, week_end),
        ).fetchone()
        return int(row["xp"] or 0)

    def weekly_leaderboard(self, learner_id: str = "local-dev", limit: int = 20) -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        today = dt.datetime.now(dt.timezone.utc).date()
        week_start = today - dt.timedelta(days=today.weekday())
        week_end = week_start + dt.timedelta(days=7)
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT learner_id, COALESCE(SUM(points), 0) AS xp, COUNT(*) AS event_count
                FROM xp_events
                WHERE day_key >= ? AND day_key < ?
                GROUP BY learner_id
                ORDER BY xp DESC, learner_id ASC
                LIMIT ?
                """,
                (week_start.isoformat(), week_end.isoformat(), max(1, min(100, int(limit)))),
            ).fetchall()
            rank_rows = conn.execute(
                """
                SELECT learner_id, COALESCE(SUM(points), 0) AS xp
                FROM xp_events
                WHERE day_key >= ? AND day_key < ?
                GROUP BY learner_id
                ORDER BY xp DESC, learner_id ASC
                """,
                (week_start.isoformat(), week_end.isoformat()),
            ).fetchall()
            exclusion_rows = conn.execute(
                """
                SELECT learner_id, GROUP_CONCAT(reason) AS reasons, COUNT(*) AS flag_count
                FROM xp_abuse_flags
                WHERE day_key >= ? AND day_key < ?
                  AND status IN ('open', 'reviewing')
                  AND severity IN ('block', 'critical')
                GROUP BY learner_id
                """,
                (week_start.isoformat(), week_end.isoformat()),
            ).fetchall()
        exclusions = {
            row["learner_id"]: {
                "reasons": [reason for reason in (row["reasons"] or "").split(",") if reason],
                "flagCount": int(row["flag_count"] or 0),
            }
            for row in exclusion_rows
        }
        entries = [
            {
                "rank": index + 1,
                "learnerId": row["learner_id"],
                "xp": int(row["xp"] or 0),
                "eventCount": int(row["event_count"] or 0),
                "isCurrentLearner": row["learner_id"] == learner_id,
                "leaderboardExcluded": row["learner_id"] in exclusions,
                "exclusionReasons": exclusions.get(row["learner_id"], {}).get("reasons", []),
            }
            for index, row in enumerate(rows)
        ]
        current_rank = None
        eligible_rank = 0
        for index, row in enumerate(rank_rows):
            if row["learner_id"] in exclusions:
                if row["learner_id"] == learner_id:
                    current_rank = None
                    break
                continue
            eligible_rank += 1
            if row["learner_id"] == learner_id:
                current_rank = eligible_rank
                break
        return {
            "weekStart": week_start.isoformat(),
            "weekEnd": week_end.isoformat(),
            "entries": entries,
            "currentLearnerRank": current_rank,
            "excludedLearnerCount": len(exclusions),
        }

    def league_status(self, learner_id: str = "local-dev") -> Dict[str, Any]:
        xp = self.xp_summary(learner_id=learner_id)
        week_xp = int(xp["weekXp"])
        current = LEAGUE_TIERS[0]
        for tier in LEAGUE_TIERS:
            if week_xp >= tier["minWeeklyXp"]:
                current = tier
        next_tier = next((tier for tier in LEAGUE_TIERS if tier["key"] == current.get("nextKey")), None)
        progress_to_next = None
        if next_tier:
            span = max(1, int(next_tier["minWeeklyXp"]) - int(current["minWeeklyXp"]))
            progress_to_next = clamp_float((week_xp - int(current["minWeeklyXp"])) / span, 0.0, 1.0)
        leaderboard = self.weekly_leaderboard(learner_id=learner_id, limit=50)
        return {
            "currentTier": {key: current[key] for key in ["key", "name", "minWeeklyXp"]},
            "nextTier": {key: next_tier[key] for key in ["key", "name", "minWeeklyXp"]} if next_tier else None,
            "weekXp": week_xp,
            "progressToNextTier": round(progress_to_next, 3) if progress_to_next is not None else None,
            "currentRank": leaderboard["currentLearnerRank"],
            "weekStart": xp["weekStart"],
        }

    def refresh_achievement_awards(self, learner_id: str = "local-dev") -> list[Dict[str, Any]]:
        learner_id = normalize_learner_id(learner_id)
        awarded: list[Dict[str, Any]] = []
        existing_keys = {
            (award["achievementKey"], int(award["level"]))
            for award in self.list_achievement_awards(learner_id=learner_id)
        }
        for achievement in self.achievement_progress(learner_id=learner_id):
            key = (achievement["key"], int(achievement["level"]))
            if achievement["completed"] and key not in existing_keys:
                award = self._award_achievement(
                    learner_id=learner_id,
                    achievement_key=achievement["key"],
                    level=achievement["level"],
                    payload={
                        "title": achievement["title"],
                        "target": achievement["target"],
                        "progress": achievement["rawProgress"],
                        "rewardGems": achievement["rewardGems"],
                    },
                )
                awarded.append(award)
                reward_gems = int(achievement.get("rewardGems") or 0)
                if reward_gems > 0:
                    with self.connect() as conn:
                        self._record_reward_currency_for_conn(
                            conn,
                            learner_id=learner_id,
                            currency_key="gems",
                            amount=reward_gems,
                            reason="achievement_award",
                            source_ref=f"achievement:{achievement['key']}:{achievement['level']}",
                            idempotency_key=f"achievement_gems:{learner_id}:{achievement['key']}:{achievement['level']}",
                            metadata={
                                "achievementKey": achievement["key"],
                                "level": achievement["level"],
                                "title": achievement["title"],
                            },
                        )
                existing_keys.add(key)
        return awarded

    def achievements_summary(self, learner_id: str = "local-dev") -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        progress = self.achievement_progress(learner_id=learner_id)
        awards_by_key = {
            (award["achievementKey"], int(award["level"])): award
            for award in self.list_achievement_awards(learner_id=learner_id)
        }
        achievements = []
        for item in progress:
            award = awards_by_key.get((item["key"], int(item["level"])))
            updated = dict(item)
            updated["awarded"] = bool(award)
            updated["awardedAt"] = award["awardedAt"] if award else None
            achievements.append(updated)
        completed_tracks = {
            item["key"]
            for item in achievements
            if int(item["level"]) == int(item["maxLevel"]) and item["completed"]
        }
        return {
            "awardedCount": sum(1 for item in achievements if item["awarded"]),
            "totalCount": len(achievements),
            "trackCount": len({item["key"] for item in achievements}),
            "completedTrackCount": len(completed_tracks),
            "achievements": achievements,
        }

    def achievement_progress(self, learner_id: str = "local-dev") -> list[Dict[str, Any]]:
        learner_id = normalize_learner_id(learner_id)
        xp = self.xp_summary(learner_id=learner_id)
        streak = self.streak_summary(learner_id=learner_id)
        quests = self.daily_quests(learner_id=learner_id)
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT source, COUNT(*) AS count
                FROM xp_events
                WHERE learner_id = ?
                GROUP BY source
                """,
                (learner_id,),
            ).fetchall()
            friend_count_row = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM friend_relationships
                WHERE status = 'active' AND (learner_a_id = ? OR learner_b_id = ?)
                """,
                (learner_id, learner_id),
            ).fetchone()
            friend_quest_claim_count_row = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM friend_quests
                WHERE learner_id = ? AND claimed_at IS NOT NULL
                """,
                (learner_id,),
            ).fetchone()
        counts_by_source = {row["source"]: int(row["count"] or 0) for row in rows}
        completed_quest_count = sum(1 for quest in quests if quest["completed"])
        friend_count = int(friend_count_row["count"] or 0)
        friend_quest_claim_count = int(friend_quest_claim_count_row["count"] or 0)
        progress_items = []
        for achievement in ACHIEVEMENTS:
            metric = achievement["metric"]
            if metric == "source_count":
                raw_progress = counts_by_source.get(achievement["source"], 0)
            elif metric == "total_xp":
                raw_progress = int(xp["totalXp"])
            elif metric == "quest_count":
                raw_progress = completed_quest_count
            elif metric == "streak_days":
                raw_progress = int(streak["currentStreak"])
            elif metric == "friend_count":
                raw_progress = friend_count
            elif metric == "friend_quest_claim_count":
                raw_progress = friend_quest_claim_count
            else:
                raw_progress = 0
            progress_items.append(
                {
                    "key": achievement["key"],
                    "title": achievement["title"],
                    "description": achievement["description"],
                    "level": achievement["level"],
                    "maxLevel": ACHIEVEMENT_MAX_LEVELS.get(achievement["key"], achievement["level"]),
                    "metric": metric,
                    "source": achievement["source"],
                    "target": achievement["target"],
                    "progress": min(raw_progress, achievement["target"]),
                    "rawProgress": raw_progress,
                    "completed": raw_progress >= achievement["target"],
                    "rewardGems": int(achievement.get("rewardGems") or 0),
                }
            )
        return progress_items

    def _award_achievement(
        self,
        learner_id: str,
        achievement_key: str,
        level: int,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        award = {
            "id": new_id("ach"),
            "learnerId": learner_id,
            "achievementKey": achievement_key,
            "level": int(level),
            "awardedAt": now_iso(),
            "payload": payload or {},
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO achievement_awards
                (id, learner_id, achievement_key, level, awarded_at, payload_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    award["id"],
                    learner_id,
                    achievement_key,
                    award["level"],
                    award["awardedAt"],
                    _json(award["payload"]),
                ),
            )
        return award

    def list_achievement_awards(self, learner_id: str = "local-dev") -> list[Dict[str, Any]]:
        learner_id = normalize_learner_id(learner_id)
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM achievement_awards
                WHERE learner_id = ?
                ORDER BY awarded_at DESC, achievement_key ASC
                """,
                (learner_id,),
            ).fetchall()
        return [self._row_to_achievement_award(row) for row in rows]

    def flag_xp_anomalies(self, learner_id: str = "local-dev", day_key: Optional[str] = None) -> list[Dict[str, Any]]:
        learner_id = normalize_learner_id(learner_id)
        day = day_key or today_key()
        with self.connect() as conn:
            totals = conn.execute(
                """
                SELECT COALESCE(SUM(points), 0) AS total_xp, COUNT(*) AS event_count, COUNT(DISTINCT source) AS source_count
                FROM xp_events
                WHERE learner_id = ? AND day_key = ?
                """,
                (learner_id, day),
            ).fetchone()
            source_rows = conn.execute(
                """
                SELECT source, COALESCE(SUM(points), 0) AS source_xp, COUNT(*) AS source_events
                FROM xp_events
                WHERE learner_id = ? AND day_key = ?
                GROUP BY source
                ORDER BY source_events DESC, source_xp DESC
                """,
                (learner_id, day),
            ).fetchall()
            event_rows = conn.execute(
                """
                SELECT *
                FROM xp_events
                WHERE learner_id = ? AND day_key = ?
                ORDER BY created_at ASC
                """,
                (learner_id, day),
            ).fetchall()
            day_start = f"{day}T00:00:00Z"
            day_end = (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat() + "T00:00:00Z"
            boost_activation_row = conn.execute(
                """
                SELECT COUNT(*) AS activation_count, GROUP_CONCAT(id) AS boost_ids
                FROM xp_boosts
                WHERE learner_id = ? AND started_at >= ? AND started_at < ?
                """,
                (learner_id, day_start, day_end),
            ).fetchone()
        total_xp = int(totals["total_xp"] or 0)
        event_count = int(totals["event_count"] or 0)
        limit = xp_daily_soft_limit()
        events = [self._row_to_xp_event(row) for row in event_rows]
        flags: list[Dict[str, Any]] = []
        if total_xp > limit:
            flags.append(
                self._upsert_xp_abuse_flag(
                    learner_id=learner_id,
                    day_key=day,
                    reason="daily_xp_soft_limit_exceeded",
                    severity="review",
                    evidence={
                        "totalXp": total_xp,
                        "softLimit": limit,
                        "eventCount": int(totals["event_count"] or 0),
                        "sourceCount": int(totals["source_count"] or 0),
                        },
                    )
                )
        boosted_events = []
        boosted_bonus_total = 0
        for event in events:
            payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
            boost_payload = payload.get("xpBoostApplied") if isinstance(payload, dict) else None
            if isinstance(boost_payload, dict):
                boosted_events.append(event)
                boosted_bonus_total += int(boost_payload.get("bonusPoints") or 0)
        boosted_xp_total = sum(int(event["points"]) for event in boosted_events)
        boosted_limit = xp_boosted_daily_soft_limit()
        if boosted_xp_total > boosted_limit:
            flags.append(
                self._upsert_xp_abuse_flag(
                    learner_id=learner_id,
                    day_key=day,
                    reason="boosted_xp_soft_limit_exceeded",
                    severity="block",
                    evidence={
                        "boostedXp": boosted_xp_total,
                        "boostBonusXp": boosted_bonus_total,
                        "boostedEventCount": len(boosted_events),
                        "boostedSoftLimit": boosted_limit,
                        "eventIds": [event["id"] for event in boosted_events[:20]],
                    },
                )
            )
        payload_buckets: Dict[str, Dict[str, Any]] = {}
        for event in events:
            fingerprint = _json({"source": event["source"], "payload": event.get("payload") or {}})
            bucket = payload_buckets.setdefault(
                fingerprint,
                {"source": event["source"], "count": 0, "xp": 0, "eventIds": []},
            )
            bucket["count"] += 1
            bucket["xp"] += int(event["points"])
            if len(bucket["eventIds"]) < 20:
                bucket["eventIds"].append(event["id"])
        duplicate_payload_limit = xp_duplicate_payload_soft_limit()
        repeated_payloads = [
            bucket
            for bucket in payload_buckets.values()
            if int(bucket["count"]) >= duplicate_payload_limit and int(bucket["xp"]) >= 80
        ]
        if repeated_payloads:
            worst = max(repeated_payloads, key=lambda item: (int(item["count"]), int(item["xp"])))
            flags.append(
                self._upsert_xp_abuse_flag(
                    learner_id=learner_id,
                    day_key=day,
                    reason="duplicate_payload_xp_burst",
                    severity="block",
                    evidence={
                        "source": worst["source"],
                        "duplicatePayloadEvents": int(worst["count"]),
                        "duplicatePayloadXp": int(worst["xp"]),
                        "duplicatePayloadSoftLimit": duplicate_payload_limit,
                        "eventIds": worst["eventIds"],
                    },
                )
            )
        boost_activation_count = int(boost_activation_row["activation_count"] or 0) if boost_activation_row else 0
        boost_activation_limit = xp_daily_boost_activation_soft_limit()
        if boost_activation_count > boost_activation_limit:
            flags.append(
                self._upsert_xp_abuse_flag(
                    learner_id=learner_id,
                    day_key=day,
                    reason="daily_boost_activation_soft_limit_exceeded",
                    severity="review",
                    evidence={
                        "boostActivationCount": boost_activation_count,
                        "boostActivationSoftLimit": boost_activation_limit,
                        "boostIds": (boost_activation_row["boost_ids"] or "").split(",")[:20] if boost_activation_row else [],
                    },
                )
            )
        event_limit = int(os.environ.get("AI_LANGUAGE_PARTNER_XP_DAILY_EVENT_SOFT_LIMIT", "120"))
        if event_count > event_limit:
            flags.append(
                self._upsert_xp_abuse_flag(
                    learner_id=learner_id,
                    day_key=day,
                    reason="daily_xp_event_count_soft_limit_exceeded",
                    severity="review",
                    evidence={"eventCount": event_count, "eventSoftLimit": event_limit, "totalXp": total_xp},
                )
            )
        if source_rows:
            top_source = source_rows[0]
            top_source_events = int(top_source["source_events"] or 0)
            top_source_xp = int(top_source["source_xp"] or 0)
            if event_count >= 15 and top_source_events / max(1, event_count) >= 0.9 and top_source_xp >= 150:
                flags.append(
                    self._upsert_xp_abuse_flag(
                        learner_id=learner_id,
                        day_key=day,
                        reason="single_source_xp_concentration",
                        severity="review",
                        evidence={
                            "source": top_source["source"],
                            "sourceEvents": top_source_events,
                            "eventCount": event_count,
                            "sourceXp": top_source_xp,
                            "totalXp": total_xp,
                        },
                    )
                )
        return flags

    def _upsert_xp_abuse_flag(
        self,
        learner_id: str,
        day_key: str,
        reason: str,
        severity: str,
        evidence: Dict[str, Any],
    ) -> Dict[str, Any]:
        timestamp = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO xp_abuse_flags
                (id, learner_id, day_key, reason, severity, evidence_json, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'open')
                ON CONFLICT(learner_id, day_key, reason)
                DO UPDATE SET
                  severity = excluded.severity,
                  evidence_json = excluded.evidence_json,
                  created_at = excluded.created_at,
                  status = CASE
                    WHEN xp_abuse_flags.status IN ('resolved', 'dismissed') THEN xp_abuse_flags.status
                    ELSE 'open'
                  END,
                  reviewed_by = CASE
                    WHEN xp_abuse_flags.status IN ('resolved', 'dismissed') THEN xp_abuse_flags.reviewed_by
                    ELSE NULL
                  END,
                  resolution_note = CASE
                    WHEN xp_abuse_flags.status IN ('resolved', 'dismissed') THEN xp_abuse_flags.resolution_note
                    ELSE NULL
                  END,
                  resolved_at = CASE
                    WHEN xp_abuse_flags.status IN ('resolved', 'dismissed') THEN xp_abuse_flags.resolved_at
                    ELSE NULL
                  END
                """,
                (new_id("xpflag"), learner_id, day_key, reason, severity, _json(evidence), timestamp),
            )
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM xp_abuse_flags
                WHERE learner_id = ? AND day_key = ? AND reason = ?
                """,
                (learner_id, day_key, reason),
            ).fetchone()
        return self._row_to_xp_abuse_flag(row)

    def list_xp_abuse_flags(
        self,
        learner_id: Optional[str] = "local-dev",
        status: Optional[str] = None,
        limit: int = 20,
    ) -> list[Dict[str, Any]]:
        normalized_learner = normalize_learner_id(learner_id) if learner_id is not None else None
        normalized_status = (status or "").strip().lower() or None
        where = []
        params: list[Any] = []
        if normalized_learner:
            where.append("learner_id = ?")
            params.append(normalized_learner)
        if normalized_status:
            where.append("status = ?")
            params.append(normalized_status)
        where_sql = "WHERE " + " AND ".join(where) if where else ""
        params.append(max(1, min(200, int(limit))))
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT *
                FROM xp_abuse_flags
                {where_sql}
                ORDER BY created_at DESC, day_key DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._row_to_xp_abuse_flag(row) for row in rows]

    def review_xp_abuse_flag(
        self,
        flag_id: str,
        status: str,
        reviewer: str,
        note: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        normalized_status = (status or "").strip().lower()
        if normalized_status not in {"open", "reviewing", "resolved", "dismissed"}:
            raise ValueError("invalid_xp_abuse_flag_status")
        reviewer_label = (reviewer or "admin").strip()[:120] or "admin"
        resolution_note = (note or "").strip()[:1000] or None
        resolved_at = now_iso() if normalized_status in {"resolved", "dismissed"} else None
        with self.connect() as conn:
            updated = conn.execute(
                """
                UPDATE xp_abuse_flags
                SET status = ?,
                    reviewed_by = ?,
                    resolution_note = ?,
                    resolved_at = ?
                WHERE id = ?
                """,
                (normalized_status, reviewer_label, resolution_note, resolved_at, flag_id),
            ).rowcount
            if not updated:
                return None
            row = conn.execute("SELECT * FROM xp_abuse_flags WHERE id = ?", (flag_id,)).fetchone()
        return self._row_to_xp_abuse_flag(row) if row else None

    def learner_reputation_profile(self, learner_id: str = "local-dev") -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        week_start, week_end, _ = current_week_window()
        with self.connect() as conn:
            xp_row = conn.execute(
                """
                SELECT
                  COALESCE(SUM(points), 0) AS week_xp,
                  COUNT(*) AS week_event_count,
                  COUNT(DISTINCT source) AS week_source_count,
                  MAX(created_at) AS latest_xp_at
                FROM xp_events
                WHERE learner_id = ? AND day_key >= ? AND day_key < ?
                """,
                (learner_id, week_start, week_end),
            ).fetchone()
            flag_rows = conn.execute(
                """
                SELECT *
                FROM xp_abuse_flags
                WHERE learner_id = ?
                ORDER BY created_at DESC, day_key DESC
                LIMIT 50
                """,
                (learner_id,),
            ).fetchall()
            social_row = conn.execute(
                """
                SELECT
                  SUM(CASE WHEN blocked_learner_id = ? THEN 1 ELSE 0 END) AS incoming_blocks,
                  SUM(CASE WHEN blocker_learner_id = ? THEN 1 ELSE 0 END) AS outgoing_blocks,
                  MAX(created_at) AS latest_block_at
                FROM social_blocks
                WHERE blocked_learner_id = ? OR blocker_learner_id = ?
                """,
                (learner_id, learner_id, learner_id, learner_id),
            ).fetchone()
            account_row = conn.execute("SELECT * FROM accounts WHERE learner_id = ?", (learner_id,)).fetchone()
            device_row = None
            session_row = None
            if account_row:
                device_row = conn.execute(
                    """
                    SELECT
                      COUNT(*) AS device_count,
                      SUM(CASE WHEN trust_status = 'trusted' AND revoked_at IS NULL THEN 1 ELSE 0 END) AS trusted_devices,
                      SUM(CASE WHEN trust_status = 'untrusted' AND revoked_at IS NULL THEN 1 ELSE 0 END) AS untrusted_devices,
                      SUM(CASE WHEN revoked_at IS NOT NULL THEN 1 ELSE 0 END) AS revoked_devices,
                      MAX(updated_at) AS latest_device_at
                    FROM account_devices
                    WHERE account_id = ?
                    """,
                    (account_row["id"],),
                ).fetchone()
                session_row = conn.execute(
                    """
                    SELECT COUNT(*) AS active_sessions, MAX(last_used_at) AS latest_session_at
                    FROM account_sessions
                    WHERE account_id = ? AND revoked_at IS NULL
                    """,
                    (account_row["id"],),
                ).fetchone()

        flags = [self._row_to_xp_abuse_flag(row) for row in flag_rows]
        open_flags = [flag for flag in flags if flag["status"] in {"open", "reviewing"}]
        blocking_flags = [flag for flag in open_flags if flag["leaderboardExcluded"]]
        incoming_blocks = int((social_row["incoming_blocks"] if social_row else 0) or 0)
        outgoing_blocks = int((social_row["outgoing_blocks"] if social_row else 0) or 0)
        device_count = int((device_row["device_count"] if device_row else 0) or 0)
        trusted_devices = int((device_row["trusted_devices"] if device_row else 0) or 0)
        untrusted_devices = int((device_row["untrusted_devices"] if device_row else 0) or 0)
        revoked_devices = int((device_row["revoked_devices"] if device_row else 0) or 0)
        active_sessions = int((session_row["active_sessions"] if session_row else 0) or 0)
        week_xp = int(xp_row["week_xp"] or 0) if xp_row else 0
        week_event_count = int(xp_row["week_event_count"] or 0) if xp_row else 0
        week_source_count = int(xp_row["week_source_count"] or 0) if xp_row else 0

        signals: list[Dict[str, Any]] = []

        def add_signal(key: str, label: str, severity: str, weight: int, evidence: Dict[str, Any]) -> None:
            signals.append(
                {
                    "key": key,
                    "label": label,
                    "severity": severity,
                    "weight": int(weight),
                    "evidence": evidence,
                }
            )

        severity_weight = {"critical": 45, "block": 35, "review": 20, "info": 8}
        for flag in open_flags:
            weight = severity_weight.get(flag["severity"], 12)
            add_signal(
                f"xp_abuse:{flag['reason']}",
                f"Open XP abuse flag: {flag['reason']}",
                "high" if flag["leaderboardExcluded"] else "medium",
                weight,
                {
                    "flagId": flag["id"],
                    "status": flag["status"],
                    "flagSeverity": flag["severity"],
                    "dayKey": flag["dayKey"],
                    "leaderboardExcluded": flag["leaderboardExcluded"],
                    "evidence": flag["evidence"],
                },
            )
        duplicate_flags = [flag for flag in open_flags if flag["reason"] == "duplicate_payload_xp_burst"]
        if duplicate_flags:
            add_signal(
                "automation:duplicate_payload_cluster",
                "Repeated XP payload pattern suggests automation",
                "high",
                20,
                {"flagCount": len(duplicate_flags), "flagIds": [flag["id"] for flag in duplicate_flags[:10]]},
            )
        if incoming_blocks:
            add_signal(
                "social:incoming_blocks",
                "Other learners have blocked this learner",
                "high" if incoming_blocks >= 3 else "medium",
                min(30, incoming_blocks * 10),
                {"incomingBlockCount": incoming_blocks},
            )
        if outgoing_blocks >= 5:
            add_signal(
                "social:high_outgoing_blocks",
                "Learner has blocked many other learners",
                "low",
                min(12, outgoing_blocks * 2),
                {"outgoingBlockCount": outgoing_blocks},
            )
        if week_event_count > 120:
            add_signal(
                "xp:high_weekly_event_volume",
                "Weekly XP event volume is unusually high",
                "medium",
                18,
                {"weekEventCount": week_event_count, "weekXp": week_xp, "weekSourceCount": week_source_count},
            )
        if week_xp > 1000:
            add_signal(
                "xp:high_weekly_xp_volume",
                "Weekly XP volume is unusually high",
                "medium",
                18,
                {"weekXp": week_xp, "weekEventCount": week_event_count},
            )
        if revoked_devices:
            add_signal(
                "device:revoked_devices",
                "Account has revoked devices",
                "medium",
                min(30, revoked_devices * 15),
                {"revokedDeviceCount": revoked_devices, "deviceCount": device_count},
            )
        if untrusted_devices >= 3:
            add_signal(
                "device:many_untrusted_devices",
                "Account has several untrusted active devices",
                "low",
                min(15, (untrusted_devices - 2) * 5),
                {"untrustedDeviceCount": untrusted_devices, "trustedDeviceCount": trusted_devices},
            )
        if active_sessions > 5:
            add_signal(
                "session:many_active_sessions",
                "Account has many active sessions",
                "low",
                8,
                {"activeSessionCount": active_sessions},
            )

        signals.sort(key=lambda item: (-int(item["weight"]), item["key"]))
        risk_score = min(100, sum(int(item["weight"]) for item in signals))
        if risk_score >= 70:
            risk_band = "critical"
        elif risk_score >= 45:
            risk_band = "high"
        elif risk_score >= 20:
            risk_band = "medium"
        elif risk_score > 0:
            risk_band = "low"
        else:
            risk_band = "trusted"
        latest_values = [
            xp_row["latest_xp_at"] if xp_row else None,
            social_row["latest_block_at"] if social_row else None,
            device_row["latest_device_at"] if device_row else None,
            session_row["latest_session_at"] if session_row else None,
            *(flag["createdAt"] for flag in flags),
        ]
        latest_signal_at = max((value for value in latest_values if value), default=None)
        return {
            "learnerId": learner_id,
            "riskScore": risk_score,
            "riskBand": risk_band,
            "reviewRecommended": risk_band in {"high", "critical"} or bool(open_flags) or incoming_blocks >= 2,
            "leaderboardEligible": not any(flag["leaderboardExcluded"] for flag in open_flags),
            "latestSignalAt": latest_signal_at,
            "signals": signals,
            "summary": {
                "openXpAbuseFlagCount": len(open_flags),
                "blockingXpAbuseFlagCount": len(blocking_flags),
                "resolvedOrDismissedXpAbuseFlagCount": len([flag for flag in flags if flag["status"] in {"resolved", "dismissed"}]),
                "incomingBlockCount": incoming_blocks,
                "outgoingBlockCount": outgoing_blocks,
                "weekXp": week_xp,
                "weekEventCount": week_event_count,
                "weekSourceCount": week_source_count,
                "deviceCount": device_count,
                "trustedDeviceCount": trusted_devices,
                "untrustedDeviceCount": untrusted_devices,
                "revokedDeviceCount": revoked_devices,
                "activeSessionCount": active_sessions,
            },
            "xpAbuseFlags": flags,
        }

    def list_reputation_profiles(
        self,
        band: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        normalized_band = (band or "").strip().lower() or None
        if normalized_band and normalized_band not in {"trusted", "low", "medium", "high", "critical"}:
            raise ValueError("invalid_reputation_band")
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT learner_id FROM xp_events
                UNION
                SELECT learner_id FROM xp_abuse_flags
                UNION
                SELECT blocker_learner_id FROM social_blocks
                UNION
                SELECT blocked_learner_id FROM social_blocks
                UNION
                SELECT id FROM learning_profiles
                UNION
                SELECT learner_id FROM accounts
                """
            ).fetchall()
        profiles = [self.learner_reputation_profile(row["learner_id"]) for row in rows]
        if normalized_band:
            profiles = [profile for profile in profiles if profile["riskBand"] == normalized_band]
        else:
            profiles = [profile for profile in profiles if profile["riskScore"] > 0 or profile["reviewRecommended"]]
        profiles.sort(key=lambda item: (-int(item["riskScore"]), item["latestSignalAt"] or "", item["learnerId"]))
        bounded_limit = max(1, min(200, int(limit)))
        return {"profiles": profiles[:bounded_limit], "count": min(len(profiles), bounded_limit)}

    def _row_to_xp_event(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "learnerId": row["learner_id"],
            "source": row["source"],
            "points": int(row["points"] or 0),
            "dayKey": row["day_key"],
            "idempotencyKey": row["idempotency_key"],
            "payload": _loads(row["payload_json"], {}),
            "createdAt": row["created_at"],
        }

    def _row_to_friend_invite(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "requesterLearnerId": row["requester_learner_id"],
            "addresseeLearnerId": row["addressee_learner_id"],
            "status": row["status"],
            "message": row["message"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
            "respondedAt": row["responded_at"],
        }

    def _row_to_friend_relationship(self, row: sqlite3.Row, learner_id: str) -> Dict[str, Any]:
        friend_id = row["learner_b_id"] if row["learner_a_id"] == learner_id else row["learner_a_id"]
        return {
            "id": row["id"],
            "learnerId": learner_id,
            "friendLearnerId": friend_id,
            "status": row["status"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
            "removedAt": row["removed_at"],
        }

    def _default_social_settings(self, learner_id: str) -> Dict[str, Any]:
        timestamp = now_iso()
        return {
            "learnerId": normalize_learner_id(learner_id),
            "discoverable": True,
            "allowFriendInvites": True,
            "showWeeklyXp": True,
            "createdAt": timestamp,
            "updatedAt": timestamp,
        }

    def _ensure_social_settings_for_conn(self, conn: sqlite3.Connection, learner_id: str) -> sqlite3.Row:
        normalized = normalize_learner_id(learner_id)
        timestamp = now_iso()
        conn.execute(
            """
            INSERT OR IGNORE INTO social_settings
            (learner_id, discoverable, allow_friend_invites, show_weekly_xp, created_at, updated_at)
            VALUES (?, 1, 1, 1, ?, ?)
            """,
            (normalized, timestamp, timestamp),
        )
        return conn.execute("SELECT * FROM social_settings WHERE learner_id = ?", (normalized,)).fetchone()

    def _row_to_social_settings(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "learnerId": row["learner_id"],
            "discoverable": bool(row["discoverable"]),
            "allowFriendInvites": bool(row["allow_friend_invites"]),
            "showWeeklyXp": bool(row["show_weekly_xp"]),
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }

    def _row_to_social_block(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "blockerLearnerId": row["blocker_learner_id"],
            "blockedLearnerId": row["blocked_learner_id"],
            "createdAt": row["created_at"],
        }

    def _row_to_reward_shop_policy(self, row: sqlite3.Row) -> Dict[str, Any]:
        reward = REWARD_CATALOG.get(row["reward_key"], {})
        return {
            "rewardKey": row["reward_key"],
            "rewardType": reward.get("type", "unknown"),
            "title": reward.get("title", row["reward_key"]),
            "description": reward.get("description"),
            "priceCurrency": row["price_currency"],
            "priceAmount": int(row["price_amount"] or 0),
            "available": bool(row["available"]),
            "dailyPurchaseLimit": int(row["daily_purchase_limit"]) if row["daily_purchase_limit"] is not None else None,
            "inventoryLimit": int(row["inventory_limit"]) if row["inventory_limit"] is not None else None,
            "startsAt": row["starts_at"],
            "endsAt": row["ends_at"],
            "sortOrder": int(row["sort_order"] or 100),
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
            "updatedBy": row["updated_by"],
        }

    def _row_to_reward_shop_item(
        self,
        conn: sqlite3.Connection,
        row: sqlite3.Row,
        learner_id: str,
        balances_by_key: Dict[str, int],
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        policy = self._row_to_reward_shop_policy(row)
        now_value = parse_iso(timestamp or now_iso()) or dt.datetime.now(dt.timezone.utc)
        starts = parse_iso(policy["startsAt"])
        ends = parse_iso(policy["endsAt"])
        active_window = (starts is None or starts <= now_value) and (ends is None or ends > now_value)
        active = bool(policy["available"]) and active_window
        today = day_key_from_iso(timestamp or now_iso())
        purchased_today = int(
            conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM reward_shop_purchases
                WHERE learner_id = ? AND reward_key = ? AND day_key = ?
                """,
                (learner_id, policy["rewardKey"], today),
            ).fetchone()["count"]
            or 0
        )
        inventory_row = conn.execute(
            "SELECT quantity FROM reward_inventory WHERE learner_id = ? AND reward_key = ?",
            (learner_id, policy["rewardKey"]),
        ).fetchone()
        current_inventory = int(inventory_row["quantity"] or 0) if inventory_row else 0
        daily_limit = policy["dailyPurchaseLimit"]
        inventory_limit = policy["inventoryLimit"]
        remaining_daily = None if daily_limit is None else max(0, int(daily_limit) - purchased_today)
        remaining_inventory = None if inventory_limit is None else max(0, int(inventory_limit) - current_inventory)
        balance = int(balances_by_key.get(policy["priceCurrency"], 0))
        price = int(policy["priceAmount"])
        can_purchase = (
            active
            and balance >= price
            and (remaining_daily is None or remaining_daily > 0)
            and (remaining_inventory is None or remaining_inventory > 0)
        )
        item = {
            **policy,
            "active": active,
            "affordable": can_purchase,
            "purchasedToday": purchased_today,
            "remainingDailyPurchases": remaining_daily,
            "currentInventoryQuantity": current_inventory,
            "remainingInventory": remaining_inventory,
        }
        return item

    def _row_to_reward_item(self, row: sqlite3.Row) -> Dict[str, Any]:
        catalog = REWARD_CATALOG.get(row["reward_key"], {})
        return {
            "id": row["id"],
            "learnerId": row["learner_id"],
            "rewardKey": row["reward_key"],
            "rewardType": row["reward_type"],
            "title": catalog.get("title", row["reward_key"]),
            "description": catalog.get("description"),
            "quantity": int(row["quantity"] or 0),
            "metadata": _loads(row["metadata_json"], {}),
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }

    def _row_to_xp_boost(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "learnerId": row["learner_id"],
            "rewardKey": row["reward_key"],
            "multiplier": float(row["multiplier"] or 1.0),
            "startedAt": row["started_at"],
            "expiresAt": row["expires_at"],
            "source": row["source"],
            "metadata": _loads(row["metadata_json"], {}),
        }

    def _row_to_achievement_award(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "learnerId": row["learner_id"],
            "achievementKey": row["achievement_key"],
            "level": int(row["level"] or 1),
            "awardedAt": row["awarded_at"],
            "payload": _loads(row["payload_json"], {}),
        }

    def _row_to_xp_abuse_flag(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "learnerId": row["learner_id"],
            "dayKey": row["day_key"],
            "reason": row["reason"],
            "severity": row["severity"],
            "status": row["status"],
            "evidence": _loads(row["evidence_json"], {}),
            "leaderboardExcluded": row["status"] in {"open", "reviewing"} and row["severity"] in {"block", "critical"},
            "reviewedBy": row["reviewed_by"],
            "resolutionNote": row["resolution_note"],
            "resolvedAt": row["resolved_at"],
            "createdAt": row["created_at"],
        }

    def audit_log(
        self,
        action: str,
        actor: Optional[str] = "anonymous",
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        entry = {
            "id": new_id("audit"),
            "action": action,
            "actor": actor,
            "targetType": target_type,
            "targetId": target_id,
            "payload": payload or {},
            "createdAt": now_iso(),
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs (id, action, actor, target_type, target_id, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry["id"],
                    entry["action"],
                    entry["actor"],
                    entry["targetType"],
                    entry["targetId"],
                    _json(entry["payload"]),
                    entry["createdAt"],
                ),
            )
        return entry

    def list_audit_logs(self, limit: int = 50) -> list[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, action, actor, target_type, target_id, payload_json, created_at
                FROM audit_logs
                ORDER BY rowid DESC
                LIMIT ?
                """,
                (max(1, min(200, int(limit))),),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "action": row["action"],
                "actor": row["actor"],
                "targetType": row["target_type"],
                "targetId": row["target_id"],
                "payload": _loads(row["payload_json"], {}),
                "createdAt": row["created_at"],
            }
            for row in rows
        ]

    def delete_learner_data(self, actor: str = "anonymous", learner_id: str = "local-dev") -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        audit_target_id = audit_subject_hash(learner_id)
        self.audit_log("privacy_deletion_requested", actor="privacy_self_service", target_type="learner", target_id=audit_target_id)
        with self.connect() as conn:
            conversation_ids = [
                row["id"] for row in conn.execute("SELECT id FROM conversations WHERE learner_id = ?", (learner_id,)).fetchall()
            ]
            placeholders = ",".join("?" for _ in conversation_ids) or "NULL"
            counts = {
                "messages": conn.execute(f"SELECT COUNT(*) AS count FROM messages WHERE conversation_id IN ({placeholders})", conversation_ids).fetchone()["count"],
                "conversations": conn.execute("SELECT COUNT(*) AS count FROM conversations WHERE learner_id = ?", (learner_id,)).fetchone()["count"],
                "reviewCards": conn.execute("SELECT COUNT(*) AS count FROM review_cards WHERE learner_id = ?", (learner_id,)).fetchone()["count"],
                "usageRecords": conn.execute("SELECT COUNT(*) AS count FROM usage_records WHERE learner_id = ?", (learner_id,)).fetchone()["count"],
                "analyticsEvents": conn.execute("SELECT COUNT(*) AS count FROM analytics_events WHERE learner_id = ?", (learner_id,)).fetchone()["count"],
                "xpEvents": conn.execute("SELECT COUNT(*) AS count FROM xp_events WHERE learner_id = ?", (learner_id,)).fetchone()["count"],
                "achievementAwards": conn.execute("SELECT COUNT(*) AS count FROM achievement_awards WHERE learner_id = ?", (learner_id,)).fetchone()["count"],
                "xpAbuseFlags": conn.execute("SELECT COUNT(*) AS count FROM xp_abuse_flags WHERE learner_id = ?", (learner_id,)).fetchone()["count"],
                "rewardInventoryItems": conn.execute("SELECT COUNT(*) AS count FROM reward_inventory WHERE learner_id = ?", (learner_id,)).fetchone()["count"],
                "xpBoosts": conn.execute("SELECT COUNT(*) AS count FROM xp_boosts WHERE learner_id = ?", (learner_id,)).fetchone()["count"],
                "rewardCurrencyEvents": conn.execute("SELECT COUNT(*) AS count FROM reward_currency_events WHERE learner_id = ?", (learner_id,)).fetchone()["count"],
                "rewardShopPurchases": conn.execute("SELECT COUNT(*) AS count FROM reward_shop_purchases WHERE learner_id = ?", (learner_id,)).fetchone()["count"],
                "friendInvites": conn.execute(
                    "SELECT COUNT(*) AS count FROM friend_invites WHERE requester_learner_id = ? OR addressee_learner_id = ?",
                    (learner_id, learner_id),
                ).fetchone()["count"],
                "friendRelationships": conn.execute(
                    "SELECT COUNT(*) AS count FROM friend_relationships WHERE learner_a_id = ? OR learner_b_id = ?",
                    (learner_id, learner_id),
                ).fetchone()["count"],
                "friendQuests": conn.execute(
                    "SELECT COUNT(*) AS count FROM friend_quests WHERE learner_id = ? OR partner_learner_id = ?",
                    (learner_id, learner_id),
                ).fetchone()["count"],
                "socialSettings": conn.execute("SELECT COUNT(*) AS count FROM social_settings WHERE learner_id = ?", (learner_id,)).fetchone()["count"],
                "socialBlocks": conn.execute(
                    "SELECT COUNT(*) AS count FROM social_blocks WHERE blocker_learner_id = ? OR blocked_learner_id = ?",
                    (learner_id, learner_id),
                ).fetchone()["count"],
                "experimentAssignments": conn.execute("SELECT COUNT(*) AS count FROM experiment_assignments WHERE learner_id = ?", (learner_id,)).fetchone()["count"],
                "experimentEvents": conn.execute("SELECT COUNT(*) AS count FROM experiment_events WHERE learner_id = ?", (learner_id,)).fetchone()["count"],
                "ttsCacheEntries": conn.execute("SELECT COUNT(*) AS count FROM tts_cache WHERE learner_id = ?", (learner_id,)).fetchone()["count"],
                "dialogueUnmatched": conn.execute("SELECT COUNT(*) AS count FROM dialogue_unmatched WHERE learner_id = ?", (learner_id,)).fetchone()["count"],
                "profiles": conn.execute("SELECT COUNT(*) AS count FROM learning_profiles WHERE id = ?", (learner_id,)).fetchone()["count"],
            }
            conn.execute(f"DELETE FROM messages WHERE conversation_id IN ({placeholders})", conversation_ids)
            conn.execute("DELETE FROM conversations WHERE learner_id = ?", (learner_id,))
            conn.execute("DELETE FROM review_cards WHERE learner_id = ?", (learner_id,))
            conn.execute("DELETE FROM usage_records WHERE learner_id = ?", (learner_id,))
            conn.execute("DELETE FROM analytics_events WHERE learner_id = ?", (learner_id,))
            conn.execute("DELETE FROM xp_events WHERE learner_id = ?", (learner_id,))
            conn.execute("DELETE FROM achievement_awards WHERE learner_id = ?", (learner_id,))
            conn.execute("DELETE FROM xp_abuse_flags WHERE learner_id = ?", (learner_id,))
            conn.execute("DELETE FROM reward_inventory WHERE learner_id = ?", (learner_id,))
            conn.execute("DELETE FROM xp_boosts WHERE learner_id = ?", (learner_id,))
            conn.execute("DELETE FROM reward_currency_events WHERE learner_id = ?", (learner_id,))
            conn.execute("DELETE FROM reward_shop_purchases WHERE learner_id = ?", (learner_id,))
            conn.execute("DELETE FROM friend_invites WHERE requester_learner_id = ? OR addressee_learner_id = ?", (learner_id, learner_id))
            conn.execute("DELETE FROM friend_relationships WHERE learner_a_id = ? OR learner_b_id = ?", (learner_id, learner_id))
            conn.execute("DELETE FROM friend_quests WHERE learner_id = ? OR partner_learner_id = ?", (learner_id, learner_id))
            conn.execute("DELETE FROM social_settings WHERE learner_id = ?", (learner_id,))
            conn.execute("DELETE FROM social_blocks WHERE blocker_learner_id = ? OR blocked_learner_id = ?", (learner_id, learner_id))
            conn.execute("DELETE FROM experiment_events WHERE learner_id = ?", (learner_id,))
            conn.execute("DELETE FROM experiment_assignments WHERE learner_id = ?", (learner_id,))
            conn.execute("DELETE FROM tts_cache WHERE learner_id = ?", (learner_id,))
            conn.execute("DELETE FROM dialogue_unmatched WHERE learner_id = ?", (learner_id,))
            conn.execute("DELETE FROM learning_profiles WHERE id = ?", (learner_id,))
        completed = self.audit_log(
            "privacy_deletion_completed",
            actor="privacy_self_service",
            target_type="learner",
            target_id=audit_target_id,
            payload={"deletedCounts": counts, "profileReset": True},
        )
        return {"ok": True, "deletedCounts": counts, "profileReset": True, "auditLogId": completed["id"]}

    def progress_today(self, learner_id: str = "local-dev") -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        key = today_key()
        gamification = self.gamification_summary(learner_id=learner_id)
        with self.connect() as conn:
            user_turns = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM messages
                WHERE role = 'user'
                  AND substr(created_at, 1, 10) = ?
                  AND conversation_id IN (SELECT id FROM conversations WHERE learner_id = ?)
                """,
                (key, learner_id),
            ).fetchone()["count"]
            cards = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM review_cards
                WHERE substr(created_at, 1, 10) = ? AND learner_id = ?
                """,
                (key, learner_id),
            ).fetchone()["count"]
            completed = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM analytics_events
                WHERE event_name = 'practice_turn_completed' AND substr(created_at, 1, 10) = ? AND learner_id = ?
                """,
                (key, learner_id),
            ).fetchone()["count"]
        return {
            "date": key,
            "streakDays": int(gamification["streak"]["currentStreak"]),
            "completedMissions": 1 if user_turns or cards or completed else 0,
            "spokenSentenceCount": int(user_turns),
            "reviewCardsCreated": int(cards),
            "xpEarnedToday": gamification["xp"]["todayXp"],
            "dailyQuestsCompleted": sum(1 for quest in gamification["dailyQuests"] if quest["completed"]),
            "dailyQuestCount": len(gamification["dailyQuests"]),
        }

    def get_profile(self, learner_id: str = "local-dev") -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM learning_profiles WHERE id = ?", (learner_id,)).fetchone()
        if not row:
            return {
                "learnerId": learner_id,
                "nativeLanguage": "ko",
                "targetLanguage": "ja",
                "level": "beginner",
                "jlptLevel": "N5",
                "goals": ["daily_speaking"],
                "weakTags": ["감정표현"],
                "preferredPersonaId": "yui",
            }
        return {
            "learnerId": row["id"],
            "nativeLanguage": row["native_language"],
            "targetLanguage": row["target_language"],
            "level": row["level"],
            "jlptLevel": row["jlpt_level"],
            "goals": _loads(row["goals_json"], []),
            "weakTags": _loads(row["weak_tags_json"], []),
            "preferredPersonaId": row["preferred_persona_id"],
        }

    def update_profile(self, patch: Dict[str, Any], learner_id: str = "local-dev") -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        current = self.get_profile(learner_id)
        updated = {
            "nativeLanguage": patch.get("nativeLanguage", current["nativeLanguage"]),
            "targetLanguage": patch.get("targetLanguage", current["targetLanguage"]),
            "level": patch.get("level", current["level"]),
            "jlptLevel": patch.get("jlptLevel", current["jlptLevel"]),
            "goals": patch.get("goals", current["goals"]),
            "weakTags": patch.get("weakTags", current["weakTags"]),
            "preferredPersonaId": patch.get("preferredPersonaId", current["preferredPersonaId"]),
        }
        timestamp = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO learning_profiles
                (id, native_language, target_language, level, jlpt_level, goals_json, weak_tags_json, preferred_persona_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM learning_profiles WHERE id = ?), ?), ?)
                """,
                (
                    learner_id,
                    updated["nativeLanguage"],
                    updated["targetLanguage"],
                    updated["level"],
                    updated["jlptLevel"],
                    _json(updated["goals"]),
                    _json(updated["weakTags"]),
                    updated["preferredPersonaId"],
                    learner_id,
                    timestamp,
                    timestamp,
                ),
            )
        return self.get_profile(learner_id)

    def recommendations_today(self, learner_id: str = "local-dev") -> Dict[str, Any]:
        profile = self.get_profile(learner_id)
        progress = self.progress_today(learner_id)
        due = self.list_due_review_cards(limit=5, learner_id=learner_id)
        signal_summary = self.learner_signal_summary(learner_id)
        memory_summary = self.memory_summary(learner_id)
        weak_tags = set(profile.get("weakTags") or [])
        weak_tags.update(item["tag"] for item in signal_summary["weakTags"][:5])
        weak_tags.update(item["tag"] for item in memory_summary["tagMastery"] if item["masteryState"] in {"new", "fragile"})
        rooms = self.list_practice_rooms()
        scored_rooms = []
        for room in rooms:
            tags = set(room.get("tags") or [])
            score = 50 + len(tags & weak_tags) * 20
            signal_overlap = tags & set(signal_summary["pressureTags"])
            score += len(signal_overlap) * 12
            memory_overlap = tags & set(memory_summary["pressureTags"])
            score += len(memory_overlap) * 18
            if room.get("personaId") == profile.get("preferredPersonaId"):
                score += 10
            if room["id"] == "tired_today":
                score += 5
            if room["id"] in signal_summary["completedPracticeRoomIdsToday"] and not due:
                score -= 12
            scored_rooms.append(
                {
                    "score": score,
                    "practiceRoom": room,
                    "reason": self._recommendation_reason(room, weak_tags, due, signal_summary, memory_summary),
                }
            )
        scored_rooms.sort(key=lambda item: item["score"], reverse=True)
        return {
            "profile": profile,
            "progress": progress,
            "dueReviewCards": due,
            "recommendedPracticeRooms": scored_rooms[:3],
            "nextBestAction": "review_due_cards" if due else ("repair_memory" if memory_summary["atRiskCards"] else "start_practice_room"),
            "signalSummary": signal_summary,
            "memorySummary": memory_summary,
        }

    def _recommendation_reason(
        self,
        room: Dict[str, Any],
        weak_tags: set[str],
        due: list[Dict[str, Any]],
        signal_summary: Optional[Dict[str, Any]] = None,
        memory_summary: Optional[Dict[str, Any]] = None,
    ) -> str:
        overlap = set(room.get("tags") or []) & weak_tags
        if due:
            return "복습 카드가 밀려 있어 오늘은 짧게 리뷰 후 같은 주제로 말하기 추천"
        memory_overlap = set(room.get("tags") or []) & set((memory_summary or {}).get("pressureTags") or [])
        if memory_overlap:
            return "기억 확률이 낮아지는 태그와 맞는 말하기 복구 루틴"
        signal_overlap = set(room.get("tags") or []) & set((signal_summary or {}).get("pressureTags") or [])
        if signal_overlap:
            return "최근 교정/리뷰 이력에서 반복된 약점 태그와 맞는 연습방"
        if overlap:
            return "최근 약점 태그와 맞는 연습방"
        return "오늘 3분 루틴용 기본 추천"

    def memory_summary(self, learner_id: str = "local-dev") -> Dict[str, Any]:
        cards = self.list_review_cards(learner_id=learner_id)
        if not cards:
            return {
                "cardCount": 0,
                "reviewedCardCount": 0,
                "newCardCount": 0,
                "averageRecallProbability": None,
                "atRiskCards": [],
                "tagMastery": [],
                "pressureTags": [],
                "model": "hlr_inspired_local_estimator_v1",
            }
        reviewed_cards = [card for card in cards if int(card.get("reviewCount") or 0) > 0]
        recall_values = [float(card["recallProbability"]) for card in reviewed_cards]
        at_risk = [
            card
            for card in cards
            if card.get("recallRisk") in {"new", "high", "medium"} or float(card.get("recallProbability") or 0) < 0.8
        ]
        at_risk.sort(key=lambda card: (float(card.get("recallProbability") or 0), -(int(card.get("lapses") or 0))))
        tags: Dict[str, Dict[str, Any]] = {}
        for card in cards:
            for tag in card.get("tags") or ["untagged"]:
                bucket = tags.setdefault(tag, {"tag": tag, "cardCount": 0, "recallTotal": 0.0, "atRiskCount": 0, "lapses": 0})
                bucket["cardCount"] += 1
                bucket["recallTotal"] += float(card.get("recallProbability") or 0)
                bucket["lapses"] += int(card.get("lapses") or 0)
                if card in at_risk:
                    bucket["atRiskCount"] += 1
        tag_mastery = []
        for bucket in tags.values():
            average = bucket["recallTotal"] / max(1, bucket["cardCount"])
            if bucket["cardCount"] == bucket["atRiskCount"]:
                state = "new" if average == 0 else "fragile"
            elif average < 0.65:
                state = "fragile"
            elif average < 0.85:
                state = "developing"
            else:
                state = "stable"
            tag_mastery.append(
                {
                    "tag": bucket["tag"],
                    "cardCount": bucket["cardCount"],
                    "averageRecallProbability": round(average, 3),
                    "atRiskCount": bucket["atRiskCount"],
                    "lapses": bucket["lapses"],
                    "masteryState": state,
                }
            )
        tag_mastery.sort(key=lambda item: (item["averageRecallProbability"], -item["atRiskCount"], item["tag"]))
        return {
            "cardCount": len(cards),
            "reviewedCardCount": len(reviewed_cards),
            "newCardCount": len(cards) - len(reviewed_cards),
            "averageRecallProbability": round(sum(recall_values) / len(recall_values), 3) if recall_values else None,
            "atRiskCards": at_risk[:10],
            "tagMastery": tag_mastery,
            "pressureTags": [item["tag"] for item in tag_mastery if item["masteryState"] in {"new", "fragile"}][:8],
            "model": "hlr_inspired_local_estimator_v1",
        }

    def learner_signal_summary(self, learner_id: str = "local-dev") -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        key = today_key()
        tag_counts: Dict[str, int] = {}
        correction_counts: Dict[str, int] = {}
        lapse_tag_counts: Dict[str, int] = {}
        recent_rooms: list[str] = []
        completed_today: list[str] = []
        with self.connect() as conn:
            card_rows = conn.execute(
                """
                SELECT tags_json, lapses
                FROM review_cards
                WHERE learner_id = ?
                """,
                (learner_id,),
            ).fetchall()
            assistant_messages = conn.execute(
                """
                SELECT metadata_json
                FROM messages
                WHERE role = 'assistant'
                  AND conversation_id IN (SELECT id FROM conversations WHERE learner_id = ?)
                """,
                (learner_id,),
            ).fetchall()
            recent_room_rows = conn.execute(
                """
                SELECT practice_room_id
                FROM conversations
                WHERE learner_id = ?
                ORDER BY created_at DESC
                LIMIT 8
                """,
                (learner_id,),
            ).fetchall()
            completed_rows = conn.execute(
                """
                SELECT payload_json
                FROM analytics_events
                WHERE learner_id = ?
                  AND event_name = 'practice_turn_completed'
                  AND substr(created_at, 1, 10) = ?
                """,
                (learner_id, key),
            ).fetchall()
        for row in card_rows:
            tags = _loads(row["tags_json"], [])
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                if int(row["lapses"] or 0) > 0:
                    lapse_tag_counts[tag] = lapse_tag_counts.get(tag, 0) + int(row["lapses"] or 0)
        for message in assistant_messages:
            metadata = _loads(message["metadata_json"], {})
            for correction in metadata.get("corrections") or []:
                category = correction.get("category") or "unknown"
                correction_counts[category] = correction_counts.get(category, 0) + 1
        for row in recent_room_rows:
            if row["practice_room_id"] not in recent_rooms:
                recent_rooms.append(row["practice_room_id"])
        for row in completed_rows:
            payload = _loads(row["payload_json"], {})
            room_id = payload.get("practiceRoomId")
            if room_id and room_id not in completed_today:
                completed_today.append(room_id)
        pressure_tags = set(tag for tag, count in tag_counts.items() if count >= 1)
        pressure_tags.update(lapse_tag_counts)
        if correction_counts:
            pressure_tags.update({"동사시제"} if correction_counts.get("verb_tense") else set())
            pressure_tags.update({"친구말투", "자연스러움"} if correction_counts.get("naturalness") else set())
            pressure_tags.update({"뉘앙스"} if correction_counts.get("register") else set())
        return {
            "weakTags": [{"tag": tag, "count": count} for tag, count in sorted(tag_counts.items(), key=lambda item: (-item[1], item[0]))[:8]],
            "correctionCategories": [
                {"category": category, "count": count}
                for category, count in sorted(correction_counts.items(), key=lambda item: (-item[1], item[0]))[:8]
            ],
            "lapseTags": [{"tag": tag, "count": count} for tag, count in sorted(lapse_tag_counts.items(), key=lambda item: (-item[1], item[0]))[:8]],
            "recentPracticeRoomIds": recent_rooms,
            "completedPracticeRoomIdsToday": completed_today,
            "pressureTags": sorted(pressure_tags),
        }

    def usage_summary(self, learner_id: str = "local-dev") -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT
                  COALESCE(SUM(llm_input_tokens), 0) AS llm_input_tokens,
                  COALESCE(SUM(llm_output_tokens), 0) AS llm_output_tokens,
                  COALESCE(SUM(stt_seconds), 0) AS stt_seconds,
                  COALESCE(SUM(tts_characters), 0) AS tts_characters,
                  COALESCE(SUM(tts_seconds), 0) AS tts_seconds,
                  COALESCE(SUM(cache_hit), 0) AS tts_cache_hits,
                  COUNT(*) AS records
                FROM usage_records
                WHERE learner_id = ?
                """
                ,
                (learner_id,),
            ).fetchone()
            cache_rows = conn.execute("SELECT COUNT(*) AS count FROM tts_cache WHERE learner_id = ?", (learner_id,)).fetchone()["count"]
        return {
            "llmInputTokens": int(row["llm_input_tokens"]),
            "llmOutputTokens": int(row["llm_output_tokens"]),
            "sttSeconds": float(row["stt_seconds"]),
            "ttsCharacters": int(row["tts_characters"]),
            "ttsSeconds": float(row["tts_seconds"]),
            "ttsCacheHits": int(row["tts_cache_hits"]),
            "usageRecords": int(row["records"]),
            "ttsCacheEntries": int(cache_rows),
            "estimatedMode": "mock_cost_tracking",
        }

    def list_grammar_points(self, level: Optional[str] = None, tag: Optional[str] = None) -> list[Dict[str, Any]]:
        with self.connect() as conn:
            if level:
                rows = conn.execute("SELECT data_json FROM grammar_points WHERE level = ? ORDER BY id", (level,)).fetchall()
            else:
                rows = conn.execute("SELECT data_json FROM grammar_points ORDER BY level, id").fetchall()
        points = [_loads(row["data_json"], {}) for row in rows]
        if tag:
            points = [point for point in points if tag in (point.get("tags") or [])]
        return points

    def list_korean_mistake_patterns(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> list[Dict[str, Any]]:
        with self.connect() as conn:
            if category:
                rows = conn.execute(
                    "SELECT data_json FROM korean_mistake_patterns WHERE category = ? ORDER BY id",
                    (category,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT data_json FROM korean_mistake_patterns ORDER BY category, id").fetchall()
        patterns = [_loads(row["data_json"], {}) for row in rows]
        if tag:
            patterns = [pattern for pattern in patterns if tag in (pattern.get("tags") or [])]
        return patterns

    def weakness_summary(self, learner_id: str = "local-dev") -> Dict[str, Any]:
        learner_id = normalize_learner_id(learner_id)
        profile = self.get_profile(learner_id)
        tag_counts: Dict[str, int] = {}
        correction_counts: Dict[str, int] = {}
        for tag in profile.get("weakTags") or []:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        with self.connect() as conn:
            cards = conn.execute("SELECT tags_json FROM review_cards WHERE learner_id = ?", (learner_id,)).fetchall()
            assistant_messages = conn.execute(
                """
                SELECT metadata_json FROM messages
                WHERE role = 'assistant'
                  AND conversation_id IN (SELECT id FROM conversations WHERE learner_id = ?)
                """,
                (learner_id,),
            ).fetchall()
        for card in cards:
            for tag in _loads(card["tags_json"], []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        for message in assistant_messages:
            metadata = _loads(message["metadata_json"], {})
            for correction in metadata.get("corrections") or []:
                category = correction.get("category") or "unknown"
                correction_counts[category] = correction_counts.get(category, 0) + 1
        top_tags = sorted(tag_counts.items(), key=lambda item: (-item[1], item[0]))
        recommended_grammar = []
        for tag, _count in top_tags[:5]:
            recommended_grammar.extend(self.list_grammar_points(tag=tag))
        recommended_mistakes = []
        for tag, _count in top_tags[:5]:
            recommended_mistakes.extend(self.list_korean_mistake_patterns(tag=tag))
        seen = set()
        unique_grammar = []
        for point in recommended_grammar:
            if point["id"] not in seen:
                unique_grammar.append(point)
                seen.add(point["id"])
        seen_mistakes = set()
        unique_mistakes = []
        for mistake in recommended_mistakes:
            if mistake["id"] not in seen_mistakes:
                unique_mistakes.append(mistake)
                seen_mistakes.add(mistake["id"])
        return {
            "weakTags": [{"tag": tag, "count": count} for tag, count in top_tags],
            "correctionCategories": [
                {"category": category, "count": count}
                for category, count in sorted(correction_counts.items(), key=lambda item: (-item[1], item[0]))
            ],
            "recommendedGrammar": unique_grammar[:5],
            "recommendedMistakes": unique_mistakes[:5],
        }
