import os
import re
import time
import warnings

# Tắt FutureWarning deprecation của google.generativeai / google.api_core — không
# actionable lúc này (xem mục migrate sang google.genai ở cuối). Phải đặt TRƯỚC import genai.
warnings.filterwarnings("ignore", category=FutureWarning)

import google.generativeai as genai
from typing import Dict, Any, Optional, Generator
from src.core.llm_provider import LLMProvider

# Free tier Gemini giới hạn ~5 request/phút → agent nhiều bước dễ dính 429.
# Tự động chờ và thử lại để demo/eval không vỡ giữa chừng.
_MAX_RETRIES = 5
_MAX_BACKOFF_SECONDS = 65


class GeminiProvider(LLMProvider):
    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        super().__init__(model_name, api_key)
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    def _generate_with_retry(self, full_prompt: str):
        """Gọi generate_content, tự backoff khi gặp 429/quota (rate limit)."""
        delay = 2.0
        for attempt in range(_MAX_RETRIES):
            try:
                return self.model.generate_content(full_prompt)
            except Exception as exc:  # noqa: BLE001
                msg = str(exc)
                is_rate_limit = (
                    "429" in msg
                    or "quota" in msg.lower()
                    or "exhausted" in msg.lower()
                    or "rate limit" in msg.lower()
                )
                if not is_rate_limit or attempt == _MAX_RETRIES - 1:
                    raise
                # Ưu tiên retry_delay do API gợi ý, nếu không có thì exponential backoff.
                hint = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", msg)
                wait = (int(hint.group(1)) + 1) if hint else delay
                wait = min(wait, _MAX_BACKOFF_SECONDS)
                time.sleep(wait)
                delay = min(delay * 2, _MAX_BACKOFF_SECONDS)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()

        # In Gemini, system instruction is passed during model initialization or as a prefix
        # For simplicity in this lab, we'll prepend it if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        response = self._generate_with_retry(full_prompt)

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        # Gemini usage data is in response.usage_metadata
        content = response.text
        usage = {
            "prompt_tokens": response.usage_metadata.prompt_token_count,
            "completion_tokens": response.usage_metadata.candidates_token_count,
            "total_tokens": response.usage_metadata.total_token_count
        }

        return {
            "content": content,
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": "google"
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        response = self.model.generate_content(full_prompt, stream=True)
        for chunk in response:
            yield chunk.text
