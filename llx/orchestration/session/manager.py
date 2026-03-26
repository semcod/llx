"""
Session Manager — core session lifecycle and state management.
Extracted from the monolithic session_manager.py.
"""

import json
import time
import uuid
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

from .models import SessionType, SessionStatus, SessionConfig, SessionState


class SessionManager:
    """Manages multiple sessions with intelligent scheduling and rate limiting."""

    def __init__(self, config_file: str = None):
        self.project_root = Path.cwd()
        self.config_file = config_file or self.project_root / "orchestration" / "sessions.json"
        self.sessions: Dict[str, SessionConfig] = {}
        self.session_states: Dict[str, SessionState] = {}
        self.request_queue: List = []
        self.lock = threading.RLock()

        # Load existing sessions
        self.load_sessions()

        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()

    # ── Config persistence ──────────────────────────────────

    def load_sessions(self) -> bool:
        """Load sessions from configuration file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    data = json.load(f)

                for session_data in data.get("sessions", []):
                    config = SessionConfig(
                        session_id=session_data["session_id"],
                        session_type=SessionType(session_data["session_type"]),
                        provider=session_data["provider"],
                        model=session_data["model"],
                        account=session_data["account"],
                        max_requests_per_hour=session_data.get("max_requests_per_hour", 100),
                        max_tokens_per_hour=session_data.get("max_tokens_per_hour", 100000),
                        cooldown_minutes=session_data.get("cooldown_minutes", 60),
                        priority=session_data.get("priority", 1),
                        metadata=session_data.get("metadata", {}),
                    )
                    self.sessions[config.session_id] = config

                    state_data = data.get("states", {}).get(config.session_id, {})
                    state = SessionState(
                        session_id=config.session_id,
                        status=SessionStatus(state_data.get("status", "idle")),
                        created_at=datetime.fromisoformat(
                            state_data.get("created_at", datetime.now().isoformat())
                        ),
                        last_used=datetime.fromisoformat(
                            state_data.get("last_used", datetime.now().isoformat())
                        ),
                        requests_count=state_data.get("requests_count", 0),
                        tokens_used=state_data.get("tokens_used", 0),
                        errors_count=state_data.get("errors_count", 0),
                        rate_limit_until=(
                            datetime.fromisoformat(state_data["rate_limit_until"])
                            if state_data.get("rate_limit_until")
                            else None
                        ),
                        metadata=state_data.get("metadata", {}),
                    )
                    self.session_states[config.session_id] = state

                print(f"✅ Loaded {len(self.sessions)} sessions")
                return True
            else:
                print("📝 No existing sessions found, starting fresh")
                return True

        except Exception as e:
            print(f"❌ Error loading sessions: {e}")
            return False

    def save_sessions(self) -> bool:
        """Save sessions to configuration file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            data: Dict[str, Any] = {"sessions": [], "states": {}}

            for config in self.sessions.values():
                data["sessions"].append({
                    "session_id": config.session_id,
                    "session_type": config.session_type.value,
                    "provider": config.provider,
                    "model": config.model,
                    "account": config.account,
                    "max_requests_per_hour": config.max_requests_per_hour,
                    "max_tokens_per_hour": config.max_tokens_per_hour,
                    "cooldown_minutes": config.cooldown_minutes,
                    "priority": config.priority,
                    "metadata": config.metadata,
                })

            for state in self.session_states.values():
                data["states"][state.session_id] = {
                    "status": state.status.value,
                    "created_at": state.created_at.isoformat(),
                    "last_used": state.last_used.isoformat(),
                    "requests_count": state.requests_count,
                    "tokens_used": state.tokens_used,
                    "errors_count": state.errors_count,
                    "rate_limit_until": (
                        state.rate_limit_until.isoformat() if state.rate_limit_until else None
                    ),
                    "metadata": state.metadata,
                }

            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=2)

            return True

        except Exception as e:
            print(f"❌ Error saving sessions: {e}")
            return False

    # ── Session CRUD ────────────────────────────────────────

    def create_session(self, session_config: SessionConfig) -> bool:
        """Create a new session."""
        with self.lock:
            if session_config.session_id in self.sessions:
                print(f"⚠️  Session {session_config.session_id} already exists")
                return False

            self.sessions[session_config.session_id] = session_config
            self.session_states[session_config.session_id] = SessionState(
                session_id=session_config.session_id,
                status=SessionStatus.IDLE,
                created_at=datetime.now(),
                last_used=datetime.now(),
            )

            print(f"✅ Created session: {session_config.session_id}")
            return True

    def remove_session(self, session_id: str) -> bool:
        """Remove a session."""
        with self.lock:
            if session_id not in self.sessions:
                print(f"❌ Session {session_id} not found")
                return False

            del self.sessions[session_id]
            del self.session_states[session_id]

            self.request_queue = [
                (sid, rid, ts) for sid, rid, ts in self.request_queue if sid != session_id
            ]

            print(f"✅ Removed session: {session_id}")
            return True

    # ── Session scheduling ──────────────────────────────────

    def get_available_session(
        self,
        session_type: SessionType,
        provider: str = None,
        model: str = None,
        account: str = None,
    ) -> Optional[str]:
        """Get the best available session for given criteria."""
        with self.lock:
            now = datetime.now()
            available_sessions = []

            for session_id, config in self.sessions.items():
                if config.session_type != session_type:
                    continue
                if provider and config.provider != provider:
                    continue
                if model and config.model != model:
                    continue
                if account and config.account != account:
                    continue

                state = self.session_states[session_id]

                if state.rate_limit_until and state.rate_limit_until > now:
                    continue
                if state.status == SessionStatus.BUSY:
                    continue
                if self._is_rate_limited(session_id, now):
                    continue

                available_sessions.append((session_id, config.priority, state.last_used))

            if not available_sessions:
                return None

            available_sessions.sort(key=lambda x: (x[1], x[2]))
            return available_sessions[0][0]

    def request_session(self, session_id: str, request_id: str = None) -> bool:
        """Request a session for use."""
        with self.lock:
            if session_id not in self.sessions:
                return False

            state = self.session_states[session_id]
            now = datetime.now()

            if state.status == SessionStatus.BUSY:
                return False
            if state.rate_limit_until and state.rate_limit_until > now:
                return False
            if self._is_rate_limited(session_id, now):
                return False

            state.status = SessionStatus.BUSY
            state.last_used = now
            state.current_request_id = request_id or str(uuid.uuid4())
            state.requests_count += 1

            return True

    def release_session(
        self, session_id: str, tokens_used: int = 0, success: bool = True
    ) -> bool:
        """Release a session after use."""
        with self.lock:
            if session_id not in self.session_states:
                return False

            state = self.session_states[session_id]
            state.status = SessionStatus.IDLE if success else SessionStatus.ERROR
            state.current_request_id = None
            state.tokens_used += tokens_used

            if not success:
                state.errors_count += 1

            if self._should_rate_limit(session_id):
                config = self.sessions[session_id]
                state.rate_limit_until = datetime.now() + timedelta(
                    minutes=config.cooldown_minutes
                )
                state.status = SessionStatus.RATE_LIMITED
                print(f"⏰ Session {session_id} rate limited until {state.rate_limit_until}")

            return True

    # ── Query methods ───────────────────────────────────────

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a session."""
        if session_id not in self.sessions:
            return None

        config = self.sessions[session_id]
        state = self.session_states[session_id]

        return {
            "session_id": session_id,
            "type": config.session_type.value,
            "provider": config.provider,
            "model": config.model,
            "account": config.account,
            "status": state.status.value,
            "created_at": state.created_at.isoformat(),
            "last_used": state.last_used.isoformat(),
            "requests_count": state.requests_count,
            "tokens_used": state.tokens_used,
            "errors_count": state.errors_count,
            "rate_limit_until": (
                state.rate_limit_until.isoformat() if state.rate_limit_until else None
            ),
            "current_request_id": state.current_request_id,
            "queue_position": state.queue_position,
            "utilization": self._get_utilization(session_id),
            "time_until_available": self._get_time_until_available(session_id),
        }

    def list_sessions(
        self, session_type: SessionType = None, status: SessionStatus = None
    ) -> List[Dict[str, Any]]:
        """List all sessions with optional filtering."""
        sessions = []
        for session_id, config in self.sessions.items():
            if session_type and config.session_type != session_type:
                continue
            state = self.session_states[session_id]
            if status and state.status != status:
                continue
            sessions.append(self.get_session_status(session_id))
        return sessions

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        with self.lock:
            for i, (session_id, _, _) in enumerate(self.request_queue):
                if session_id in self.session_states:
                    self.session_states[session_id].queue_position = i + 1

            return {
                "queue_length": len(self.request_queue),
                "waiting_sessions": len(
                    [s for s in self.session_states.values() if s.status == SessionStatus.RATE_LIMITED]
                ),
                "active_sessions": len(
                    [s for s in self.session_states.values() if s.status == SessionStatus.ACTIVE]
                ),
                "busy_sessions": len(
                    [s for s in self.session_states.values() if s.status == SessionStatus.BUSY]
                ),
                "idle_sessions": len(
                    [s for s in self.session_states.values() if s.status == SessionStatus.IDLE]
                ),
                "next_available": self._get_next_available_time(),
            }

    # ── Internal helpers ────────────────────────────────────

    def _is_rate_limited(self, session_id: str, now: datetime) -> bool:
        """Check if session is rate limited."""
        config = self.sessions[session_id]
        state = self.session_states[session_id]
        if state.requests_count >= config.max_requests_per_hour:
            return True
        if state.tokens_used >= config.max_tokens_per_hour:
            return True
        return False

    def _should_rate_limit(self, session_id: str) -> bool:
        """Check if session should be rate limited."""
        config = self.sessions[session_id]
        state = self.session_states[session_id]
        if state.requests_count >= config.max_requests_per_hour:
            return True
        if state.tokens_used >= config.max_tokens_per_hour:
            return True
        if state.errors_count >= 5:
            return True
        return False

    def _get_utilization(self, session_id: str) -> float:
        """Get session utilization percentage."""
        config = self.sessions[session_id]
        state = self.session_states[session_id]
        request_util = (state.requests_count / config.max_requests_per_hour) * 100
        token_util = (state.tokens_used / config.max_tokens_per_hour) * 100
        return max(request_util, token_util)

    def _get_time_until_available(self, session_id: str) -> Optional[int]:
        """Get seconds until session is available."""
        state = self.session_states[session_id]
        if state.status == SessionStatus.IDLE:
            return 0
        if state.rate_limit_until:
            delta = state.rate_limit_until - datetime.now()
            return max(0, int(delta.total_seconds()))
        return None

    def _get_next_available_time(self) -> Optional[str]:
        """Get when the next session will be available."""
        next_times = []
        for state in self.session_states.values():
            if state.rate_limit_until:
                next_times.append(state.rate_limit_until)
        if next_times:
            return min(next_times).isoformat()
        return None

    # ── Background tasks ────────────────────────────────────

    def _cleanup_worker(self):
        """Background worker for cleanup tasks."""
        while True:
            try:
                time.sleep(60)
                self._cleanup_expired_limits()
                self._update_session_stats()
            except Exception as e:
                print(f"❌ Cleanup worker error: {e}")

    def _cleanup_expired_limits(self):
        """Clean up expired rate limits."""
        with self.lock:
            now = datetime.now()
            for session_id, state in self.session_states.items():
                if state.rate_limit_until and state.rate_limit_until <= now:
                    state.rate_limit_until = None
                    if state.status == SessionStatus.RATE_LIMITED:
                        state.status = SessionStatus.IDLE
                        print(f"✅ Session {session_id} rate limit expired")

    def _update_session_stats(self):
        """Update session statistics and save if needed."""
        if time.time() % 300 < 60:
            self.save_sessions()

    # ── Print summary ───────────────────────────────────────

    def print_status_summary(self):
        """Print comprehensive status summary."""
        print("🎭 Session Manager Status")
        print("========================")

        total_sessions = len(self.sessions)
        status_counts: Dict[str, int] = {}
        type_counts: Dict[str, int] = {}

        for state in self.session_states.values():
            status_counts[state.status.value] = status_counts.get(state.status.value, 0) + 1
        for config in self.sessions.values():
            type_counts[config.session_type.value] = type_counts.get(config.session_type.value, 0) + 1

        print(f"📊 Total Sessions: {total_sessions}")
        print(f"📈 By Status: {dict(status_counts)}")
        print(f"🏷️  By Type: {dict(type_counts)}")

        queue_status = self.get_queue_status()
        print(f"\n🚶 Queue Status:")
        print(f"  Length: {queue_status['queue_length']}")
        print(f"  Waiting: {queue_status['waiting_sessions']}")
        print(f"  Active: {queue_status['active_sessions']}")
        print(f"  Busy: {queue_status['busy_sessions']}")
        print(f"  Idle: {queue_status['idle_sessions']}")

        if queue_status["next_available"]:
            print(f"  Next Available: {queue_status['next_available']}")

        rate_limited = [s for s in self.session_states.values() if s.rate_limit_until]
        if rate_limited:
            print(f"\n⏰ Rate Limited Sessions:")
            for state in rate_limited:
                time_left = state.rate_limit_until - datetime.now()
                print(f"  • {state.session_id}: {time_left.total_seconds():.0f}s")

        print()
