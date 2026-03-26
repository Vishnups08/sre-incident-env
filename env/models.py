from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ActionType(str, Enum):
    CHECK_LOGS = "check_logs"
    CHECK_METRICS = "check_metrics"
    CHECK_STATUS = "check_status"
    CHECK_CONFIG = "check_config"
    RESTART_SERVICE = "restart_service"
    ROLLBACK_DEPLOY = "rollback_deploy"
    SCALE_UP = "scale_up"
    UPDATE_CONFIG = "update_config"
    RUN_DIAGNOSTIC = "run_diagnostic"
    RESOLVE = "resolve"


class Alert(BaseModel):
    """Represents a production alert that triggers the incident."""
    severity: Severity
    service: str
    message: str
    timestamp: str
    alert_id: str


class ServiceMetrics(BaseModel):
    """Metrics for a specific service."""
    cpu_percent: float = Field(ge=0, le=100)
    memory_percent: float = Field(ge=0, le=100)
    error_rate_percent: float = Field(ge=0, le=100)
    latency_p99_ms: float = Field(ge=0)
    requests_per_second: float = Field(ge=0)
    active_connections: int = Field(ge=0)


class Action(BaseModel):
    """Action the agent can take in the environment."""
    action_type: ActionType
    target_service: str
    parameters: Optional[Dict[str, Any]] = None


class Observation(BaseModel):
    """What the agent sees after each step."""
    alerts: List[Alert]
    available_services: List[str]
    logs: Optional[str] = None
    metrics: Optional[Dict[str, ServiceMetrics]] = None
    service_status: Optional[Dict[str, str]] = None
    config: Optional[Dict[str, Any]] = None
    diagnostic_result: Optional[str] = None
    action_history: List[Dict[str, Any]] = []
    steps_taken: int = 0
    max_steps: int = 15
    steps_remaining: int = 15
    message: str = ""
    task_id: str = ""


class Reward(BaseModel):
    """Reward signal returned after each step."""
    step_reward: float = Field(ge=-1.0, le=1.0)
    cumulative_reward: float
    breakdown: Dict[str, float] = {}
    message: str = ""


class StepResult(BaseModel):
    """Complete result of a step."""
    observation: Observation
    reward: Reward
    done: bool
    info: Dict[str, Any] = {}


class EnvironmentState(BaseModel):
    """Full environment state."""
    task_id: str
    episode_active: bool
    steps_taken: int
    max_steps: int
    cumulative_reward: float
    actions_taken: List[Dict[str, Any]]
    incident_resolved: bool
    correct_root_cause_identified: bool
    correct_fix_applied: bool
    services_investigated: List[str]


class TaskInfo(BaseModel):
    """Information about a task."""
    task_id: str
    name: str
    difficulty: str
    description: str
    max_steps: int
    available_actions: List[str]
    available_services: List[str]


class GroundTruth(BaseModel):
    """The actual correct answers for a scenario. Used internally for grading."""
    root_cause: str
    root_cause_keywords: List[str]
    correct_fix_action: ActionType
    correct_fix_target: str
    correct_fix_params: Optional[Dict[str, Any]] = None
    affected_services: List[str]
    relevant_services: List[str]
    red_herring_services: List[str] = []
    optimal_steps: int
