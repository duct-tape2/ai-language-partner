from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict, Iterable, Optional


MODEL_NAME = "offline_logistic_reputation_model_v1"
FEATURE_NAMES = [
    "bias",
    "week_xp_norm",
    "week_event_count_norm",
    "source_concentration_risk",
    "open_flag_count_norm",
    "blocking_flag_count_norm",
    "duplicate_payload_signal",
    "boosted_xp_signal",
    "incoming_block_norm",
    "device_risk_norm",
]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)
    z = math.exp(value)
    return z / (1 + z)


def _stable_bucket(value: str, modulo: int) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % modulo


def reputation_profile_features(profile: Dict[str, Any]) -> list[float]:
    summary = profile.get("summary") if isinstance(profile.get("summary"), dict) else {}
    signals = profile.get("signals") if isinstance(profile.get("signals"), list) else []
    signal_keys = {str(signal.get("key") or "") for signal in signals if isinstance(signal, dict)}
    week_xp = max(0, int(summary.get("weekXp") or 0))
    week_event_count = max(0, int(summary.get("weekEventCount") or 0))
    week_source_count = max(0, int(summary.get("weekSourceCount") or 0))
    open_flags = max(0, int(summary.get("openXpAbuseFlagCount") or 0))
    blocking_flags = max(0, int(summary.get("blockingXpAbuseFlagCount") or 0))
    incoming_blocks = max(0, int(summary.get("incomingBlockCount") or 0))
    device_risk_count = max(0, int(summary.get("revokedDeviceCount") or 0)) + max(0, int(summary.get("untrustedDeviceCount") or 0))
    concentration = 0.0
    if week_event_count > 0:
        concentration = 1.0 - _clamp(week_source_count / max(1, week_event_count), 0.0, 1.0)
    return [
        1.0,
        _clamp(math.log1p(week_xp) / math.log1p(5000), 0.0, 1.0),
        _clamp(week_event_count / 250.0, 0.0, 1.0),
        concentration,
        _clamp(open_flags / 6.0, 0.0, 1.0),
        _clamp(blocking_flags / 3.0, 0.0, 1.0),
        1.0 if "automation:duplicate_payload_cluster" in signal_keys or any("duplicate_payload" in key for key in signal_keys) else 0.0,
        1.0 if any("boosted_xp" in key for key in signal_keys) else 0.0,
        _clamp(incoming_blocks / 5.0, 0.0, 1.0),
        _clamp(device_risk_count / 5.0, 0.0, 1.0),
    ]


def reputation_profiles_to_examples(profiles: Iterable[Dict[str, Any]], source: str = "reputation_profiles") -> list[Dict[str, Any]]:
    examples: list[Dict[str, Any]] = []
    for index, profile in enumerate(profiles):
        learner_id = str(profile.get("learnerId") or f"{source}_{index}")
        risk_band = str(profile.get("riskBand") or "trusted")
        label = 1 if risk_band in {"high", "critical"} or profile.get("leaderboardEligible") is False else 0
        examples.append(
            {
                "id": learner_id,
                "label": label,
                "features": reputation_profile_features(profile),
                "source": source,
            }
        )
    return examples


