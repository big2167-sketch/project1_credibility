"""
Unit tests for Deliverable 1.

We test:
- invalid input handling
- output format consistency
- score range [0,1]
"""
from src.scorer import score_source

def test_invalid_url_returns_zeroish_score():
    out = score_source("not a url")
    assert isinstance(out, dict)
    assert "score" in out and "explanation" in out
    assert 0.0 <= out["score"] <= 1.0
    assert out["score"] == 0.0

def test_valid_url_output_format():
    out = score_source("https://example.com")
    assert isinstance(out, dict)
    assert "score" in out and "explanation" in out
    assert isinstance(out["score"], float)
    assert isinstance(out["explanation"], str)
    assert 0.0 <= out["score"] <= 1.0

def test_https_bonus_does_not_crash():
    out = score_source("example.com")
    assert "score" in out and "explanation" in out
    assert 0.0 <= out["score"] <= 1.0