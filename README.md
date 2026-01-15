# Term Dashboard

A terminal dashboard with stocks, news, weather, work items, and Obsidian search.

## Requirements

- Python 3.11+
- `ripgrep` for Obsidian search (`brew install ripgrep`)
- Optional: `w3m`, `lynx`, or `links` for terminal link opening

## Install

```bash
python3.11 -m pip install -r requirements.txt
```

## Run

```bash
PYTHONPATH=src python3.11 -m term_dashboard
```

## Environment (.env)

Create `.env` in the repo root using `.env.example` as a template:

```bash
GITHUB_TOKEN=your_github_token
LINEAR_TOKEN=your_linear_token
```

Both tokens are optional, but the Work tile will only populate when provided.

## Config files

Config files live in `config/` and are loaded by name (`tile_<name>.yml`).

### Global settings

`config/global_config.yml`

```yaml
refresh_interval_minutes: 5
layout:
  min_tile_width: 40
  max_columns: 3
  gap: 1
```

### Stocks

`config/tile_stocks.yml`

```yaml
tickers:
  - symbol: SPY
    units: 10
currency: USD
max_rows: 8
delta_periods:
  - 5d
  - 6mo
  - 1yr
```

### Hacker News

`config/tile_hackernews.yml`

```yaml
feed: top
limit: 10
open_links_in_terminal: false
```

### Financial Times

`config/tile_financial_times.yml`

```yaml
feed_url: "https://www.ft.com/..."
max_items: 10
open_links_in_terminal: false
auth:
  bearer_token: ""
  cookies: ""
```

### Weather

`config/tile_weather.yml`

```yaml
city: "Kraków, Poland"
units: metric
forecast_days: 5
```

### Work (GitHub + Linear)

`config/tile_work.yml`

```yaml
github_max_items: 8
linear_max_items: 8
linear_filter: assigned_current_cycle
open_links_in_terminal: false
# github_user: your-handle
```

`linear_filter` supports `assigned` or `assigned_current_cycle` (falls back to `assigned` if no active cycle).

### Obsidian Search

`config/tile_obsidian.yml`

```yaml
vault_paths:
  - /Users/jm/Documents/ML
  - /Users/jm/Documents/Simulations
max_results: 20
open_in_nvim: true
```

## Link behavior

- `open_links_in_terminal: true` tries `w3m`, `lynx`, or `links` and returns to the dashboard on exit.
- If no terminal browser is available, links open in your default browser.
- Obsidian results open in `nvim` (returns to dashboard on exit).
