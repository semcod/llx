"""
Queue Manager for llx Orchestration
Manages request queuing and prioritization for rate-limited resources.
"""

import os
import sys
import json
import time
import threading
import heapq
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import deque
import uuid


class QueueStatus(Enum):
    """Queue status."""
    IDLE = "idle"
    PROCESSING = "processing"
    FULL = "full"
    PAUSED = "paused"


class RequestPriority(Enum):
    """Request priority levels."""
    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class QueueRequest:
    """A request in the queue."""
    request_id: str
    provider: str
    account: str
    request_type: str
    priority: RequestPriority
    created_at: datetime
    tokens: int = 0
    timeout_seconds: int = 300
    max_retries: int = 3
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """For priority queue ordering."""
        # Lower priority number = higher priority
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        
        # If same priority, earlier creation time wins
        return self.created_at < other.created_at


@dataclass
class QueueConfig:
    """Configuration for a queue."""
    queue_id: str
    provider: str
    account: str
    max_size: int = 100
    max_concurrent: int = 5
    default_timeout: int = 300
    retry_policy: str = "exponential_backoff"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueueState:
    """Current state of a queue."""
    queue_id: str
    status: QueueStatus
    created_at: datetime
    last_processed: Optional[datetime]
    total_requests: int = 0
    processed_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    current_processing: int = 0
    average_wait_time: float = 0.0
    average_processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class QueueManager:
    """Manages multiple request queues with intelligent prioritization."""
    
    def __init__(self, config_file: str = None):
        self.project_root = Path.cwd()
        self.config_file = config_file or self.project_root / "orchestration" / "queues.json"
        self.queues: Dict[str, QueueConfig] = {}
        self.queue_states: Dict[str, QueueState] = {}
        self.request_queues: Dict[str, List[QueueRequest]] = {}  # Priority queues (heap)
        self.processing_requests: Dict[str, List[QueueRequest]] = {}  # Currently processing
        self.completed_requests: Dict[str, deque] = {}  # Recently completed
        self.lock = threading.RLock()
        
        # Worker threads
        self.workers: Dict[str, List[threading.Thread]] = {}
        self.running = False
        
        # Load existing configuration
        self.load_queues()
        
        # Start queue manager
        self.start()
    
    def load_queues(self) -> bool:
        """Load queues from configuration file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Load queue configurations
                for queue_data in data.get("queues", []):
                    config = QueueConfig(
                        queue_id=queue_data["queue_id"],
                        provider=queue_data["provider"],
                        account=queue_data["account"],
                        max_size=queue_data.get("max_size", 100),
                        max_concurrent=queue_data.get("max_concurrent", 5),
                        default_timeout=queue_data.get("default_timeout", 300),
                        retry_policy=queue_data.get("retry_policy", "exponential_backoff"),
                        metadata=queue_data.get("metadata", {})
                    )
                    self.queues[config.queue_id] = config
                    
                    # Initialize queue structures
                    self.request_queues[config.queue_id] = []
                    self.processing_requests[config.queue_id] = []
                    self.completed_requests[config.queue_id] = deque(maxlen=100)
                    
                    # Load or create queue state
                    state_data = data.get("states", {}).get(config.queue_id, {})
                    state = QueueState(
                        queue_id=config.queue_id,
                        status=QueueStatus(state_data.get("status", "idle")),
                        created_at=datetime.fromisoformat(state_data.get("created_at", datetime.now().isoformat())),
                        last_processed=datetime.fromisoformat(state_data["last_processed"]) if state_data.get("last_processed") else None,
                        total_requests=state_data.get("total_requests", 0),
                        processed_requests=state_data.get("processed_requests", 0),
                        failed_requests=state_data.get("failed_requests", 0),
                        timeout_requests=state_data.get("timeout_requests", 0),
                        current_processing=state_data.get("current_processing", 0),
                        average_wait_time=state_data.get("average_wait_time", 0.0),
                        average_processing_time=state_data.get("average_processing_time", 0.0),
                        metadata=state_data.get("metadata", {})
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
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "queues": [],
                "states": {}
            }
            
            # Save queue configurations
            for config in self.queues.values():
                data["queues"].append({
                    "queue_id": config.queue_id,
                    "provider": config.provider,
                    "account": config.account,
                    "max_size": config.max_size,
                    "max_concurrent": config.max_concurrent,
                    "default_timeout": config.default_timeout,
                    "retry_policy": config.retry_policy,
                    "metadata": config.metadata
                })
            
            # Save queue states
            for state in self.queue_states.values():
                data["states"][state.queue_id] = {
                    "status": state.status.value,
                    "created_at": state.created_at.isoformat(),
                    "last_processed": state.last_processed.isoformat() if state.last_processed else None,
                    "total_requests": state.total_requests,
                    "processed_requests": state.processed_requests,
                    "failed_requests": state.failed_requests,
                    "timeout_requests": state.timeout_requests,
                    "current_processing": state.current_processing,
                    "average_wait_time": state.average_wait_time,
                    "average_processing_time": state.average_processing_time,
                    "metadata": state.metadata
                }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving queues: {e}")
            return False
    
    def start(self):
        """Start the queue manager and workers."""
        with self.lock:
            if self.running:
                return
            
            self.running = True
            
            # Start workers for each queue
            for queue_id, config in self.queues.items():
                self.workers[queue_id] = []
                
                for i in range(config.max_concurrent):
                    worker = threading.Thread(
                        target=self._worker_loop,
                        args=(queue_id, f"worker-{i}"),
                        daemon=True
                    )
                    worker.start()
                    self.workers[queue_id].append(worker)
            
            print(f"✅ Started queue manager with {len(self.queues)} queues")
    
    def stop(self):
        """Stop the queue manager and workers."""
        with self.lock:
            self.running = False
            
            # Wait for workers to finish
            for queue_id, workers in self.workers.items():
                for worker in workers:
                    worker.join(timeout=5)
            
            self.workers.clear()
            print(f"✅ Stopped queue manager")
    
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
            
            # Create initial state
            self.queue_states[config.queue_id] = QueueState(
                queue_id=config.queue_id,
                status=QueueStatus.IDLE,
                created_at=datetime.now()
            )
            
            # Start workers for new queue
            if self.running:
                self.workers[config.queue_id] = []
                for i in range(config.max_concurrent):
                    worker = threading.Thread(
                        target=self._worker_loop,
                        args=(config.queue_id, f"worker-{i}"),
                        daemon=True
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
            
            # Stop workers
            if queue_id in self.workers:
                # Note: Workers will stop naturally when queue is removed
                del self.workers[queue_id]
            
            # Remove queue structures
            del self.queues[queue_id]
            del self.queue_states[queue_id]
            del self.request_queues[queue_id]
            del self.processing_requests[queue_id]
            del self.completed_requests[queue_id]
            
            print(f"✅ Removed queue: {queue_id}")
            return True
    
    def enqueue_request(self, request: QueueRequest) -> bool:
        """Add a request to the appropriate queue."""
        with self.lock:
            queue_id = self._get_queue_id(request.provider, request.account)
            
            if not queue_id:
                print(f"❌ No queue found for {request.provider}:{request.account}")
                return False
            
            config = self.queues[queue_id]
            state = self.queue_states[queue_id]
            
            # Check queue capacity
            if len(self.request_queues[queue_id]) >= config.max_size:
                print(f"❌ Queue {queue_id} is full")
                return False
            
            # Add to priority queue
            heapq.heappush(self.request_queues[queue_id], request)
            state.total_requests += 1
            
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
            
            # Add to processing
            self.processing_requests[queue_id].append(request)
            state = self.queue_states[queue_id]
            state.current_processing += 1
            
            return request
    
    def complete_request(self, request: QueueRequest, success: bool = True, processing_time: float = 0.0) -> bool:
        """Mark a request as completed."""
        with self.lock:
            queue_id = self._get_queue_id(request.provider, request.account)
            
            if not queue_id:
                return False
            
            # Remove from processing
            if request in self.processing_requests[queue_id]:
                self.processing_requests[queue_id].remove(request)
            
            # Add to completed
            self.completed_requests[queue_id].append(request)
            
            # Update statistics
            state = self.queue_states[queue_id]
            state.current_processing = max(0, state.current_processing - 1)
            state.last_processed = datetime.now()
            
            if success:
                state.processed_requests += 1
            else:
                state.failed_requests += 1
                
                # Retry logic
                if request.retry_count < request.max_retries:
                    request.retry_count += 1
                    
                    # Calculate retry delay
                    retry_delay = self._calculate_retry_delay(request.retry_count, request.created_at)
                    if retry_delay > 0:
                        # Requeue with delay
                        threading.Timer(retry_delay, self._retry_request, args=[queue_id, request]).start()
                    else:
                        # Requeue immediately
                        heapq.heappush(self.request_queues[queue_id], request)
                else:
                    # Max retries exceeded
                    print(f"❌ Request {request.request_id} exceeded max retries")
            
            # Update averages
            self._update_averages(queue_id, processing_time)
            
            return True
    
    def get_queue_status(self, queue_id: str = None) -> Dict[str, Any]:
        """Get status of queues."""
        with self.lock:
            if queue_id:
                if queue_id not in self.queues:
                    return {}
                
                return self._get_single_queue_status(queue_id)
            else:
                return self._get_all_queue_status()
    
    def get_queue_metrics(self, queue_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed metrics for a queue."""
        with self.lock:
            if queue_id not in self.queues:
                return None
            
            config = self.queues[queue_id]
            state = self.queue_states[queue_id]
            
            # Calculate wait times
            wait_times = []
            now = datetime.now()
            
            for request in self.request_queues[queue_id]:
                wait_time = (now - request.created_at).total_seconds()
                wait_times.append(wait_time)
            
            # Calculate processing times from completed requests
            processing_times = []
            for request in self.completed_requests[queue_id]:
                if "processing_time" in request.metadata:
                    processing_times.append(request.metadata["processing_time"])
            
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
                "success_rate": (state.processed_requests / state.total_requests * 100) if state.total_requests > 0 else 0,
                "average_wait_time": state.average_wait_time,
                "average_processing_time": state.average_processing_time,
                "current_wait_times": wait_times,
                "current_processing_times": processing_times,
                "oldest_request_age": max(wait_times) if wait_times else 0,
                "workers_running": len(self.workers.get(queue_id, [])),
                "utilization": (len(self.processing_requests[queue_id]) / config.max_concurrent * 100) if config.max_concurrent > 0 else 0
            }
    
    def _get_queue_id(self, provider: str, account: str) -> Optional[str]:
        """Get queue ID for provider and account."""
        for queue_id, config in self.queues.items():
            if config.provider == provider and config.account == account:
                return queue_id
        return None
    
    def _get_single_queue_status(self, queue_id: str) -> Dict[str, Any]:
        """Get status of a single queue."""
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
            "success_rate": (state.processed_requests / state.total_requests * 100) if state.total_requests > 0 else 0,
            "average_wait_time": state.average_wait_time,
            "average_processing_time": state.average_processing_time,
            "workers_running": len(self.workers.get(queue_id, [])),
            "utilization": (len(self.processing_requests[queue_id]) / config.max_concurrent * 100) if config.max_concurrent > 0 else 0
        }
    
    def _get_all_queue_status(self) -> Dict[str, Any]:
        """Get status of all queues."""
        status = {
            "total_queues": len(self.queues),
            "running": self.running,
            "total_workers": sum(len(workers) for workers in self.workers.values()),
            "queues": {}
        }
        
        for queue_id in self.queues:
            status["queues"][queue_id] = self._get_single_queue_status(queue_id)
        
        return status
    
    def _worker_loop(self, queue_id: str, worker_name: str):
        """Worker thread loop."""
        print(f"🔄 Worker {worker_name} started for queue {queue_id}")
        
        while self.running:
            try:
                # Get next request
                request = self.dequeue_request(queue_id)
                
                if not request:
                    # No requests available, wait
                    time.sleep(0.1)
                    continue
                
                # Process request
                start_time = time.time()
                success = self._process_request(request)
                processing_time = time.time() - start_time
                
                # Mark as completed
                request.metadata["processing_time"] = processing_time
                self.complete_request(request, success, processing_time)
                
            except Exception as e:
                print(f"❌ Worker {worker_name} error: {e}")
                time.sleep(1)
        
        print(f"🛑 Worker {worker_name} stopped for queue {queue_id}")
    
    def _process_request(self, request: QueueRequest) -> bool:
        """Process a single request."""
        # This is a placeholder - actual processing would be done by the calling code
        # The request should be processed by the appropriate service (LLM, VS Code, etc.)
        
        # For now, simulate processing
        time.sleep(0.1)
        
        # Check for timeout
        if time.time() - request.created_at.timestamp() > request.timeout_seconds:
            return False
        
        return True
    
    def _retry_request(self, queue_id: str, request: QueueRequest):
        """Retry a failed request."""
        with self.lock:
            if queue_id in self.request_queues:
                heapq.heappush(self.request_queues[queue_id], request)
                print(f"🔄 Retrying request {request.request_id} (attempt {request.retry_count})")
    
    def _calculate_retry_delay(self, retry_count: int, created_at: datetime) -> float:
        """Calculate retry delay based on policy."""
        # Exponential backoff
        return min(300, (2 ** retry_count))  # Max 5 minutes
    
    def _update_averages(self, queue_id: str, processing_time: float):
        """Update average wait and processing times."""
        state = self.queue_states[queue_id]
        
        # Update processing time average
        if state.processed_requests > 0:
            state.average_processing_time = (
                (state.average_processing_time * (state.processed_requests - 1) + processing_time) /
                state.processed_requests
            )
        
        # Update wait time average
        wait_times = []
        now = datetime.now()
        
        for request in self.completed_requests[queue_id]:
            wait_time = (request.created_at - state.created_at).total_seconds()
            wait_times.append(wait_time)
        
        if wait_times:
            state.average_wait_time = sum(wait_times) / len(wait_times)
    
    def print_status_summary(self):
        """Print comprehensive status summary."""
        print("📋 Queue Manager Status")
        print("======================")
        
        # Overall stats
        total_queues = len(self.queues)
        total_requests = sum(state.total_requests for state in self.queue_states.values())
        total_processed = sum(state.processed_requests for state in self.queue_states.values())
        total_failed = sum(state.failed_requests for state in self.queue_states.values())
        
        print(f"📊 Total Queues: {total_queues}")
        print(f"🔄 Running: {self.running}")
        print(f"👷 Total Workers: {sum(len(workers) for workers in self.workers.values())}")
        print(f"📈 Total Requests: {total_requests}")
        print(f"✅ Processed: {total_processed}")
        print(f"❌ Failed: {total_failed}")
        print(f"📊 Success Rate: {(total_processed / total_requests * 100) if total_requests > 0 else 0:.1f}%")
        
        # Queue breakdown
        print(f"\n📋 Queue Details:")
        for queue_id, config in self.queues.items():
            state = self.queue_states[queue_id]
            queue_length = len(self.request_queues[queue_id])
            processing = len(self.processing_requests[queue_id])
            utilization = (processing / config.max_concurrent * 100) if config.max_concurrent > 0 else 0
            
            print(f"  • {queue_id}: {config.provider}:{config.account}")
            print(f"    Status: {state.status.value}")
            print(f"    Queue: {queue_length}/{config.max_size}")
            print(f"    Processing: {processing}/{config.max_concurrent}")
            print(f"    Utilization: {utilization:.1f}%")
            print(f"    Success Rate: {(state.processed_requests / state.total_requests * 100) if state.total_requests > 0 else 0:.1f}%")
        
        print()


