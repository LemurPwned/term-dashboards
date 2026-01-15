from __future__ import annotations

from typing import Any

from datetime import datetime
import feedparser
import requests
from rich.text import Text

from term_dashboard.tiles.base import ListTile, TileRenderItem


class FinancialTimesTile(ListTile):
    tile_name = "financial_times"
    title = "Financial Times"

    def fetch_data(self) -> list[dict[str, Any]]:
        feed_url = self.config.get("feed_url")
        if not feed_url:
            raise ValueError("feed_url is required in tile_financial_times.yml")

        headers = {}
        auth = self.config.get("auth", {})
        bearer_token = auth.get("bearer_token")
        cookies = auth.get("cookies")
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"
        if cookies:
            headers["Cookie"] = cookies

        response = requests.get(feed_url, headers=headers, timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        max_items = int(self.config.get("max_items", 10))
        entries = feed.entries[:max_items]
        items = []
        for entry in entries:
            published, published_dt = self._format_date(entry)
            items.append(
                {
                    "title": entry.get("title", "Untitled"),
                    "link": entry.get("link"),
                    "published": published,
                    "published_dt": published_dt,
                }
            )
        return items

    def render_data(self, data: list[dict[str, Any]]) -> None:
        items = []
        for item in data:
            published = item.get("published", "--- --:--")
            prefix = f"{published:<10}  "
            line = Text(prefix)
            line.stylize(self._day_color(item.get("published_dt")), 0, 10)
            line.append(item["title"])
            items.append(TileRenderItem(label=line, url=item.get("link")))
        self.render_list(items)

    @staticmethod
    def _format_date(entry: Any) -> tuple[str, datetime | None]:
        published = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
        if not published:
            return "--- --:--", None
        parsed = datetime(*published[:6])
        return parsed.strftime("%a %H:%M"), parsed

    @staticmethod
    def _day_color(value: datetime | None) -> str:
        if not value:
            return "white"
        palette = ["cyan", "green", "yellow", "magenta", "blue", "bright_black", "white"]
        return palette[value.weekday() % len(palette)]
