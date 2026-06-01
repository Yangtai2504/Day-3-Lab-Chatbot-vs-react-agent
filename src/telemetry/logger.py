import logging
import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

class IndustryLogger:
    """
    Structured logger that simulates industry practices.
    Logs to console, a daily file, and a per-session file — tất cả ở dạng JSON.

    Mỗi tiến trình mở một "session" (1 phiên làm việc) với session_id riêng. Mọi
    event đều gắn session_id và được ghi đồng thời vào:
      - logs/YYYY-MM-DD.log            (log tổng theo ngày)
      - logs/sessions/<session_id>.log (log riêng từng phiên — dễ tách để phân tích)
    """
    def __init__(self, name: str = "AI-Lab-Agent", log_dir: str = "logs",
                 session_id: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        self.log_dir = log_dir
        self.session_dir = os.path.join(log_dir, "sessions")
        os.makedirs(self.session_dir, exist_ok=True)

        # File Handler theo ngày (JSON) — luôn bật.
        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
        file_handler = logging.FileHandler(log_file)

        # Console Handler.
        console_handler = logging.StreamHandler()

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # Handler riêng cho session — gắn trong set_session().
        self._session_handler: Optional[logging.FileHandler] = None
        self.session_id = ""
        self.set_session(session_id or self._new_session_id())

    # ── Session management ────────────────────────────────────────────────────
    @staticmethod
    def _new_session_id() -> str:
        return datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]

    def set_session(self, session_id: str) -> str:
        """Bắt đầu / chuyển sang một session: mọi log sau đó gắn session_id này và
        được ghi thêm vào logs/sessions/<session_id>.log."""
        self.session_id = session_id

        # Gỡ handler session cũ (nếu có) để không ghi lẫn sang file phiên trước.
        if self._session_handler is not None:
            self.logger.removeHandler(self._session_handler)
            self._session_handler.close()

        self._session_handler = logging.FileHandler(
            os.path.join(self.session_dir, f"{session_id}.log")
        )
        self.logger.addHandler(self._session_handler)
        return session_id

    def new_session(self) -> str:
        """Tạo session_id mới và kích hoạt. Trả về id để caller lưu lại."""
        return self.set_session(self._new_session_id())

    # ── Logging ───────────────────────────────────────────────────────────────
    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Logs an event with a timestamp, session id and type."""
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": self.session_id,
            "event": event_type,
            "data": data
        }
        self.logger.info(json.dumps(payload))

    def info(self, msg: str):
        self.logger.info(msg)

    def error(self, msg: str, exc_info=True):
        self.logger.error(msg, exc_info=exc_info)

# Global logger instance
logger = IndustryLogger()