# CLI interface
def main():
    """CLI interface for queue manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="llx Queue Manager")
    parser.add_argument("command", choices=[
        "add", "remove", "enqueue", "dequeue", "complete", "status", "metrics", "cleanup"
    ])
    parser.add_argument("--queue-id", help="Queue ID")
    parser.add_argument("--provider", help="Provider name")
    parser.add_argument("--account", help="Account name")
    parser.add_argument("--request-id", help="Request ID")
    parser.add_argument("--priority", choices=["urgent", "high", "normal", "low", "background"], help="Request priority")
    parser.add_argument("--type", help="Request type")
    parser.add_argument("--tokens", type=int, default=0, help="Number of tokens")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    parser.add_argument("--max-size", type=int, default=100, help="Maximum queue size")
    parser.add_argument("--max-concurrent", type=int, default=5, help="Maximum concurrent requests")
    parser.add_argument("--success", action="store_true", help="Request was successful")
    
    args = parser.parse_args()
    
    manager = QueueManager()
    
    try:
        if args.command == "add":
            if not args.queue_id or not args.provider or not args.account:
                print("❌ --queue-id, --provider, and --account required for add")
                sys.exit(1)
            
            config = QueueConfig(
                queue_id=args.queue_id,
                provider=args.provider,
                account=args.account,
                max_size=args.max_size,
                max_concurrent=args.max_concurrent
            )
            
            success = manager.add_queue(config)
            if success:
                manager.save_queues()
        
        elif args.command == "remove":
            if not args.queue_id:
                print("❌ --queue-id required for remove")
                sys.exit(1)
            
            success = manager.remove_queue(args.queue_id)
            if success:
                manager.save_queues()
        
        elif args.command == "enqueue":
            if not args.provider or not args.account or not args.request_id:
                print("❌ --provider, --account, and --request-id required for enqueue")
                sys.exit(1)
            
            request = QueueRequest(
                request_id=args.request_id,
                provider=args.provider,
                account=args.account,
                request_type=args.type or "default",
                priority=RequestPriority(args.priority) if args.priority else RequestPriority.NORMAL,
                created_at=datetime.now(),
                tokens=args.tokens,
                timeout_seconds=args.timeout
            )
            
            success = manager.enqueue_request(request)
        
        elif args.command == "dequeue":
            if not args.queue_id:
                print("❌ --queue-id required for dequeue")
                sys.exit(1)
            
            request = manager.dequeue_request(args.queue_id)
            if request:
                print(f"✅ Dequeued request: {request.request_id}")
            else:
                print("❌ No requests available")
        
        elif args.command == "complete":
            if not args.request_id:
                print("❌ --request-id required for complete")
                sys.exit(1)
            
            # This is a simplified completion - in real usage, you'd need the actual request object
            print(f"✅ Completed request: {args.request_id}")
        
        elif args.command == "status":
            if args.queue_id:
                status = manager.get_queue_status(args.queue_id)
                print(json.dumps(status, indent=2))
            else:
                status = manager.get_queue_status()
                print(json.dumps(status, indent=2))
        
        elif args.command == "metrics":
            if not args.queue_id:
                print("❌ --queue-id required for metrics")
                sys.exit(1)
            
            metrics = manager.get_queue_metrics(args.queue_id)
            if metrics:
                print(json.dumps(metrics, indent=2))
            else:
                print(f"❌ No metrics available for {args.queue_id}")
        
        elif args.command == "cleanup":
            manager.save_queues()
            print("✅ Cleanup completed")
        
        sys.exit(0 if success else 1)
    
    finally:
        manager.stop()


if __name__ == "__main__":
    main()
