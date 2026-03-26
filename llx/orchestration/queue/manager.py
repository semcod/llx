"""
Queue Manager — core queue lifecycle, workers, and request processing.
Extracted from the monolithic queue_manager.py.
"""

import json
import time
import heapq
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import field
from pathlib import Path
from collections import deque

from .models import QueueStatus, RequestPriority, QueueRequest, QueueConfig, QueueState
from .._utils import save_json


class QueueManager:
    """Manages multiple request queues with intelligent prioritization."""

    def __init__(self, config_file: str = None):
        self.project_root = Path.cwd()
        self.config_file = config_file or self.project_root / "orchestration" / "queues.json"
        self.queues: Dict[str, QueueConfig] = {}
        self.queue_states: Dict[str, QueueState] = {}
        self.request_queues: Dict[str, List[QueueRequest]] = {}
        self.processing_requests: Dict[str, List[QueueRequest]] = {}
        self.completed_requests: Dict[str, deque] = {}
        self.lock = threading.RLock()

        self.workers: Dict[str, List[threading.Thread]] = {}
        self.running = False

        self.load_queues()
        self.start()

    # ── Config persistence ──────────────────────────────────

    def load_queues(self) -> bool:
        """Load queues from configuration file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    data = json.load(f)

                for queue_data in data.get("queues", []):
                    config = QueueConfig(
                        queue_id=queue_data["queue_id"],
                        provider=queue_data["provider"],
                        account=queue_data["account"],
                        max_size=queue_data.get("max_size", 100),
                        max_concurrent=queue_data.get("max_concurrent", 5),
                        default_timeout=queue_data.get("default_timeout", 300),
                        retry_policy=queue_data.get("retry_policy", "exponential_backoff"),
                        metadata=queue_data.get("metadata", {}),
                    )
                    self.queues[config.queue_id] = config

                    self.request_queues[config.queue_id] = []
                    self.processing_requests[config.queue_id] = []
                    self.completed_requests[config.queue_id] = deque(maxlen=100)

                    state_data = data.get("states", {}).get(config.queue_id, {})
                    state = QueueState(
                        queue_id=config.queue_id,
                        status=QueueStatus(state_data.get("status", "idle")),
                        created_at=datetime.fromisoformat(
                            state_data.get("created_at", datetime.now().isoformat())
                        ),
                        last_processed=(
                            datetime.fromisoformat(state_data["last_processed"])
                            if state_data.get("last_processed")
                            else None
                        ),
                        total_requests=state_data.get("total_requests", 0),
                        processed_requests=state_data.get("processed_requests", 0),
                        failed_requests=state_data.get("failed_requests", 0),
                        timeout_requests=state_data.get("timeout_requests", 0),
                        current_processing=state_data.get("current_processing", 0),
                        average_wait_time=state_data.get("average_wait_time", 0.0),
                        average_processing_time=state_data.get("average_processing_time", 0.0),
                        metadata=state_data.get("metadata", {}),
                    )
                    self.queue_states[config.queue_id] = state

                print(f"✅ Loaded {len(self.queues)} queues")
                return True
            else:
                print("📝 No existing queues found, starting fresh")
                return True

        except Exception as e:
            print(f"❌ Error loading queues: {e}")
            return False

    def save_queues(self) -> bool:
        """Save queues to configuration file."""
        try:
            data: Dict[str, Any] = {"queues": [], "states": {}}

            for config in self.queues.values():
                data["queues"].append({
                    "queue_id": config.queue_id,
                    "provider": config.provider,
                    "account": config.account,
                    "max_size": config.max_size,
                    "max_concurrent": config.max_concurrent,
                    "default_timeout": config.default_timeout,
                    "retry_policy": config.retry_policy,
                    "metadata": config.metadata,
                })

            for state in self.queue_states.values():
                data["states"][state.queue_id] = {
                    "status": state.status.value,
                    "created_at": state.created_at.isoformat(),
                    "last_processed": (
                        state.last_processed.isoformat() if state.last_processed else None
                    ),
                    "total_requests": state.total_requests,
                    "processed_requests": state.processed_requests,
                    "failed_requests": state.failed_requests,
                    "timeout_requests": state.timeout_requests,
                    "current_processing": state.current_processing,
                    "average_wait_time": state.average_wait_time,
                    "average_processing_time": state.average_processing_time,
                    "metadata": state.metadata,
                }

            return save_json(self.config_file, data, "queues")

        except Exception as e:
            print(f"❌ Error saving queues: {e}")
            return False

    # ── Lifecycle ───────────────────────────────────────────

    def start(self):
        """Start the queue manager and workers."""
        with self.lock:
            if self.running:
                return
            self.running = True

            for queue_id, config in self.queues.items():
                self.workers[queue_id] = []
                for i in range(config.max_concurrent):
                    worker = threading.Thread(
                        target=self._worker_loop,
                        args=(queue_id, f"worker-{i}"),
                        daemon=True,
                    )
                    worker.start()
                    self.workers[queue_id].append(worker)

            print(f"✅ Started queue manager with {len(self.queues)} queues")

    def stop(self):
        """Stop the queue manager and workers."""
        with self.lock:
            self.running = False
            for workers in self.workers.values():
                for worker in workers:
                    worker.join(timeout=5)
            self.workers.clear()
            print("✅ Stopped queue manager")

    # ── Queue CRUD ──────────────────────────────────────────

    def add_queue(self, config: QueueConfig) -> bool:
        """Add a new queue."""
        with self.lock:
            if config.queue_id in self.queues:
                print(f"⚠️  Queue {config.queue_id} already exists")
                return False

            self.queues[config.queue_id] = config
            self.request_queues[config.queue_id] = []
            self.processing_requests[config.queue_id] = []
            self.completed_requests[config.queue_id] = deque(maxlen=100)

            self.queue_states[config.queue_id] = QueueState(
                queue_id=config.queue_id,
                status=QueueStatus.IDLE,
                created_at=datetime.now(),
            )

            if self.running:
                self.workers[config.queue_id] = []
                for i in range(config.max_concurrent):
                    worker = threading.Thread(
                        target=self._worker_loop,
                        args=(config.queue_id, f"worker-{i}"),
                        daemon=True,
                    )
                    worker.start()
                    self.workers[config.queue_id].append(worker)

            print(f"✅ Added queue: {config.queue_id}")
            return True

    def remove_queue(self, queue_id: str) -> bool:
        """Remove a queue."""
        with self.lock:
            if queue_id not in self.queues:
                print(f"❌ Queue {queue_id} not found")
                return False

            if queue_id in self.workers:
                del self.workers[queue_id]

            del self.queues[queue_id]
            del self.queue_states[queue_id]
            del self.request_queues[queue_id]
            del self.processing_requests[queue_id]
            del self.completed_requests[queue_id]

            print(f"✅ Removed queue: {queue_id}")
            return True

    # ── Enqueue / dequeue / complete ────────────────────────

    def enqueue_request(self, request: QueueRequest) -> bool:
        """Add a request to the appropriate queue."""
        with self.lock:
            queue_id = self._get_queue_id(request.provider, request.account)
            if not queue_id:
                print(f"❌ No queue found for {request.provider}:{request.account}")
                return False

            config = self.queues[queue_id]
            if len(self.request_queues[queue_id]) >= config.max_size:
                print(f"❌ Queue {queue_id} is full")
                return False

            heapq.heappush(self.request_queues[queue_id], request)
            self.queue_states[queue_id].total_requests += 1

            print(f"✅ Enqueued request {request.request_id} in {queue_id}")
            return True

    def dequeue_request(self, queue_id: str) -> Optional[QueueRequest]:
        """Get the next request from a queue."""
        with self.lock:
            if queue_id not in self.request_queues:
                return None
            if not self.request_queues[queue_id]:
                return None

            request = heapq.heappop(self.request_queues[queue_id])
            self.processing_requests[queue_id].append(request)
            self.queue_states[queue_id].current_processing += 1

            return request

    def complete_request(
        self, request: QueueRequest, success: bool = True, processing_time: float = 0.0
    ) -> bool:
        """Mark a request as completed."""
        with self.lock:
            queue_id = self._get_queue_id(request.provider, request.account)
            if not queue_id:
                return False

            if request in self.processing_requests[queue_id]:
                self.processing_requests[queue_id].remove(request)

            self.completed_requests[queue_id].append(request)

            state = self.queue_states[queue_id]
            state.current_processing = max(0, state.current_processing - 1)
            state.last_processed = datetime.now()

            if success:
                state.processed_requests += 1
            else:
                state.failed_requests += 1
                if request.retry_count < request.max_retries:
                    request.retry_count += 1
                    retry_delay = self._calculate_retry_delay(request.retry_count, request.created_at)
                    if retry_delay > 0:
                        threading.Timer(
                            retry_delay, self._retry_request, args=[queue_id, request]
                        ).start()
                    else:
                        heapq.heappush(self.request_queues[queue_id], request)
                else:
                    print(f"❌ Request {request.request_id} exceeded max retries")

            self._update_averages(queue_id, processing_time)
            return True

    # ── Query methods ───────────────────────────────────────

    def get_queue_status(self, queue_id: str = None) -> Dict[str, Any]:
        """Get status of queues."""
        with self.lock:
            if queue_id:
                if queue_id not in self.queues:
                    return {}
                return self._get_single_queue_status(queue_id)
            return self._get_all_queue_status()

    def get_queue_metrics(self, queue_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed metrics for a queue."""
        with self.lock:
            if queue_id not in self.queues:
                return None

            config = self.queues[queue_id]
            state = self.queue_states[queue_id]
            now = datetime.now()

            wait_times = [
                (now - r.created_at).total_seconds() for r in self.request_queues[queue_id]
            ]
            processing_times = [
                r.metadata["processing_time"]
                for r in self.completed_requests[queue_id]
                if "processing_time" in r.metadata
            ]

            return {
                "queue_id": queue_id,
                "provider": config.provider,
                "account": config.account,
                "status": state.status.value,
                "queue_length": len(self.request_queues[queue_id]),
                "processing": len(self.processing_requests[queue_id]),
                "max_size": config.max_size,
                "max_concurrent": config.max_concurrent,
                "total_requests": state.total_requests,
                "processed_requests": state.processed_requests,
                "failed_requests": state.failed_requests,
                "timeout_requests": state.timeout_requests,
                "success_rate": (
                    (state.processed_requests / state.total_requests * 100)
                    if state.total_requests > 0
                    else 0
                ),
                "average_wait_time": state.average_wait_time,
                "average_processing_time": state.average_processing_time,
                "current_wait_times": wait_times,
                "current_processing_times": processing_times,
                "oldest_request_age": max(wait_times) if wait_times else 0,
                "workers_running": len(self.workers.get(queue_id, [])),
                "utilization": (
                    (len(self.processing_requests[queue_id]) / config.max_concurrent * 100)
                    if config.max_concurrent > 0
                    else 0
                ),
            }

    # ── Internal helpers ────────────────────────────────────

    def _get_queue_id(self, provider: str, account: str) -> Optional[str]:
        for queue_id, config in self.queues.items():
            if config.provider == provider and config.account == account:
                return queue_id
        return None

    def _get_single_queue_status(self, queue_id: str) -> Dict[str, Any]:
        config = self.queues[queue_id]
        state = self.queue_states[queue_id]
        return {
            "queue_id": queue_id,
            "provider": config.provider,
            "account": config.account,
            "status": state.status.value,
            "queue_length": len(self.request_queues[queue_id]),
            "processing": len(self.processing_requests[queue_id]),
            "max_size": config.max_size,
            "max_concurrent": config.max_concurrent,
            "total_requests": state.total_requests,
            "processed_requests": state.processed_requests,
            "failed_requests": state.failed_requests,
            "timeout_requests": state.timeout_requests,
            "success_rate": (
                (state.processed_requests / state.total_requests * 100)
                if state.total_requests > 0
                else 0
            ),
            "average_wait_time": state.average_wait_time,
            "average_processing_time": state.average_processing_time,
            "workers_running": len(self.workers.get(queue_id, [])),
            "utilization": (
                (len(self.processing_requests[queue_id]) / config.max_concurrent * 100)
                if config.max_concurrent > 0
                else 0
            ),
        }

    def _get_all_queue_status(self) -> Dict[str, Any]:
        status: Dict[str, Any] = {
            "total_queues": len(self.queues),
            "running": self.running,
            "total_workers": sum(len(w) for w in self.workers.values()),
            "queues": {},
        }
        for queue_id in self.queues:
            status["queues"][queue_id] = self._get_single_queue_status(queue_id)
        return status

    def _worker_loop(self, queue_id: str, worker_name: str):
        print(f"🔄 Worker {worker_name} started for queue {queue_id}")
        while self.running:
            try:
                request = self.dequeue_request(queue_id)
                if not request:
                    time.sleep(0.1)
                    continue
                start_time = time.time()
                success = self._process_request(request)
                processing_time = time.time() - start_time
                request.metadata["processing_time"] = processing_time
                self.complete_request(request, success, processing_time)
            except Exception as e:
                print(f"❌ Worker {worker_name} error: {e}")
                time.sleep(1)
        print(f"🛑 Worker {worker_name} stopped for queue {queue_id}")

    def _process_request(self, request: QueueRequest) -> bool:
        time.sleep(0.1)
        if time.time() - request.created_at.timestamp() > request.timeout_seconds:
            return False
        return True

    def _retry_request(self, queue_id: str, request: QueueRequest):
        with self.lock:
            if queue_id in self.request_queues:
                heapq.heappush(self.request_queues[queue_id], request)
                print(f"🔄 Retrying request {request.request_id} (attempt {request.retry_count})")

    def _calculate_retry_delay(self, retry_count: int, created_at: datetime) -> float:
        return min(300, (2 ** retry_count))

    def _update_averages(self, queue_id: str, processing_time: float):
        state = self.queue_states[queue_id]
        if state.processed_requests > 0:
            state.average_processing_time = (
                (state.average_processing_time * (state.processed_requests - 1) + processing_time)
                / state.processed_requests
            )
        wait_times = []
        for request in self.completed_requests[queue_id]:
            wt = (request.created_at - state.created_at).total_seconds()
            wait_times.append(wt)
        if wait_times:
            state.average_wait_time = sum(wait_times) / len(wait_times)

    # ── Print summary ───────────────────────────────────────

    def print_status_summary(self):
        """Print comprehensive status summary."""
        print("📋 Queue Manager Status")
        print("======================")

        total_queues = len(self.queues)
        total_requests = sum(s.total_requests for s in self.queue_states.values())
        total_processed = sum(s.processed_requests for s in self.queue_states.values())
        total_failed = sum(s.failed_requests for s in self.queue_states.values())

        print(f"📊 Total Queues: {total_queues}")
        print(f"🔄 Running: {self.running}")
        print(f"👷 Total Workers: {sum(len(w) for w in self.workers.values())}")
        print(f"📈 Total Requests: {total_requests}")
        print(f"✅ Processed: {total_processed}")
        print(f"❌ Failed: {total_failed}")
        print(
            f"📊 Success Rate: "
            f"{(total_processed / total_requests * 100) if total_requests > 0 else 0:.1f}%"
        )

        print("\n📋 Queue Details:")
        for queue_id, config in self.queues.items():
            state = self.queue_states[queue_id]
            queue_length = len(self.request_queues[queue_id])
            processing = len(self.processing_requests[queue_id])
            utilization = (
                (processing / config.max_concurrent * 100) if config.max_concurrent > 0 else 0
            )

            print(f"  • {queue_id}: {config.provider}:{config.account}")
            print(f"    Status: {state.status.value}")
            print(f"    Queue: {queue_length}/{config.max_size}")
            print(f"    Processing: {processing}/{config.max_concurrent}")
            print(f"    Utilization: {utilization:.1f}%")
            print(
                f"    Success Rate: "
                f"{(state.processed_requests / state.total_requests * 100) if state.total_requests > 0 else 0:.1f}%"
            )

        print()
