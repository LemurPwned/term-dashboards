from __future__ import annotations

from pathlib import Path
from typing import Any

from textual.app import App
from textual.containers import Grid

from term_dashboard.config import load_env, load_global_config, load_tile_configs
from term_dashboard.tiles.financial_times import FinancialTimesTile
from term_dashboard.tiles.hackernews import HackerNewsTile
from term_dashboard.tiles.obsidian import ObsidianSearchTile
from term_dashboard.tiles.stocks import StocksTile
from term_dashboard.tiles.weather import WeatherTile
from term_dashboard.tiles.work import WorkTile


TILE_CLASSES = [
    StocksTile,
    HackerNewsTile,
    WeatherTile,
    FinancialTimesTile,
    WorkTile,
    ObsidianSearchTile,
]


class DashboardApp(App):
    CSS = """
    Screen {
        background: #0b0f17;
    }

    #grid {
        width: 100%;
        height: 100%;
    }

    .tile-header {
        text-style: bold;
        color: #e6edf3;
        background: #1b2536;
        padding: 0 1;
    }

    .tile-body {
        padding: 1;
        color: #d0d6de;
    }

    .search-input {
        margin: 1 1 0 1;
        background: #0f1622;
        color: #e6edf3;
    }

    .tile {
        border: round #2b3545;
    }
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        super().__init__()
        self.base_dir = base_dir or Path.cwd()
        load_env(self.base_dir)
        self.global_config = load_global_config(self.base_dir)
        self.tile_configs = load_tile_configs(self.base_dir)
        self.tiles = self._build_tiles()

    def _build_tiles(self) -> list[Any]:
        tiles = []
        for tile_cls in TILE_CLASSES:
            config = self.tile_configs.get(tile_cls.tile_name, {})
            tile = tile_cls(config=config, global_config=self.global_config)
            tile.add_class("tile")
            tiles.append(tile)
        return tiles

    def compose(self):
        with Grid(id="grid"):
            for tile in self.tiles:
                yield tile

    async def on_mount(self) -> None:
        self._apply_grid_layout()

    async def on_resize(self) -> None:
        self._apply_grid_layout()

    def _apply_grid_layout(self) -> None:
        grid = self.query_one("#grid", Grid)
        layout = self.global_config.layout
        min_width = int(layout.get("min_tile_width", 40))
        max_columns = int(layout.get("max_columns", 3))
        gap = int(layout.get("gap", 1))
        width = max(self.size.width, min_width)
        columns = max(1, min(max_columns, width // min_width))
        grid.styles.grid_size_columns = columns
        grid.styles.grid_gutter = (gap, gap)


def run() -> None:
    DashboardApp().run()
