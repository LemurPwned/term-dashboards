from __future__ import annotations

import asyncio
import shutil
import subprocess
import webbrowser
from dataclasses import dataclass
from typing import Any, Iterable

from textual.containers import Container
from textual.widgets import Label, ListItem, ListView, Static


@dataclass
class TileRenderItem:
    label: Any
    url: str | None = None
    file_path: str | None = None
    line: int | None = None
    open_in_nvim: bool = False
    open_in_terminal: bool = False


class LinkItem(ListItem):
    def __init__(
        self,
        label: Any,
        url: str | None = None,
        file_path: str | None = None,
        line: int | None = None,
        open_in_nvim: bool = False,
        open_in_terminal: bool = False,
        background: str | None = None,
        color: str | None = None,
    ) -> None:
        self.url = url
        self.file_path = file_path
        self.line = line
        self.open_in_nvim = open_in_nvim
        self.open_in_terminal = open_in_terminal
        label_widget = Label(label)
        if color:
            label_widget.styles.color = color
        super().__init__(label_widget)
        if background:
            self.styles.background = background
            self.styles.padding = (0, 1)
        self.styles.width = "100%"


class BaseTile(Container):
    tile_name = "base"
    title = "Tile"

    def __init__(self, config: dict[str, Any], global_config: Any) -> None:
        super().__init__()
        self.config = config
        self.global_config = global_config
        self.body: Static | ListView | None = None
        self.refresh_seconds = int(
            config.get("refresh_interval_minutes", global_config.refresh_interval_minutes)
        ) * 60

    def compose(self):
        yield Static(self.config.get("title", self.title), classes="tile-header")
        self.body = Static("Loading…", classes="tile-body")
        yield self.body

    async def on_mount(self) -> None:
        await self.refresh_tile()
        self.set_interval(self.refresh_seconds, self.refresh_tile)

    async def refresh_tile(self) -> None:
        try:
            data = await asyncio.to_thread(self.fetch_data)
            self.render_data(data)
        except Exception as exc:  # noqa: BLE001
            self.render_error(str(exc))

    def fetch_data(self) -> Any:
        raise NotImplementedError

    def render_data(self, data: Any) -> None:
        if self.body:
            self.body.update(str(data))

    def render_error(self, message: str) -> None:
        if self.body:
            self.body.update(f"Error: {message}")


class ListTile(BaseTile):
    def compose(self):
        yield Static(self.config.get("title", self.title), classes="tile-header")
        self.body = ListView(classes="tile-body")
        yield self.body

    def render_list(self, items: Iterable[TileRenderItem]) -> None:
        if not isinstance(self.body, ListView):
            return
        self.body.clear()
        default_open_in_terminal = bool(self.config.get("open_links_in_terminal", False))
        for index, item in enumerate(items):
            background = "#141a25" if index % 2 else "#101623"
            row = LinkItem(
                item.label,
                item.url,
                file_path=item.file_path,
                line=item.line,
                open_in_nvim=item.open_in_nvim,
                open_in_terminal=item.open_in_terminal or default_open_in_terminal,
                background=background,
                color="#d9e2f2",
            )
            self.body.append(row)

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if not isinstance(item, LinkItem):
            return
        if item.url:
            if item.open_in_terminal:
                self._open_in_terminal([item.url])
            else:
                webbrowser.open(item.url)
            return
        if item.file_path:
            if item.open_in_nvim:
                command = ["nvim", item.file_path]
                if item.line:
                    command.insert(1, f"+{item.line}")
                self._open_in_terminal(command)
                if isinstance(self.body, ListView):
                    self.body.focus()
            else:
                webbrowser.open(f"file://{item.file_path}")

    def _open_in_terminal(self, args: list[str]) -> None:
        with self.app.suspend():
            if args and args[0].startswith("http"):
                terminal_browser = self._terminal_browser()
                if terminal_browser:
                    subprocess.run([terminal_browser, *args], check=False)
                else:
                    webbrowser.open(args[0])
                return
            subprocess.run(args, check=False)
        self.app.refresh()

    @staticmethod
    def _terminal_browser() -> str | None:
        for candidate in ("w3m", "lynx", "links"):
            if shutil.which(candidate):
                return candidate
        return None
