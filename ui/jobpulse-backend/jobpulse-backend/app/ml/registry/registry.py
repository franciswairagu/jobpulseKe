"""
Model registry.

Per spec section 4: track available models, load once, reuse. Also
records the honest status of each of the three originally-planned
model integrations - including the one (time-series/job-availability)
that was descoped to CRUD status tracking per an explicit product
decision, so that decision stays visible at runtime rather than
silently disappearing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ModelStatus(str, Enum):
    READY = "READY"
    DEGRADED = "DEGRADED"          # loaded but a sub-component (e.g. classifier) is unavailable
    NOT_AVAILABLE = "NOT_AVAILABLE"


@dataclass
class ModelEntry:
    model_name: str
    version: str
    framework: str
    status: ModelStatus
    loaded_at: datetime
    notes: str = ""


class ModelRegistry:
    def __init__(self):
        self._entries: dict[str, ModelEntry] = {}

    def register(self, entry: ModelEntry) -> None:
        self._entries[entry.model_name] = entry

    def get(self, model_name: str) -> ModelEntry | None:
        return self._entries.get(model_name)

    def all(self) -> list[ModelEntry]:
        return list(self._entries.values())


_registry = ModelRegistry()


def build_registry() -> ModelRegistry:
    from app.ml.adapters.cv_analyzer import CVAnalyzer

    now = datetime.now(timezone.utc)
    cv_analyzer = CVAnalyzer()
    cv_health = cv_analyzer.health()

    _registry.register(ModelEntry(
        model_name="CV_NLP_MODEL",
        version="skill_extractor_v1_reconstructed" + ("+classifier" if cv_health["classifier_ready"] else ""),
        framework="rule-based" + ("+sklearn" if cv_health["classifier_ready"] else ""),
        status=ModelStatus.READY if cv_health["classifier_ready"] else ModelStatus.DEGRADED,
        loaded_at=now,
        notes=(
            "Skill/metadata extraction is real (rule-based, reconstructed from the "
            "notebook's documented interface). Tech-category classification is "
            "only active if a trained .joblib artifact exists at CV_CATEGORY_MODEL_PATH."
            if not cv_health["classifier_ready"] else
            "Skill/metadata extraction (rule-based) + trained tech-category classifier, both active."
        ),
    ))

    _registry.register(ModelEntry(
        model_name="RECOMMENDATION_MODEL",
        version="1.0-hybrid-weighted",
        framework="deterministic-scoring (src/recommender)",
        status=ModelStatus.READY,
        loaded_at=now,
        notes="Real, uploaded JobRecommender package used verbatim - hybrid weighted skill/experience/location scoring.",
    ))

    _registry.register(ModelEntry(
        model_name="JOB_AVAILABILITY_MODEL",
        version="n/a",
        framework="n/a",
        status=ModelStatus.NOT_AVAILABLE,
        loaded_at=now,
        notes=(
            "No time-series model exists (the pipeline's own time-series component was "
            "rescoped to a reliability audit + market composition report due to unreliable "
            "date_posted coverage). Per product decision, job availability is tracked via "
            "CRUD status + JobStatusHistory only - no prediction is made."
        ),
    ))

    return _registry


def get_registry() -> ModelRegistry:
    return _registry
