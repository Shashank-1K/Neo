"""
API Key Manager - Intelligent round-robin load balancing with health tracking
"""
import time
import asyncio
from typing import Optional, Dict
from dataclasses import dataclass, field
from config import settings
import logging

logger = logging.getLogger(__name__)


@dataclass
class KeyHealth:
    key: str
    total_requests: int = 0
    failed_requests: int = 0
    rate_limited_until: float = 0.0
    last_used: float = 0.0
    consecutive_failures: int = 0
    is_disabled: bool = False

    @property
    def is_available(self) -> bool:
        if self.is_disabled:
            return False
        if self.rate_limited_until > time.time():
            return False
        return True

    @property
    def failure_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests


class APIKeyManager:
    """
    Manages multiple Groq API keys with:
    - Round-robin rotation
    - Health tracking per key
    - Automatic backoff on rate limits
    - Workload isolation (different keys for different tasks)
    """

    def __init__(self):
        self.keys: Dict[str, KeyHealth] = {}
        self._current_index = 0
        self._lock = asyncio.Lock()

        # Initialize all keys
        for key in settings.GROQ_API_KEYS:
            self.keys[key] = KeyHealth(key=key)

        # Workload isolation mapping
        self._workload_mapping: Dict[str, int] = {
            "chat": 0,
            "voice": 1,
            "vision": 2,
            "compound": 3,
            "safety": 4,
            "batch": 5,
        }

        logger.info(f"APIKeyManager initialized with {len(self.keys)} keys")

    async def get_key(self, workload: str = "chat") -> str:
        """Get the next available API key for a workload"""
        async with self._lock:
            keys_list = list(self.keys.values())
            num_keys = len(keys_list)

            # Try workload-specific key first
            if workload in self._workload_mapping:
                preferred_idx = self._workload_mapping[workload] % num_keys
                preferred_key = keys_list[preferred_idx]
                if preferred_key.is_available:
                    preferred_key.total_requests += 1
                    preferred_key.last_used = time.time()
                    return preferred_key.key

            # Fall back to round-robin
            for _ in range(num_keys):
                key_health = keys_list[self._current_index % num_keys]
                self._current_index = (self._current_index + 1) % num_keys

                if key_health.is_available:
                    key_health.total_requests += 1
                    key_health.last_used = time.time()
                    return key_health.key

            # All keys exhausted — find the one with shortest cooldown
            soonest = min(keys_list, key=lambda k: k.rate_limited_until)
            wait_time = max(0, soonest.rate_limited_until - time.time())
            if wait_time > 0:
                logger.warning(f"All keys rate-limited. Waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
            soonest.total_requests += 1
            soonest.last_used = time.time()
            return soonest.key

    async def report_success(self, key: str):
        """Report successful use of a key"""
        if key in self.keys:
            self.keys[key].consecutive_failures = 0

    async def report_failure(self, key: str, is_rate_limit: bool = False):
        """Report a failure for a key"""
        if key not in self.keys:
            return

        health = self.keys[key]
        health.failed_requests += 1
        health.consecutive_failures += 1

        if is_rate_limit:
            # Exponential backoff: 10s, 20s, 40s, 80s, max 300s
            backoff = min(10 * (2 ** (health.consecutive_failures - 1)), 300)
            health.rate_limited_until = time.time() + backoff
            logger.warning(
                f"Key {key[:20]}... rate limited. Backing off {backoff}s"
            )

        if health.consecutive_failures >= 10:
            health.is_disabled = True
            logger.error(f"Key {key[:20]}... disabled after 10 consecutive failures")

    def get_stats(self) -> list:
        """Get health stats for all keys"""
        return [
            {
                "key_prefix": kh.key[:20] + "...",
                "total_requests": kh.total_requests,
                "failed_requests": kh.failed_requests,
                "failure_rate": f"{kh.failure_rate:.1%}",
                "is_available": kh.is_available,
                "consecutive_failures": kh.consecutive_failures,
            }
            for kh in self.keys.values()
        ]


# Singleton
key_manager = APIKeyManager()