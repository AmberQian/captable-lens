from pathlib import Path

from dilution_dashboard.market_data import MarketCapCache, resolve_market_caps


def test_manual_market_caps_override_cache(tmp_path: Path):
    manual = tmp_path / "manual.json"
    manual.write_text('{"AAOI": 12345}', encoding="utf-8")

    cache = MarketCapCache(tmp_path / "cache")
    cache.merge({"AAOI": 1, "IREN": 2})

    caps = resolve_market_caps(
        ["AAOI", "IREN"],
        manual_path=str(manual),
        provider="none",
        cache_dir=tmp_path / "cache",
    )

    assert caps == {"AAOI": 12345.0}


def test_cache_returns_fresh_values(tmp_path: Path):
    cache = MarketCapCache(tmp_path)
    cache.merge({"AAOI": 1_000_000_000})

    assert cache.read_fresh(max_age_seconds=60)["AAOI"] == 1_000_000_000

