"""Queue manager CLI — _build_parser + _dispatch pattern."""

import json
import argparse
from datetime import datetime

from .._utils import cli_main
from ..cli_utils import cmd_remove_wrapper
from ..utils._cmd_remove import create_remove_handler
from ..utils._cmd_cleanup import create_cleanup_handler

from .models import RequestPriority, QueueRequest, QueueConfig
from .manager import QueueManager


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="llx Queue Manager")
    parser.add_argument(
        "command",
        choices=["add", "remove", "enqueue", "dequeue", "complete", "status", "metrics", "cleanup"],
    )
    parser.add_argument("--queue-id", help="Queue ID")
    parser.add_argument("--provider", help="Provider name")
    parser.add_argument("--account", help="Account name")
    parser.add_argument("--request-id", help="Request ID")
    parser.add_argument(
        "--priority",
        choices=["urgent", "high", "normal", "low", "background"],
        help="Request priority",
    )
    parser.add_argument("--type", help="Request type")
    parser.add_argument("--tokens", type=int, default=0, help="Number of tokens")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    parser.add_argument("--max-size", type=int, default=100, help="Maximum queue size")
    parser.add_argument("--max-concurrent", type=int, default=5, help="Maximum concurrent requests")
    parser.add_argument("--success", action="store_true", help="Request was successful")
    return parser


def _dispatch(args: argparse.Namespace, mgr: QueueManager) -> bool:
    handlers = {
        "add": _cmd_add,
        "remove": _cmd_remove,
        "enqueue": _cmd_enqueue,
        "dequeue": _cmd_dequeue,
        "complete": _cmd_complete,
        "status": _cmd_status,
        "metrics": _cmd_metrics,
        "cleanup": _cmd_cleanup,
    }
    handler = handlers.get(args.command)
    if handler:
        return handler(args, mgr)
    return False


def _cmd_add(args, mgr: QueueManager) -> bool:
    if not args.queue_id or not args.provider or not args.account:
        print("❌ --queue-id, --provider, and --account required for add")
        return False
    config = QueueConfig(
        queue_id=args.queue_id,
        provider=args.provider,
        account=args.account,
        max_size=args.max_size,
        max_concurrent=args.max_concurrent,
    )
    success = mgr.add_queue(config)
    if success:
        mgr.save_queues()
    return success


# Create remove handler
_cmd_remove = create_remove_handler(
    id_attr="queue_id",
    id_label="Queue",
    remove_func=lambda mgr, id: mgr.remove_queue(id),
    save_func=lambda mgr: mgr.save_queues()
)


def _cmd_enqueue(args, mgr: QueueManager) -> bool:
    if not args.provider or not args.account or not args.request_id:
        print("❌ --provider, --account, and --request-id required for enqueue")
        return False
    request = QueueRequest(
        request_id=args.request_id,
        provider=args.provider,
        account=args.account,
        request_type=args.type or "default",
        priority=RequestPriority(args.priority) if args.priority else RequestPriority.NORMAL,
        created_at=datetime.now(),
        tokens=args.tokens,
        timeout_seconds=args.timeout,
    )
    return mgr.enqueue_request(request)


def _cmd_dequeue(args, mgr: QueueManager) -> bool:
    if not args.queue_id:
        print("❌ --queue-id required for dequeue")
        return False
    request = mgr.dequeue_request(args.queue_id)
    if request:
        print(f"✅ Dequeued request: {request.request_id}")
        return True
    print("❌ No requests available")
    return False


def _cmd_complete(args, mgr: QueueManager) -> bool:
    if not args.request_id:
        print("❌ --request-id required for complete")
        return False
    print(f"✅ Completed request: {args.request_id}")
    return True


def _cmd_status(args, mgr: QueueManager) -> bool:
    status = mgr.get_queue_status(args.queue_id)
    print(json.dumps(status, indent=2))
    return True


def _cmd_metrics(args, mgr: QueueManager) -> bool:
    if not args.queue_id:
        print("❌ --queue-id required for metrics")
        return False
    metrics = mgr.get_queue_metrics(args.queue_id)
    if metrics:
        print(json.dumps(metrics, indent=2))
        return True
    print(f"❌ No metrics available for {args.queue_id}")
    return False


# Create cleanup handler
_cmd_cleanup = create_cleanup_handler(
    save_func=lambda mgr: mgr.save_queues()
)


def main():
    cli_main(_build_parser, _dispatch, QueueManager, cleanup=lambda m: m.stop())


if __name__ == "__main__":
    main()
