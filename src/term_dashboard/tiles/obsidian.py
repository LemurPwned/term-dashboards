from __future__ import annotations

import asyncio
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.text import Text
from textual.widgets import Input, ListView, Static

from term_dashboard.tiles.base import ListTile, TileRenderItem


class ObsidianSearchTile(ListTile):
    tile_name = "obsidian"
    title = "Obsidian"

    def __init__(self, config: dict[str, Any], global_config: Any) -> None:
        super().__init__(config, global_config)
        self.input: Input | None = None
        self.body: ListView | None = None
        self._search_task: asyncio.Task | None = None
        self._last_query = ""

    def compose(self):
        yield Static(self.config.get("title", self.title), classes="tile-header")
        self.input = Input(placeholder="Search notes…", classes="search-input")
        yield self.input
        self.body = ListView(classes="tile-body")
        yield self.body

    async def on_mount(self) -> None:
        if self.input:
            self.input.focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        await self._run_search(event.value.strip(), debounce=False)

    async def on_input_changed(self, event: Input.Changed) -> None:
        await self._run_search(event.value.strip(), debounce=True)

    async def _run_search(self, query: str, debounce: bool) -> None:
        if self._search_task:
            self._search_task.cancel()
        if not query:
            self.render_list([TileRenderItem(label=Text("Enter a search query", style="dim"))])
            return
        self._last_query = query
        if debounce:
            self._search_task = asyncio.create_task(self._debounced_search(query))
        else:
            self._search_task = asyncio.create_task(self._execute_search(query))

    async def _debounced_search(self, query: str) -> None:
        await asyncio.sleep(0.35)
        await self._execute_search(query)

    async def _execute_search(self, query: str) -> None:
        if query != self._last_query:
            return
        results = await asyncio.to_thread(self._search, query)
        if query != self._last_query:
            return
        if isinstance(results, str):
            self.render_list([TileRenderItem(label=Text(results, style="red"))])
            return
        if not results:
            self.render_list([TileRenderItem(label=Text("No matches", style="dim"))])
            return
        self.render_list(results)

    def _search(self, query: str) -> list[TileRenderItem] | str:
        vault_paths = [Path(path).expanduser() for path in self.config.get("vault_paths", [])]
        vault_paths = [path for path in vault_paths if path.exists()]
        if not vault_paths:
            return "No vault paths configured"

        max_results = int(self.config.get("max_results", 20))
        open_in_nvim = bool(self.config.get("open_in_nvim", True))
        args = [
            "rg",
            "--no-heading",
            "--color",
            "never",
            "--line-number",
            "--column",
            query,
            *[str(path) for path in vault_paths],
        ]
        try:
            process = subprocess.run(args, capture_output=True, text=True, check=False)
        except FileNotFoundError:
            return "ripgrep (rg) not found"

        if process.returncode not in (0, 1):
            return process.stderr.strip() or "Search failed"

        items: list[TileRenderItem] = []
        lines = process.stdout.splitlines()
        for line in lines:
            parts = line.split(":", 3)
            if len(parts) < 4:
                continue
            path, line_no, column, text = parts
            try:
                line_index = int(line_no)
                column_index = int(column)
            except ValueError:
                continue
            snippet = self._snippet(text, column_index, query)
            label = self._build_label(path, line_index, snippet)
            items.append(
                TileRenderItem(
                    label=label,
                    file_path=path,
                    line=line_index,
                    open_in_nvim=open_in_nvim,
                )
            )
            if len(items) >= max_results:
                break
        return items

    def _snippet(self, text: str, column_index: int, query: str) -> Text:
        match_start = max(column_index - 1, 0)
        start = max(match_start - 30, 0)
        end = min(match_start + 70, len(text))
        snippet = text[start:end].strip()
        highlighted = Text(snippet)
        try:
            pattern = re.compile(query, re.IGNORECASE)
        except re.error:
            return Text(snippet)

        for match in pattern.finditer(snippet):
            highlighted.stylize("bold yellow", match.start(), match.end())
        return highlighted

    def _build_label(self, path: str, line_index: int, snippet: Text) -> Text:
        title = Path(path).stem
        date_label = self._modified_date(path)
        header = Text(f"{date_label:<10}  {title}", style="bold")
        header.stylize(self._day_color(path), 0, 10)
        label = Text()
        label.append(header)
        label.append("\n  ")
        label.append(f"{path}", style="dim")
        label.append("\n  ")
        label.append(snippet)
        return label

    @staticmethod
    def _modified_date(path: str) -> str:
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            return "--- --:--"
        return datetime.fromtimestamp(mtime).strftime("%a %H:%M")

    @staticmethod
    def _day_color(path: str) -> str:
        try:
            mtime = os.path.getmtime(path)
            day = datetime.fromtimestamp(mtime)
        except OSError:
            return "white"
        palette = ["cyan", "green", "yellow", "magenta", "blue", "bright_black", "white"]
        return palette[day.weekday() % len(palette)]
