"""LLX Planfile integration - Bridge to planfile package."""

# Re-export from planfile package for backward compatibility
try:
    from planfile.models import Strategy, Sprint, TaskPattern, TaskType, ModelHints, ModelTier, Goal, QualityGate
    from planfile.runner import load_valid_strategy, run_strategy, verify_strategy_post_execution
    from planfile.executor_standalone import execute_strategy, TaskResult
    from planfile.builder import create_strategy_command
    
    __all__ = [
        "execute_strategy",
        "TaskResult", 
        "Strategy",
        "Sprint",
        "TaskPattern",
        "TaskType",
        "ModelHints",
        "ModelTier",
        "Goal",
        "QualityGate",
        "load_valid_strategy",
        "run_strategy",
        "verify_strategy_post_execution",
        "create_strategy_command",
    ]
except ImportError as e:
    # Fallback for when planfile package is not installed
    import warnings
    warnings.warn(f"planfile package not available: {e}", ImportWarning)
    
    # Provide minimal stubs
    class Strategy:
        pass
    
    class Sprint:
        pass
    
    class TaskPattern:
        pass
    
    class TaskType:
        pass
    
    class ModelHints:
        pass
    
    class ModelTier:
        pass
    
    class Goal:
        pass
    
    class QualityGate:
        pass
    
    class TaskResult:
        pass
    
    def execute_strategy(*args, **kwargs):
        raise ImportError("planfile package is required for execute_strategy")
    
    def load_valid_strategy(*args, **kwargs):
        raise ImportError("planfile package is required for load_valid_strategy")
    
    def run_strategy(*args, **kwargs):
        raise ImportError("planfile package is required for run_strategy")
    
    def verify_strategy_post_execution(*args, **kwargs):
        raise ImportError("planfile package is required for verify_strategy_post_execution")
    
    def create_strategy_command(*args, **kwargs):
        raise ImportError("planfile package is required for create_strategy_command")
    
    __all__ = [
        "execute_strategy",
        "TaskResult", 
        "Strategy",
        "Sprint",
        "TaskPattern",
        "TaskType",
        "ModelHints",
        "ModelTier",
        "Goal",
        "QualityGate",
        "load_valid_strategy",
        "run_strategy",
        "verify_strategy_post_execution",
        "create_strategy_command",
    ]
