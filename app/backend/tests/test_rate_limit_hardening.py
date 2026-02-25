import pytest

import app.rate_limit as rate_limit_module
from app.rate_limit import RateLimiter


def test_rate_limiter_rejects_invalid_init_values() -> None:
    with pytest.raises(ValueError):
        RateLimiter(capacity=0, refill_per_sec=1.0)
    with pytest.raises(ValueError):
        RateLimiter(capacity=1, refill_per_sec=0.0)
    with pytest.raises(ValueError):
        RateLimiter(capacity=1, refill_per_sec=1.0, cleanup_every=0)
    with pytest.raises(ValueError):
        RateLimiter(capacity=1, refill_per_sec=1.0, bucket_ttl_sec=0)


def test_rate_limiter_cleans_up_stale_buckets(monkeypatch) -> None:
    state = {"now": 1000.0}

    def _fake_time() -> float:
        return state["now"]

    monkeypatch.setattr(rate_limit_module.time, "time", _fake_time)

    limiter = RateLimiter(
        capacity=1,
        refill_per_sec=1.0,
        cleanup_every=1,
        bucket_ttl_sec=10.0,
    )
    assert limiter.check("user-a") is True
    assert "user-a" in limiter._buckets

    state["now"] = 1015.0
    assert limiter.check("user-b") is True
    assert "user-a" not in limiter._buckets
    assert "user-b" in limiter._buckets
