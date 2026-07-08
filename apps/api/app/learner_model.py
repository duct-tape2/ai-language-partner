from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from typing import Any, Dict, Iterable, Optional


MODEL_NAME = "offline_logistic_memory_model_v1"
FEATURE_NAMES = [
    "bias",
    "log_memory_strength",
    "memory_difficulty",
    "review_count",
    "lapse_rate",
    "days_since_review",
    "interval_days",
    "ease_factor",
]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)
    z = math.exp(value)
    return z / (1 + z)


def _parse_iso(value: Optional[str]) -> Optional[dt.datetime]:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = dt.datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)
    except Exception:
        return None


def _stable_bucket(value: str, modulo: int) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % modulo


def memory_model_features(card: Dict[str, Any], now: Optional[dt.datetime] = None) -> list[float]:
    now = now or dt.datetime.now(dt.timezone.utc)
    reviewed_at = _parse_iso(card.get("lastReviewedAt"))
    if reviewed_at:
        elapsed_days = max(0.0, (now - reviewed_at).total_seconds() / 86400)
    else:
        elapsed_days = float(card.get("daysSinceReview") or 0)
    review_count = max(0, int(card.get("reviewCount") or 0))
    lapses = max(0, int(card.get("lapses") or 0))
    strength = _clamp(float(card.get("memoryStrengthDays") or 0.5), 0.25, 365.0)
    difficulty = _clamp(float(card.get("memoryDifficulty") or 0.65), 0.05, 0.95)
    interval = max(0, int(card.get("intervalDays") or 0))
    ease = _clamp(float(card.get("easeFactor") or 2.5), 1.3, 4.0)
    attempts = max(1, review_count + lapses)
    return [
        1.0,
        _clamp(math.log1p(strength) / math.log1p(365.0), 0.0, 1.0),
        difficulty,
        _clamp(review_count / 12.0, 0.0, 1.0),
        _clamp(lapses / attempts, 0.0, 1.0),
        _clamp(elapsed_days / 90.0, 0.0, 1.0),
        _clamp(interval / 180.0, 0.0, 1.0),
        _clamp((ease - 1.3) / 2.7, 0.0, 1.0),
    ]


def review_cards_to_examples(
    cards: Iterable[Dict[str, Any]],
    now: Optional[dt.datetime] = None,
    source: str = "review_cards",
) -> list[Dict[str, Any]]:
    examples: list[Dict[str, Any]] = []
    for index, card in enumerate(cards):
        quality = card.get("lastReviewQuality")
        if quality is None:
            continue
        label = 1 if int(quality) >= 3 else 0
        identity = str(card.get("id") or f"{source}_{index}")
        examples.append(
            {
                "id": identity,
                "label": label,
                "features": memory_model_features(card, now=now),
                "source": source,
            }
        )
    return examples


def fixture_examples(now: Optional[dt.datetime] = None) -> list[Dict[str, Any]]:
    now = now or dt.datetime(2026, 6, 30, tzinfo=dt.timezone.utc)
    examples: list[Dict[str, Any]] = []
    strengths = [0.5, 1.2, 3.0, 7.0, 21.0, 60.0]
    difficulties = [0.2, 0.45, 0.7, 0.9]
    elapsed_days = [0.1, 1.0, 4.0, 12.0, 35.0]
    idx = 0
    for strength in strengths:
        for difficulty in difficulties:
            elapsed = elapsed_days[idx % len(elapsed_days)]
            review_count = 1 + (idx % 8)
            lapses = idx % 3
            interval = max(1, round(strength * (1.2 + (review_count % 3) * 0.35)))
            ease = 1.5 + ((idx % 6) * 0.32)
            retention_score = (
                math.log1p(strength) * 0.95
                + review_count * 0.14
                + ease * 0.18
                - difficulty * 1.25
                - (elapsed / max(0.5, strength)) * 0.55
                - lapses * 0.28
            )
            quality = 5 if retention_score >= 1.35 else (4 if retention_score >= 0.95 else (2 if retention_score >= 0.45 else 1))
            reviewed_at = (now - dt.timedelta(days=elapsed)).isoformat(timespec="seconds").replace("+00:00", "Z")
            card = {
                "id": f"fixture_{idx:03d}",
                "memoryStrengthDays": strength,
                "memoryDifficulty": difficulty,
                "reviewCount": review_count,
                "lapses": lapses,
                "intervalDays": interval,
                "easeFactor": ease,
                "lastReviewQuality": quality,
                "lastReviewedAt": reviewed_at,
            }
            examples.extend(review_cards_to_examples([card], now=now, source="deterministic_fixture"))
            idx += 1
    return examples


def _predict(features: list[float], weights: list[float]) -> float:
    return _sigmoid(sum(feature * weight for feature, weight in zip(features, weights)))


def fit_logistic_memory_model(
    examples: list[Dict[str, Any]],
    epochs: int = 700,
    learning_rate: float = 0.18,
    l2: float = 0.015,
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
        if accuracy > best_accuracy or (accuracy == best_accuracy and abs(threshold - 0.5) < abs(best_threshold - 0.5)):
            best_accuracy = accuracy
            best_threshold = threshold
    return round(float(best_threshold), 4)


def evaluate_logistic_memory_model(
    model: Dict[str, Any],
    examples: list[Dict[str, Any]],
    threshold: float = 0.5,
) -> Dict[str, Any]:
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


def train_evaluate_memory_model(
    db_examples: Optional[list[Dict[str, Any]]] = None,
    include_fixture: bool = True,
    now: Optional[dt.datetime] = None,
) -> Dict[str, Any]:
    now = now or dt.datetime.now(dt.timezone.utc)
    examples = list(db_examples or [])
    fixture_count = 0
    if include_fixture:
        fixture = fixture_examples(now=now)
        fixture_count = len(fixture)
        examples.extend(fixture)
    if not examples:
        return {
            "modelName": MODEL_NAME,
            "status": "insufficient_examples",
            "featureNames": FEATURE_NAMES,
            "dbExampleCount": 0,
            "fixtureExampleCount": 0,
            "trainCount": 0,
            "evaluation": evaluate_logistic_memory_model({"weights": [0.0 for _ in FEATURE_NAMES]}, []),
            "productionTrained": False,
            "notes": ["No local review-grade examples and fixture examples disabled."],
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
        train = train[:-len(evaluation)]
    model = fit_logistic_memory_model(train)
    decision_threshold = calibrate_decision_threshold(model, train)
    metrics = evaluate_logistic_memory_model(model, evaluation, threshold=decision_threshold)
    default_threshold_metrics = evaluate_logistic_memory_model(model, evaluation, threshold=0.5)
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
        "evaluation": metrics,
        "defaultThresholdEvaluation": default_threshold_metrics,
        "productionTrained": False,
        "notes": [
            "This proves a deterministic offline train/evaluate pipeline, not a Duolingo-scale production learner model.",
            "Use real review-grade history before enabling model-driven scheduling decisions.",
        ],
        "artifactVersion": "learner_model_evaluation_v1",
    }


def artifact_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
