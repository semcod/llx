"""
Strategy models for LLX - integrated approach.
No separate library needed - just add to llx package.
"""
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
import yaml


class TaskType(str, Enum):
    """Type of task in the strategy."""
    feature = "feature"
    tech_debt = "tech_debt"
    bug = "bug"
    chore = "chore"
    documentation = "documentation"


class ModelTier(str, Enum):
    """Model tier for different phases of work."""
    local = "local"
    cheap = "cheap"
    balanced = "balanced"
    premium = "premium"


class ModelHints(BaseModel):
    """AI model hints for different phases of task execution."""
    design: Optional[ModelTier] = None
    implementation: Optional[ModelTier] = None
    review: Optional[ModelTier] = None
    triage: Optional[ModelTier] = None


class TaskPattern(BaseModel):
    """A pattern for generating tasks."""
    id: str = Field(..., description="Unique identifier for the pattern")
    type: TaskType = Field(..., description="Type of task")
    title: str = Field(..., description="Template for task title")
    description: str = Field(..., description="Template for task description")
    priority: Optional[str] = Field(None, description="Default priority")
    estimate: Optional[str] = Field(None, description="Default estimate (e.g., '3d', '1w')")
    labels: List[str] = Field(default_factory=list, description="Default labels")
    model_hints: ModelHints = Field(default_factory=ModelHints, description="AI model hints")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Sprint(BaseModel):
    """A sprint in the strategy."""
    id: int = Field(..., description="Sprint number")
    name: str = Field(..., description="Sprint name")
    length_days: int = Field(14, description="Sprint length in days")
    objectives: List[str] = Field(default_factory=list, description="Sprint objectives")
    start_date: Optional[str] = Field(None, description="Start date (ISO format)")
    tasks: List[str] = Field(default_factory=list, description="Task pattern IDs for this sprint")


class Goal(BaseModel):
    """Project goal definition."""
    short: str = Field(..., description="Short one-sentence goal")
    quality: List[str] = Field(default_factory=list, description="Quality goals")
    delivery: List[str] = Field(default_factory=list, description="Delivery goals")
    metrics: List[str] = Field(default_factory=list, description="Success metrics")


class QualityGate(BaseModel):
    """Quality gate definition."""
    name: str = Field(..., description="Gate name")
    description: str = Field(..., description="Gate description")
    criteria: List[str] = Field(..., description="Criteria to pass the gate")
    required: bool = Field(True, description="Whether this gate is required")


class Strategy(BaseModel):
    """Main strategy configuration."""
    name: str = Field(..., description="Strategy name")
    version: str = Field("0.1.0", description="Strategy version")
    project_type: str = Field(..., description="Type of project (e.g., 'web', 'mobile', 'api')")
    domain: str = Field(..., description="Business domain")
    goal: Goal = Field(..., description="Project goals")
    description: Optional[str] = Field(None, description="Detailed description")
    
    # Sprint configuration
    sprints: List[Sprint] = Field(default_factory=list, description="Sprints in this strategy")
    
    # Task patterns
    tasks: Dict[str, List[TaskPattern]] = Field(
        default_factory=lambda: {"patterns": []},
        description="Task patterns by category"
    )
    
    # Quality gates
    quality_gates: List[QualityGate] = Field(default_factory=list, description="Quality gates")
    
    # Strategy metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('sprints')
    def validate_sprint_ids(cls, v):
        """Ensure sprint IDs are unique."""
        ids = [sprint.id for sprint in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Sprint IDs must be unique")
        return v
    
    def get_task_patterns(self, category: str = "patterns") -> List[TaskPattern]:
        """Get task patterns by category."""
        return self.tasks.get(category, [])
    
    def get_sprint(self, sprint_id: int) -> Optional[Sprint]:
        """Get sprint by ID."""
        for sprint in self.sprints:
            if sprint.id == sprint_id:
                return sprint
        return None
    
    @classmethod
    def model_validate_yaml(cls, yaml_content: str) -> "Strategy":
        """Load strategy from YAML string."""
        data = yaml.safe_load(yaml_content)
        
        # Convert string enums back to enum values
        def convert_enum_fields(obj, field_type):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == 'type' and isinstance(v, str):
                        if field_type == 'task':
                            obj[k] = TaskType(v)
                    else:
                        convert_enum_fields(v, field_type)
            elif isinstance(obj, list):
                for item in obj:
                    convert_enum_fields(item, field_type)
        
        # Convert task types
        if 'tasks' in data and 'patterns' in data['tasks']:
            for pattern in data['tasks']['patterns']:
                if 'type' in pattern and isinstance(pattern['type'], str):
                    pattern['type'] = TaskType(pattern['type'])
        
        return cls.model_validate(data)
    
    def model_dump_yaml(self) -> str:
        """Dump model to YAML string."""
        data = self.model_dump()
        # Convert enums to strings for YAML
        def convert_enums(obj):
            if isinstance(obj, dict):
                return {k: convert_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enums(item) for item in obj]
            elif hasattr(obj, 'value'):  # Enum
                return obj.value
            else:
                return obj
        
        data = convert_enums(data)
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
