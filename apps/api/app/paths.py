from __future__ import annotations

from pathlib import Path


def resolve_project_root(module_file: Path) -> Path:
    module_path = Path(module_file).resolve()
    search_from = module_path if module_path.is_dir() else module_path.parent
    candidates = [search_from, *search_from.parents]
    for candidate in candidates:
        if (candidate / "contracts").exists() or (candidate / "packs").exists():
            return candidate
    for candidate in candidates:
        if (candidate / "requirements-prod.txt").exists() and (candidate / "app").is_dir():
            return candidate
    if search_from.name == "app":
        return search_from.parent
    return search_from
