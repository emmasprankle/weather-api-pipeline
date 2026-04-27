# Weather Schedule Design

**Date:** 2026-04-27
**Status:** Approved

## Overview

Automate the daily execution of `weather.py` using GitHub Actions, appending each run's forecast data to a growing `weather_data.csv` committed back to the repository.

## Architecture

Two components:

1. **`weather.py` (modified)** — reads the API key from the `WEATHERAPI_KEY` environment variable instead of a hardcoded string. Adds a `run_date` column to each row. On save, checks if `weather_data.csv` already exists; if so, reads it and concatenates new rows before writing. If not, writes fresh.

2. **`.github/workflows/weather_schedule.yml` (new)** — GitHub Actions workflow that triggers daily at noon UTC and on manual dispatch. Checks out the repo, sets up Python 3.12, installs dependencies, runs `weather.py`, then commits and pushes the updated CSV if changes are detected.

## Data Flow

1. GitHub Actions triggers at `0 12 * * *` (noon UTC)
2. Repo checked out — includes latest `weather_data.csv` from prior run
3. `weather.py` runs — fetches 3-day forecasts for 20 zip codes, appends 60 new rows with today's `run_date`
4. Script checks for existing CSV → concatenates if present, writes fresh if not
5. Workflow runs `git diff` — commits and pushes if CSV changed (`chore: daily weather update YYYY-MM-DD`)
6. On API failure, script exits non-zero → Actions run marked failed → GitHub notifies repo watchers

The CSV grows by ~60 rows/day (~22,000 rows after one year), remaining fast to read with pandas.

## GitHub Actions Workflow

```yaml
# .github/workflows/weather_schedule.yml
on:
  schedule:
    - cron: '0 12 * * *'
  workflow_dispatch:

jobs:
  fetch-weather:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install requests pandas
      - run: python weather.py
        env:
          WEATHERAPI_KEY: ${{ secrets.WEATHERAPI_KEY }}
      - run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add weather_data.csv
          git diff --cached --quiet || git commit -m "chore: daily weather update $(date -u +%Y-%m-%d)" && git push
```

## weather.py Changes

- Replace hardcoded `API_KEY` with `os.environ["WEATHERAPI_KEY"]`
- Add `run_date` column (today's date) to each result row
- On CSV save: if file exists, read → concat → write; otherwise write fresh

## Secrets Setup

| Secret name      | Where to add                                      | Value          |
|------------------|---------------------------------------------------|----------------|
| `WEATHERAPI_KEY` | GitHub repo → Settings → Secrets → Actions       | Your API key   |

## Error Handling

- API errors or missing env var cause a non-zero exit → Actions run marked failed
- GitHub sends default failure email to repo watchers
- No partial writes: the CSV is only updated after all 20 cities fetch successfully
