import time
from typing import Dict, Any, List
from src.telemetry.logger import logger

class PerformanceTracker:
    """
    Tracking industry-standard metrics for LLMs.
    """
    def __init__(self):
        self.session_metrics = []

    def track_request(self, provider: str, model: str, usage: Dict[str, int], latency_ms: int):
        """
        Logs a single request metric to our telemetry.
        """
        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency_ms": latency_ms,
            "cost_estimate": self._calculate_cost(model, usage) # Mock cost calculation
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)

    # Giá tham khảo (USD trên 1 TRIỆU token) — (input, output). Cập nhật 2026.
    # Lưu ý xếp biến thể "-lite"/"-mini" TRƯỚC bản thường vì khớp theo substring.
    _PRICING = {
        "gemini-2.5-flash-lite": (0.10, 0.40),
        "gemini-2.5-flash":      (0.30, 2.50),
        "gemini-2.5-pro":        (1.25, 10.00),
        "gemini-2.0-flash-lite": (0.075, 0.30),
        "gemini-2.0-flash":      (0.10, 0.40),
        "gpt-4o-mini":           (0.15, 0.60),
        "gpt-4o":                (2.50, 10.00),
    }
    _DEFAULT_PRICE = (0.30, 2.50)  # mặc định theo gemini-2.5-flash

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """Ước tính chi phí (USD) dựa trên bảng giá input/output theo từng model."""
        model_key = (model or "").lower()
        price_in, price_out = self._DEFAULT_PRICE
        for key, rates in self._PRICING.items():
            if key in model_key:
                price_in, price_out = rates
                break

        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        cost = (prompt_tokens / 1_000_000) * price_in + (completion_tokens / 1_000_000) * price_out
        return round(cost, 6)

# Global tracker instance
tracker = PerformanceTracker()
