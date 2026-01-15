from __future__ import annotations

from typing import Any

from datetime import datetime, timezone
import requests
from rich.text import Text

from term_dashboard.tiles.base import ListTile, TileRenderItem


class HackerNewsTile(ListTile):
    tile_name = "hackernews"
    title = "Hacker News"

    def fetch_data(self) -> list[dict[str, Any]]:
        feed = (self.config.get("feed") or "top").lower()
        limit = int(self.config.get("limit", 10))

        if feed == "new":
            url = "https://hn.algolia.com/api/v1/search_by_date?tags=story"
        elif feed == "best":
            url = "https://hn.algolia.com/api/v1/search?tags=story&numericFilters=points>100"
        else:
            url = "https://hn.algolia.com/api/v1/search?tags=front_page"

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        hits = response.json().get("hits", [])
        return hits[:limit]

    def render_data(self, data: list[dict[str, Any]]) -> None:
        items = []
        for hit in data:
            title = hit.get("title") or hit.get("story_title") or "Untitled"
            points = hit.get("points") or 0
            url = hit.get("url")
            created_at = hit.get("created_at")
            date_label = self._format_date(created_at)
            date_color = self._day_color(created_at)
            if not url and hit.get("objectID"):
                url = f"https://news.ycombinator.com/item?id={hit['objectID']}"
            prefix = f"{date_label:<10}  {points:>4}  "
            line = Text(prefix)
            line.stylize(date_color, 0, 10)
            line.append(title)
            items.append(TileRenderItem(label=line, url=url))
        self.render_list(items)

    @staticmethod
    def _format_date(value: str | None) -> str:
        if not value:
            return "--- --:--"
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.astimezone(timezone.utc).strftime("%a %H:%M")
        except ValueError:
            return value[:10]

    @staticmethod
    def _day_color(value: str | None) -> str:
        if not value:
            return "white"
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return "white"
        palette = ["cyan", "green", "yellow", "magenta", "blue", "bright_black", "white"]
        return palette[parsed.weekday() % len(palette)]
