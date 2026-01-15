from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


DEFAULT_GLOBAL_CONFIG = {
    "refresh_interval_minutes": 5,
    "layout": {
        "min_tile_width": 40,
        "max_columns": 3,
        "gap": 1,
    },
}


@dataclass
class GlobalConfig:
    refresh_interval_minutes: int
    layout: dict[str, Any]


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text())
    return data or {}


def load_global_config(base_dir: Path) -> GlobalConfig:
    config_path = base_dir / "config" / "global_config.yml"
    if not config_path.exists():
        config_path = base_dir / "global_config.yml"

    data = DEFAULT_GLOBAL_CONFIG | _load_yaml(config_path)
    layout = DEFAULT_GLOBAL_CONFIG["layout"] | data.get("layout", {})
    return GlobalConfig(
        refresh_interval_minutes=int(data.get("refresh_interval_minutes", 5)),
        layout=layout,
    )


def load_env(base_dir: Path) -> None:
    env_path = base_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def load_tile_configs(base_dir: Path) -> dict[str, dict[str, Any]]:
    configs: dict[str, dict[str, Any]] = {}
    search_dirs = [base_dir / "config", base_dir]
    for directory in search_dirs:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("tile_*.yml")):
            name = path.stem.replace("tile_", "", 1)
            if name in configs:
                continue
            configs[name] = _load_yaml(path)
    return configs
