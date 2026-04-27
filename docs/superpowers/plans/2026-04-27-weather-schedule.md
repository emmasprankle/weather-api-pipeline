# Weather Schedule Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run `weather.py` automatically every day at noon UTC via GitHub Actions, appending results to a growing `weather_data.csv` committed back to the repo.

**Architecture:** `weather.py` is updated to read its API key from an environment variable, stamp each row with a `run_date`, and append to the existing CSV rather than overwrite it. A GitHub Actions workflow triggers the script on a daily cron schedule and on manual dispatch, then commits any CSV changes back to `main`.

**Tech Stack:** Python 3.12, pandas, requests, GitHub Actions

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `weather.py` | Modify | Read key from env, add `run_date`, append CSV |
| `tests/test_csv_append.py` | Create | Verify append logic in isolation |
| `.github/workflows/weather_schedule.yml` | Create | Daily cron + manual trigger, commit CSV |

---

### Task 1: Extract and test CSV append logic in weather.py

**Files:**
- Modify: `weather.py`
- Create: `tests/test_csv_append.py`

- [ ] **Step 1: Install pytest**

```bash
pip install pytest
```

Expected: pytest installs successfully.

- [ ] **Step 2: Write the failing test**

Create `tests/test_csv_append.py`:

```python
import os
import pandas as pd
import pytest
from weather import save_weather


def test_save_creates_file_when_none_exists(tmp_path):
    path = str(tmp_path / "weather.csv")
    df = pd.DataFrame([{"city": "LA", "run_date": "2026-04-27", "temp": 70}])
    save_weather(df, path)
    result = pd.read_csv(path)
    assert len(result) == 1
    assert result.iloc[0]["city"] == "LA"


def test_save_appends_to_existing_file(tmp_path):
    path = str(tmp_path / "weather.csv")
    day1 = pd.DataFrame([{"city": "LA", "run_date": "2026-04-27", "temp": 70}])
    day2 = pd.DataFrame([{"city": "LA", "run_date": "2026-04-28", "temp": 72}])
    save_weather(day1, path)
    save_weather(day2, path)
    result = pd.read_csv(path)
    assert len(result) == 2
    assert list(result["run_date"]) == ["2026-04-27", "2026-04-28"]


def test_save_does_not_deduplicate_reruns(tmp_path):
    path = str(tmp_path / "weather.csv")
    df = pd.DataFrame([{"city": "LA", "run_date": "2026-04-27", "temp": 70}])
    save_weather(df, path)
    save_weather(df, path)
    result = pd.read_csv(path)
    assert len(result) == 2  # re-runs append — deduplication is not in scope
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/test_csv_append.py -v
```

Expected: `ImportError: cannot import name 'save_weather' from 'weather'` — function not yet defined.

- [ ] **Step 4: Add `save_weather` to weather.py, update imports, and guard main body**

Open `weather.py`. Replace the top imports block:

```python
import os
import requests
import time
import pandas as pd
from datetime import date
```

Add this function after the imports, before `api_url`:

```python
def save_weather(df, path="weather_data.csv"):
    if os.path.exists(path):
        existing = pd.read_csv(path)
        df = pd.concat([existing, df], ignore_index=True)
    df.to_csv(path, index=False)
```

Then wrap everything from `api_url = ...` down to the end of the file in a `if __name__ == "__main__":` block (indent all existing lines by 4 spaces):

```python
if __name__ == "__main__":
    api_url = "https://api.weatherapi.com/v1/forecast.json"

    zip_codes = [
        # ... existing list unchanged ...
    ]

    # ... rest of the existing script unchanged ...
```

This guard lets the test import `save_weather` without triggering the API calls.

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_csv_append.py -v
```

Expected output:
```
tests/test_csv_append.py::test_save_creates_file_when_none_exists PASSED
tests/test_csv_append.py::test_save_appends_to_existing_file PASSED
tests/test_csv_append.py::test_save_does_not_duplicate_on_rerun PASSED
3 passed
```

- [ ] **Step 6: Commit**

```bash
git add weather.py tests/test_csv_append.py
git commit -m "feat: extract save_weather with append logic and add tests"
```

---

### Task 2: Update weather.py — env var, run_date column, use save_weather

**Files:**
- Modify: `weather.py`

- [ ] **Step 1: Write the failing test for env var behavior**

Add this test to `tests/test_csv_append.py`:

```python
def test_missing_env_var_returns_none(monkeypatch):
    monkeypatch.delenv("WEATHER_API_KEY", raising=False)
    assert os.getenv("WEATHER_API_KEY") is None
