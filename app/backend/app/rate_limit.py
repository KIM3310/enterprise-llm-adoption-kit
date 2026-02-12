import time
import threading
from dataclasses import dataclass
from typing import Dict


@dataclass
class Bucket:
    capacity: int
    refill_per_sec: float
    tokens: float
    last_refill: float

    def allow(self) -> bool:
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)
        self.last_refill = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class RateLimiter:
    def __init__(
        self,
        capacity: int,
        refill_per_sec: float,
        cleanup_every: int = 500,
        bucket_ttl_sec: float = 600.0,
    ) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        if refill_per_sec <= 0:
            raise ValueError("refill_per_sec must be > 0")
        if cleanup_every <= 0:
            raise ValueError("cleanup_every must be > 0")
        if bucket_ttl_sec <= 0:
            raise ValueError("bucket_ttl_sec must be > 0")
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.cleanup_every = cleanup_every
        self.bucket_ttl_sec = bucket_ttl_sec
        self._buckets: Dict[str, Bucket] = {}
        self._lock = threading.Lock()
        self._checks = 0

    def check(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            self._checks += 1
            if self._checks % self.cleanup_every == 0:
                self._cleanup(now)

            bucket = self._buckets.get(key)
            if not bucket:
                bucket = Bucket(
                    capacity=self.capacity,
                    refill_per_sec=self.refill_per_sec,
                    tokens=self.capacity,
                    last_refill=now,
                )
                self._buckets[key] = bucket
            return bucket.allow()

    def _cleanup(self, now: float) -> None:
        stale_keys = [
            key
            for key, bucket in self._buckets.items()
            if (now - bucket.last_refill) > self.bucket_ttl_sec
        ]
        for key in stale_keys:
            self._buckets.pop(key, None)