def fixture_examples() -> list[Dict[str, Any]]:
    fixtures = [
        {
            "learnerId": "fixture_trusted_low_xp",
            "riskBand": "trusted",
            "leaderboardEligible": True,
            "signals": [],
            "summary": {"weekXp": 120, "weekEventCount": 8, "weekSourceCount": 4, "openXpAbuseFlagCount": 0, "blockingXpAbuseFlagCount": 0},
        },
        {
            "learnerId": "fixture_regular_power_user",
            "riskBand": "trusted",
            "leaderboardEligible": True,
            "signals": [],
            "summary": {"weekXp": 780, "weekEventCount": 44, "weekSourceCount": 6, "openXpAbuseFlagCount": 0, "blockingXpAbuseFlagCount": 0},
        },
        {
            "learnerId": "fixture_social_warning",
            "riskBand": "medium",
            "leaderboardEligible": True,
            "signals": [{"key": "social:incoming_blocks"}],
            "summary": {"weekXp": 500, "weekEventCount": 30, "weekSourceCount": 5, "incomingBlockCount": 2, "openXpAbuseFlagCount": 0, "blockingXpAbuseFlagCount": 0},
        },
        {
            "learnerId": "fixture_daily_soft_limit_review",
            "riskBand": "medium",
            "leaderboardEligible": True,
            "signals": [{"key": "xp_abuse:daily_xp_soft_limit_exceeded"}],
            "summary": {"weekXp": 1500, "weekEventCount": 90, "weekSourceCount": 7, "openXpAbuseFlagCount": 1, "blockingXpAbuseFlagCount": 0},
        },
        {
            "learnerId": "fixture_duplicate_payload_block",
            "riskBand": "high",
            "leaderboardEligible": False,
            "signals": [{"key": "xp_abuse:duplicate_payload_xp_burst"}, {"key": "automation:duplicate_payload_cluster"}],
            "summary": {"weekXp": 900, "weekEventCount": 80, "weekSourceCount": 1, "openXpAbuseFlagCount": 1, "blockingXpAbuseFlagCount": 1},
        },
        {
            "learnerId": "fixture_boosted_xp_block",
            "riskBand": "high",
            "leaderboardEligible": False,
            "signals": [{"key": "xp_abuse:boosted_xp_soft_limit_exceeded"}],
            "summary": {"weekXp": 1900, "weekEventCount": 120, "weekSourceCount": 3, "openXpAbuseFlagCount": 2, "blockingXpAbuseFlagCount": 1},
        },
        {
            "learnerId": "fixture_critical_multi_signal",
            "riskBand": "critical",
            "leaderboardEligible": False,
            "signals": [
                {"key": "xp_abuse:boosted_xp_soft_limit_exceeded"},
                {"key": "xp_abuse:duplicate_payload_xp_burst"},
                {"key": "social:incoming_blocks"},
                {"key": "device:revoked_devices"},
            ],
            "summary": {
                "weekXp": 3100,
                "weekEventCount": 180,
                "weekSourceCount": 2,
                "openXpAbuseFlagCount": 3,
                "blockingXpAbuseFlagCount": 2,
                "incomingBlockCount": 4,
                "revokedDeviceCount": 1,
            },
        },
        {
            "learnerId": "fixture_device_noise_low",
            "riskBand": "low",
            "leaderboardEligible": True,
            "signals": [{"key": "device:many_untrusted_devices"}],
            "summary": {"weekXp": 350, "weekEventCount": 20, "weekSourceCount": 5, "untrustedDeviceCount": 3, "openXpAbuseFlagCount": 0, "blockingXpAbuseFlagCount": 0},
        },
    ]
    return reputation_profiles_to_examples(fixtures, source="deterministic_reputation_fixture")


def _predict(features: list[float], weights: list[float]) -> float:
    return _sigmoid(sum(feature * weight for feature, weight in zip(features, weights)))


def fit_logistic_reputation_model(
    examples: list[Dict[str, Any]],
    epochs: int = 650,
    learning_rate: float = 0.16,
    l2: float = 0.02,
) -> Dict[str, Any]:
    if not examples:
        raise ValueError("At least one training example is required")
    weights = [0.0 for _ in FEATURE_NAMES]
    for _ in range(max(1, epochs)):
        gradients = [0.0 for _ in weights]
        for example in examples:
            prediction = _predict(example["features"], weights)
            error = prediction - float(example["label"])
            for index, feature in enumerate(example["features"]):
                gradients[index] += error * feature
        count = float(len(examples))
        for index in range(len(weights)):
            regularizer = 0.0 if index == 0 else l2 * weights[index]
            weights[index] -= learning_rate * ((gradients[index] / count) + regularizer)
    return {
        "modelName": MODEL_NAME,
        "featureNames": FEATURE_NAMES,
        "weights": [round(weight, 6) for weight in weights],
    }


def calibrate_decision_threshold(model: Dict[str, Any], examples: list[Dict[str, Any]]) -> float:
    if not examples:
        return 0.5
    weights = [float(value) for value in model["weights"]]
    candidates = sorted({_predict(example["features"], weights) for example in examples})
    thresholds = [0.5]
    thresholds.extend(candidates)
    thresholds.extend((left + right) / 2 for left, right in zip(candidates, candidates[1:]))
    best_threshold = 0.5
    best_accuracy = -1.0
    for threshold in thresholds:
        correct = sum(1 for example in examples if (_predict(example["features"], weights) >= threshold) == bool(example["label"]))
        accuracy = correct / len(examples)
        if accuracy > best_accuracy or (accuracy == best_accuracy and threshold >= best_threshold):
            best_accuracy = accuracy
            best_threshold = threshold
    return round(float(best_threshold), 4)