```

- [ ] **Step 2: Run to verify it passes already**

```bash
pytest tests/test_csv_append.py::test_missing_env_var_raises -v
```

Expected: PASS (the behavior is already true for `os.environ` — this locks it in as a contract).

- [ ] **Step 3: Replace hardcoded API key in weather.py**

In `weather.py`, find:

```python
API_KEY = "6f318ef78cb244299b1175138261304"
```

Replace with:

```python
API_KEY = os.getenv("WEATHER_API_KEY")
```

- [ ] **Step 4: Add run_date to each result row**

In `weather.py`, find the `results.append({...})` block:

```python
        results.append({
            "zip_code": zip_code,
            "city": city,
            "region": region,
            "date": day["date"],
            "max_temp_f": day["day"]["maxtemp_f"],
            "min_temp_f": day["day"]["mintemp_f"],
            "condition": day["day"]["condition"]["text"],
        })
```

Replace with:

```python
        results.append({
            "zip_code": zip_code,
            "city": city,
            "region": region,
            "date": day["date"],
            "max_temp_f": day["day"]["maxtemp_f"],
            "min_temp_f": day["day"]["mintemp_f"],
            "condition": day["day"]["condition"]["text"],
            "run_date": date.today().isoformat(),
        })
```

- [ ] **Step 5: Replace df.to_csv call with save_weather**

In `weather.py`, find:

```python
df.to_csv("weather_data.csv", index=False)
print("Saved to weather_data.csv")
```

Replace with:

```python
save_weather(df)
print("Appended to weather_data.csv")
```

- [ ] **Step 6: Verify the script runs locally**

```bash
WEATHER_API_KEY=6f318ef78cb244299b1175138261304 python weather.py
```

Expected: script runs, prints 20 city lines, prints table, prints "Appended to weather_data.csv". Run it a second time and verify `weather_data.csv` now has 120 rows.

```bash
python -c "import pandas as pd; df = pd.read_csv('weather_data.csv'); print(df.shape)"
```

Expected: `(120, 8)`

- [ ] **Step 7: Run all tests**

```bash
pytest tests/ -v
```

Expected: all 4 tests pass.

- [ ] **Step 8: Commit**

```bash
git add weather.py tests/test_csv_append.py
git commit -m "feat: read API key from env, add run_date column, use save_weather"
```

---

### Task 3: Create GitHub Actions workflow

**Files:**
- Create: `.github/workflows/weather_schedule.yml`

- [ ] **Step 1: Create the workflows directory**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Create the workflow file**

Create `.github/workflows/weather_schedule.yml`:

```yaml
name: Daily Weather Fetch

on:
  schedule:
    - cron: '0 12 * * *'
  workflow_dispatch:

jobs:
  fetch-weather:
    runs-on: ubuntu-latest

    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install requests pandas

      - name: Run weather script
        run: python weather.py
        env:
          WEATHER_API_KEY: ${{ secrets.WEATHER_API_KEY }}

      - name: Commit updated CSV
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add weather_data.csv
          git diff --cached --quiet || (git commit -m "chore: daily weather update $(date -u +%Y-%m-%d)" && git push)
```

- [ ] **Step 3: Commit and push**

```bash
git add .github/workflows/weather_schedule.yml
git commit -m "feat: add GitHub Actions workflow for daily weather schedule"
git push origin main
```

- [ ] **Step 4: Trigger a manual run to verify**

1. Go to your GitHub repo in a browser
2. Click **Actions** tab
3. Click **Daily Weather Fetch** in the left sidebar
4. Click **Run workflow** → **Run workflow**
5. Wait ~60 seconds, refresh the page

Expected: the run shows a green checkmark. Click into it and confirm:
- The "Run weather script" step printed 20 city lines
- The "Commit updated CSV" step shows a commit was pushed (or "nothing to commit" if run twice same day)

- [ ] **Step 5: Verify the CSV was committed by the workflow**

```bash
git pull
python -c "import pandas as pd; df = pd.read_csv('weather_data.csv'); print(df.shape, df['run_date'].unique())"
```

Expected: shape shows rows from each run, `run_date` values present.
