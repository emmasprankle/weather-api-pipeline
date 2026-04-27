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


def test_missing_env_var_returns_none(monkeypatch):
    monkeypatch.delenv("WEATHER_API_KEY", raising=False)
    assert os.getenv("WEATHER_API_KEY") is None

