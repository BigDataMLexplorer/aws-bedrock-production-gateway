from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class CircuitState:
    failures: int = 0
    opened_at: float | None = None


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 20.0):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._state: dict[str, CircuitState] = {}

    def is_open(self, key: str) -> bool:
        state = self._state.setdefault(key, CircuitState())
        if state.opened_at is None:
            return False
        if time.monotonic() - state.opened_at >= self.cooldown_seconds:
            state.failures = 0
            state.opened_at = None
            return False
        return True

    def record_success(self, key: str) -> None:
        self._state[key] = CircuitState()

    def record_failure(self, key: str) -> bool:
        state = self._state.setdefault(key, CircuitState())
        state.failures += 1
        if state.failures >= self.failure_threshold and state.opened_at is None:
            state.opened_at = time.monotonic()
            return True
        return False
