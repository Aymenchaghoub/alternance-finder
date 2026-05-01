"""
Rate limiter simple pour les requêtes réseau.
"""

import time


class RateLimiter:
    """Limite le débit d'exécution à N appels par période."""

    def __init__(self, max_calls: int = 20, period_seconds: float = 86400):
        self.max_calls = max_calls
        self.period = period_seconds
        self.calls: list[float] = []

    def wait_if_needed(self):
        """Bloque si la limite est atteinte."""
        now = time.time()
        # Nettoyer les appels expirés
        self.calls = [t for t in self.calls if now - t < self.period]

        if len(self.calls) >= self.max_calls:
            wait_time = self.period - (now - self.calls[0])
            if wait_time > 0:
                raise RateLimitExceeded(
                    f"Limite atteinte ({self.max_calls} appels / "
                    f"{self.period:.0f}s). Réessayer dans {wait_time:.0f}s."
                )

        self.calls.append(now)

    @property
    def remaining(self) -> int:
        """Nombre d'appels restants dans la période."""
        now = time.time()
        self.calls = [t for t in self.calls if now - t < self.period]
        return max(0, self.max_calls - len(self.calls))


class RateLimitExceeded(Exception):
    """Levée quand la limite de débit est dépassée."""
    pass
