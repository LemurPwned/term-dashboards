from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import Any

import requests
from rich.text import Text

from term_dashboard.tiles.base import ListTile, TileRenderItem


class WorkTile(ListTile):
    tile_name = "work"
    title = "Work"

    def fetch_data(self) -> dict[str, Any]:
        github_token = os.getenv("GITHUB_TOKEN")
        linear_token = os.getenv("LINEAR_TOKEN")
        data: dict[str, Any] = {
            "github": [],
            "linear": [],
            "github_token": bool(github_token),
            "linear_token": bool(linear_token),
        }
        if github_token:
            try:
                data["github"] = self._fetch_github(github_token)
            except Exception as exc:  # noqa: BLE001
                data["github_error"] = str(exc)
        if linear_token:
            try:
                data["linear"] = self._fetch_linear(linear_token)
            except Exception as exc:  # noqa: BLE001
                data["linear_error"] = str(exc)
        return data

    def render_data(self, data: dict[str, Any]) -> None:
        items: list[TileRenderItem] = []
        github_items = data.get("github", [])
        linear_items = data.get("linear", [])
        github_token = data.get("github_token", False)
        linear_token = data.get("linear_token", False)
        github_error = data.get("github_error")
        linear_error = data.get("linear_error")

        items.append(TileRenderItem(label=Text("GitHub", style="bold #9ddcff")))
        if github_items:
            items.extend(self._render_github(github_items))
        elif github_error:
            items.append(TileRenderItem(label=Text(f"GitHub error: {github_error}", style="red")))
        elif not github_token:
            items.append(TileRenderItem(label=Text("Set GITHUB_TOKEN in .env", style="red")))
        else:
            items.append(TileRenderItem(label=Text("No assigned items", style="dim")))

        items.append(TileRenderItem(label=Text(" ")))
        items.append(TileRenderItem(label=Text("Linear", style="bold #c7b3ff")))
        if linear_items:
            items.extend(self._render_linear(linear_items))
        elif linear_error:
            items.append(TileRenderItem(label=Text(f"Linear error: {linear_error}", style="red")))
        elif not linear_token:
            items.append(TileRenderItem(label=Text("Set LINEAR_TOKEN in .env", style="red")))
        else:
            items.append(TileRenderItem(label=Text("No assigned tasks", style="dim")))

        self.render_list(items)

    def _fetch_github(self, token: str) -> list[dict[str, Any]]:
        max_items = int(self.config.get("github_max_items", 8))
        base_headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

        user = self.config.get("github_user")
        if not user:
            response = requests.get("https://api.github.com/user", headers=base_headers, timeout=10)
            response.raise_for_status()
            user = response.json().get("login")

        response = requests.get(
            "https://api.github.com/issues",
            headers=base_headers,
            params={"filter": "assigned", "state": "open", "per_page": max_items},
            timeout=10,
        )
        if not response.ok:
            raise ValueError(f"GitHub API {response.status_code}: {response.text[:120]}")
        assigned = response.json()

        review_requested = []
        if user:
            response = requests.get(
                "https://api.github.com/search/issues",
                headers=base_headers,
                params={
                    "q": f"is:open is:pr review-requested:{user}",
                    "per_page": max_items,
                },
                timeout=10,
            )
            if not response.ok:
                raise ValueError(f"GitHub search {response.status_code}: {response.text[:120]}")
            review_requested = response.json().get("items", [])

        seen = set()
        output = []
        for item in assigned + review_requested:
            url = item.get("html_url")
            if not url or url in seen:
                continue
            seen.add(url)
            repo = (item.get("repository_url") or "").split("/")[-1]
            is_pr = "pull_request" in item
            output.append(
                {
                    "title": item.get("title", "Untitled"),
                    "url": url,
                    "updated_at": item.get("updated_at"),
                    "repo": repo,
                    "kind": "PR" if is_pr else "ISS",
                }
            )
            if len(output) >= max_items:
                break
        return output

    def _fetch_linear(self, token: str) -> list[dict[str, Any]]:
        max_items = int(self.config.get("linear_max_items", 100))
        headers = {"Authorization": token, "Content-Type": "application/json"}
        filter_mode = str(self.config.get("linear_filter", "assigned"))
        exclude_completed = bool(self.config.get("linear_exclude_completed", True))
        issue_filter: dict[str, Any] = {}
        if exclude_completed:
            issue_filter["state"] = {"type": {"neq": "completed"}}
        if filter_mode == "assigned_current_cycle":
            issue_filter["cycle"] = {"isActive": {"eq": True}}
        if not issue_filter:
            issue_filter = None

        query = """
        query AssignedIssues($first: Int!, $filter: IssueFilter) {
          viewer {
            assignedIssues(first: $first, filter: $filter) {
              nodes {
                title
                url
                createdAt
                dueDate
                state { name type }
                cycle { name }
              }
            }
          }
        }
        """
        nodes = self._fetch_linear_nodes(headers, query, max_items, issue_filter)
        if filter_mode == "assigned_current_cycle" and not nodes:
            fallback_filter = {"state": {"type": {"neq": "completed"}}} if exclude_completed else None
            nodes = self._fetch_linear_nodes(headers, query, max_items, fallback_filter)
        return [
            {
                "title": node.get("title", "Untitled"),
                "url": node.get("url"),
                "created_at": node.get("createdAt"),
                "due_date": node.get("dueDate"),
                "state": (node.get("state") or {}).get("name", ""),
                "cycle": (node.get("cycle") or {}).get("name", ""),
            }
            for node in nodes
        ]

    def _fetch_linear_nodes(
        self,
        headers: dict[str, str],
        query: str,
        max_items: int,
        issue_filter: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        response = requests.post(
            "https://api.linear.app/graphql",
            headers=headers,
            json={"query": query, "variables": {"first": max_items, "filter": issue_filter}},
            timeout=10,
        )
        if not response.ok:
            raise ValueError(f"Linear API {response.status_code}: {response.text[:120]}")
        payload = response.json()
        if payload.get("errors"):
            raise ValueError(f"Linear error: {payload['errors'][0].get('message', 'unknown')}")
        return (
            payload.get("data", {})
            .get("viewer", {})
            .get("assignedIssues", {})
            .get("nodes", [])
        )

    def _render_github(self, items: list[dict[str, Any]]) -> list[TileRenderItem]:
        rendered = []
        for item in items:
            date_value = item.get("updated_at")
            date_label = self._format_datetime(date_value)
            color = self._day_color(date_value)
            prefix = f"{date_label:<10}  {item.get('kind', 'ISS'):>3}  {item.get('repo', ''):<8}  "
            line = Text(prefix)
            line.stylize(color, 0, 10)
            line.append(item.get("title", "Untitled"))
            rendered.append(TileRenderItem(label=line, url=item.get("url")))
        return rendered

    def _render_linear(self, items: list[dict[str, Any]]) -> list[TileRenderItem]:
        rendered = []
        for item in items:
            date_value = item.get("due_date") or item.get("created_at")
            date_label = self._format_datetime(date_value)
            color = self._day_color(date_value)
            state = item.get("state", "")
            cycle = item.get("cycle", "")
            cycle_label = cycle[:8] if cycle else ""
            prefix = f"{date_label:<10}  {state[:8]:<8}  {cycle_label:<8}  "
            line = Text(prefix)
            line.stylize(color, 0, 10)
            line.append(item.get("title", "Untitled"))
            rendered.append(TileRenderItem(label=line, url=item.get("url")))
        return rendered

    @staticmethod
    def _format_datetime(value: str | None) -> str:
        if not value:
            return "--- --:--"
        try:
            if len(value) == 10:
                parsed = datetime.strptime(value, "%Y-%m-%d")
            else:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.astimezone(timezone.utc).strftime("%a %H:%M")
        except ValueError:
            return value[:10]

    @staticmethod
    def _day_color(value: str | None) -> str:
        if not value:
            return "white"
        try:
            if len(value) == 10:
                parsed = datetime.strptime(value, "%Y-%m-%d")
            else:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return "white"
        palette = ["cyan", "green", "yellow", "magenta", "blue", "bright_black", "white"]
        return palette[parsed.weekday() % len(palette)]
