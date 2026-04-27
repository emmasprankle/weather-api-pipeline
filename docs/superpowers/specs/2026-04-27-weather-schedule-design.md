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

## Run Cadence

| Trigger type | Schedule               | Notes                                      |
|--------------|------------------------|--------------------------------------------|
| Scheduled    | Daily at 12:00 UTC     | Cron expression: `0 12 * * *`              |
| Manual       | On demand              | Via `workflow_dispatch` in the Actions tab |

GitHub Actions may delay scheduled runs by up to a few minutes under high load — this is expected and acceptable.

## Manual vs. Scheduled Triggers

**Scheduled trigger** (`schedule`) fires automatically every day at noon UTC. It is the normal production path and requires no human action once the workflow is merged.

**Manual trigger** (`workflow_dispatch`) allows anyone with repo write access to run the workflow on demand from the Actions tab. Use cases: backfilling a missed day, testing after a code change, or verifying the secret is configured correctly. Manual runs behave identically to scheduled runs — same script, same append logic, same commit step.

## Success Criteria

A run is considered successful when all of the following are true:

1. `weather.py` exits with code 0 (all 20 zip code requests returned valid forecast data)
2. `weather_data.csv` has been updated with exactly 60 new rows (20 cities × 3 forecast days)
3. The updated CSV has been committed and pushed to `main` with a `chore: daily weather update YYYY-MM-DD` message

If the CSV already contains today's `run_date` (e.g., a manual re-run on the same day), `git diff` will detect no change and no commit is made — this is also a success.

## Failure Handling

| Failure cause                  | Behavior                                                        |
|--------------------------------|-----------------------------------------------------------------|
| API key missing or invalid     | `os.environ["WEATHERAPI_KEY"]` raises `KeyError` → non-zero exit |
| WeatherAPI returns error JSON  | `data["forecast"]` raises `KeyError` → non-zero exit            |
| Network timeout                | `requests.get` raises exception → non-zero exit                 |
| Git push fails                 | Workflow step fails → non-zero exit                             |

In all cases: the CSV is **not written** (failure happens before or instead of the write step), the Actions run is marked **failed**, and GitHub emails the default failure notification to repository watchers. No alerting beyond that is configured — check the Actions tab if data stops updating.

## Credentials

| Secret name      | Where it lives                                          | How it's used                                      |
|------------------|---------------------------------------------------------|----------------------------------------------------|
| `WEATHERAPI_KEY` | GitHub repo → Settings → Secrets and variables → Actions | Injected as `WEATHERAPI_KEY` env var at runtime   |

The key is **never** stored in code or committed to the repo. `weather.py` reads it exclusively via `os.environ["WEATHERAPI_KEY"]`. The secret is only visible to Actions runs on the `main` branch — it cannot be read from pull requests opened by forks.
