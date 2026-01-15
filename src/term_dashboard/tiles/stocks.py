from __future__ import annotations

from typing import Any

import yfinance as yf
from rich.text import Text

from term_dashboard.tiles.base import BaseTile


class StocksTile(BaseTile):
    tile_name = "stocks"
    title = "Stocks"

    def fetch_data(self) -> dict[str, Any]:
        tickers_config = self.config.get("tickers", [])
        symbols = [item.get("symbol") for item in tickers_config if item.get("symbol")]
        if not symbols:
            return {"rows": [], "currency": self.config.get("currency", "USD")}

        tickers = yf.Tickers(" ".join(symbols))
        rows = []
        units_map = {item.get("symbol"): float(item.get("units", 0)) for item in tickers_config}
        delta_periods = self._normalize_periods(self.config.get("delta_periods"))
        sparkline_period = str(self.config.get("sparkline_period", delta_periods[0]))
        for symbol in symbols:
            ticker = tickers.tickers.get(symbol)
            price = None
            history_values: list[float] = []
            changes: dict[str, float | None] = {}
            if ticker is not None:
                info = getattr(ticker, "fast_info", {}) or {}
                price = info.get("last_price")
                if price is None:
                    price = (ticker.info or {}).get("regularMarketPrice")
                history_cache: dict[str, list[float]] = {}
                for period in delta_periods:
                    normalized_period = self._normalize_period(period)
                    interval = str(
                        self.config.get(
                            "history_interval", self._interval_for_period(normalized_period)
                        )
                    )
                    history = ticker.history(period=normalized_period, interval=interval)
                    if not history.empty and "Close" in history:
                        values = [float(val) for val in history["Close"].tolist()]
                        history_cache[period] = values
                        if len(values) >= 2:
                            changes[period] = values[-1] - values[0]
                        else:
                            changes[period] = None
                    else:
                        history_cache[period] = []
                        changes[period] = None
                history_values = history_cache.get(sparkline_period, [])
            units = units_map.get(symbol, 0)
            value = price * units if price is not None else None
            rows.append(
                {
                    "symbol": symbol,
                    "price": price,
                    "units": units,
                    "value": value,
                    "history": history_values,
                    "changes": changes,
                }
            )
        return {
            "rows": rows,
            "currency": self.config.get("currency", "USD"),
            "delta_periods": delta_periods,
        }

    def render_data(self, data: dict[str, Any]) -> None:
        rows = data.get("rows", [])
        max_rows = int(self.config.get("max_rows", len(rows)))
        currency = data.get("currency", "USD")
        delta_periods = data.get("delta_periods", ["5d"])
        delta_header = "".join([f"{('Δ' + period):>9}" for period in delta_periods])
        header = (
            f"{'Symbol':<6}{'Price':>10}{'Units':>7}{'Value':>11}"
            f"{delta_header}  {'Trend':<5}"
        )
        output = Text(header, style="bold #e6edf3")
        for row in rows[:max_rows]:
            price = self._format_money(row.get("price"), currency)
            value = self._format_money(row.get("value"), currency)
            units = row.get("units", 0)
            changes = row.get("changes", {})
            prefix = f"{row.get('symbol', ''):<6}{price:>10}{units:>7.2f}{value:>11}"
            line = Text(prefix)
            line.stylize("cyan", 0, len(row.get("symbol", "")))
            for period in delta_periods:
                change = changes.get(period)
                change_label = "—" if change is None else f"{change:+.2f}"
                change_field = f"{change_label:>9}"
                start = len(line)
                line.append(change_field)
                if change is not None:
                    color = "green" if change >= 0 else "red"
                    line.stylize(color, start, start + len(change_field))
            line.append("  ")
            sparkline = self._sparkline(row.get("history", []), changes.get(delta_periods[0]))
            line.append(sparkline)
            output.append("\n")
            output.append(line)
        if self.body:
            self.body.update(output)

    @staticmethod
    def _format_money(value: float | None, currency: str) -> str:
        if value is None:
            return "—"
        if currency.upper() == "USD":
            return f"${value:,.2f}"
        return f"{value:,.2f} {currency.upper()}"

    @staticmethod
    def _sparkline(values: list[float], change: float | None) -> Text:
        if not values:
            return Text("—", style="dim")
        blocks = "▁▂▃▄▅▆▇█"
        low = min(values)
        high = max(values)
        span = high - low
        chars = []
        for value in values:
            if span == 0:
                index = len(blocks) // 2
            else:
                index = int((value - low) / span * (len(blocks) - 1))
            chars.append(blocks[index])
        color = "green" if (change or 0) >= 0 else "red"
        return Text("".join(chars), style=color)

    @staticmethod
    def _interval_for_period(period: str) -> str:
        mapping = {
            "5d": "1d",
            "1mo": "1d",
            "3mo": "1wk",
            "6mo": "1wk",
            "1y": "1mo",
            "1yr": "1mo",
            "2y": "1mo",
            "5y": "1mo",
        }
        return mapping.get(period, "1d")

    @staticmethod
    def _normalize_periods(value: Any) -> list[str]:
        if isinstance(value, list) and value:
            return [str(item) for item in value]
        if isinstance(value, str) and value:
            return [value]
        return ["5d", "6mo", "1yr"]

    @staticmethod
    def _normalize_period(period: str) -> str:
        if period == "1yr":
            return "1y"
        return period
