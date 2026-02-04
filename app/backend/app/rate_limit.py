import time
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
    def __init__(self, capacity: int, refill_per_sec: float) -> None:
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self._buckets: Dict[str, Bucket] = {}

    def check(self, key: str) -> bool:
        bucket = self._buckets.get(key)
        if not bucket:
            bucket = Bucket(
                capacity=self.capacity,
                refill_per_sec=self.refill_per_sec,
                tokens=self.capacity,
                last_refill=time.time(),
            )
            self._buckets[key] = bucket
        return bucket.allow()

