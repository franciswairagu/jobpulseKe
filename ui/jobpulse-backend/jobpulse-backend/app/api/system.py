from fastapi import APIRouter

from app.ml.registry.registry import get_registry

router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    registry = get_registry()
    entries = registry.all()
    return {
        "status": "ok",
        "models": [
            {
                "model_name": e.model_name,
                "version": e.version,
                "framework": e.framework,
                "status": e.status.value,
                "loaded_at": e.loaded_at.isoformat(),
                "notes": e.notes,
            }
            for e in entries
        ],
    }


@router.get("/api/models")
def list_models():
    registry = get_registry()
    return [
        {
            "model_name": e.model_name,
            "version": e.version,
            "framework": e.framework,
            "status": e.status.value,
            "notes": e.notes,
        }
        for e in registry.all()
    ]