def evaluate_logistic_reputation_model(model: Dict[str, Any], examples: list[Dict[str, Any]], threshold: float = 0.5) -> Dict[str, Any]:
    if not examples:
        return {
            "exampleCount": 0,
            "accuracy": None,
            "logLoss": None,
            "brierScore": None,
            "auc": None,
            "positiveCount": 0,
            "negativeCount": 0,
            "decisionThreshold": round(float(threshold), 4),
        }
    weights = [float(value) for value in model["weights"]]
    predictions = [(_predict(example["features"], weights), int(example["label"])) for example in examples]
    decision_threshold = float(threshold)
    correct = sum(1 for probability, label in predictions if (probability >= decision_threshold) == bool(label))
    eps = 1e-9
    log_loss = -sum(label * math.log(max(eps, probability)) + (1 - label) * math.log(max(eps, 1 - probability)) for probability, label in predictions) / len(predictions)
    brier = sum((probability - label) ** 2 for probability, label in predictions) / len(predictions)
    positives = [probability for probability, label in predictions if label == 1]
    negatives = [probability for probability, label in predictions if label == 0]
    auc = None
    if positives and negatives:
        wins = 0.0
        for positive in positives:
            for negative in negatives:
                if positive > negative:
                    wins += 1.0
                elif positive == negative:
                    wins += 0.5
        auc = wins / (len(positives) * len(negatives))
    return {
        "exampleCount": len(examples),
        "accuracy": round(correct / len(examples), 4),
        "logLoss": round(log_loss, 4),
        "brierScore": round(brier, 4),
        "auc": round(auc, 4) if auc is not None else None,
        "positiveCount": len(positives),
        "negativeCount": len(negatives),
        "decisionThreshold": round(decision_threshold, 4),
    }


def train_evaluate_reputation_model(
    db_examples: Optional[list[Dict[str, Any]]] = None,
    include_fixture: bool = True,
) -> Dict[str, Any]:
    examples = list(db_examples or [])
    fixture_count = 0
    if include_fixture:
        fixture = fixture_examples()
        fixture_count = len(fixture)
        examples.extend(fixture)
    if not examples:
        empty_model = {"weights": [0.0 for _ in FEATURE_NAMES]}
        return {
            "modelName": MODEL_NAME,
            "status": "insufficient_examples",
            "featureNames": FEATURE_NAMES,
            "dbExampleCount": 0,
            "fixtureExampleCount": 0,
            "trainCount": 0,
            "evaluation": evaluate_logistic_reputation_model(empty_model, []),
            "productionTrained": False,
            "notes": ["No local reputation examples and fixture examples disabled."],
        }
    train = []
    evaluation = []
    for example in examples:
        target = evaluation if _stable_bucket(example["id"], 5) == 0 else train
        target.append(example)
    if not train:
        train, evaluation = examples, []
    if not evaluation and len(train) > 3:
        evaluation = train[-max(1, len(train) // 5):]
        train = train[: -len(evaluation)]
    model = fit_logistic_reputation_model(train)
    threshold = calibrate_decision_threshold(model, train)
    source_counts: Dict[str, int] = {}
    for example in examples:
        source_counts[example["source"]] = source_counts.get(example["source"], 0) + 1
    return {
        "modelName": MODEL_NAME,
        "status": "evaluated",
        "featureNames": FEATURE_NAMES,
        "weights": model["weights"],
        "coefficients": dict(zip(FEATURE_NAMES, model["weights"])),
        "dbExampleCount": len(db_examples or []),
        "fixtureExampleCount": fixture_count,
        "sourceCounts": source_counts,
        "trainCount": len(train),
        "evaluation": evaluate_logistic_reputation_model(model, evaluation, threshold=threshold),
        "defaultThresholdEvaluation": evaluate_logistic_reputation_model(model, evaluation, threshold=0.5),
        "productionTrained": False,
        "notes": [
            "This proves an offline anti-cheat/reputation train/evaluate pipeline, not production-scale learned enforcement.",
            "Use real moderation outcomes before enabling automated enforcement decisions.",
        ],
        "artifactVersion": "reputation_model_evaluation_v1",
    }


def artifact_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
