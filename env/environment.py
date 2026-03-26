import copy
from typing import Optional, Dict, Any, Tuple

from env.models import (
    Action, ActionType, Observation, Reward, StepResult,
    EnvironmentState, TaskInfo, GroundTruth, Alert, ServiceMetrics
)
from env.scenarios import get_scenario, get_all_task_ids, SCENARIOS


class SREIncidentEnv:
    """
    SRE Incident Response Environment.
    
    An OpenEnv-compatible environment that simulates production incident
    response. The agent must diagnose, investigate, and resolve system
    incidents like a Site Reliability Engineer.
    """

    def __init__(self):
        self.task_id: Optional[str] = None
        self.scenario: Optional[dict] = None
        self.ground_truth: Optional[GroundTruth] = None
        self.episode_active: bool = False
        self.steps_taken: int = 0
        self.max_steps: int = 15
        self.cumulative_reward: float = 0.0
        self.actions_taken: list = []
        self.services_investigated: set = set()
        self.incident_resolved: bool = False
        self.correct_root_cause: bool = False
        self.correct_fix: bool = False
        self.last_observation: Optional[Observation] = None
        self._fix_applied: bool = False
        self._services_restarted: set = set()
        self._configs_updated: dict = {}

    def reset(self, task_id: str = "easy_crashed_deploy") -> Observation:
        """
        Reset the environment to start a new episode.
        
        Args:
            task_id: One of the available task IDs
            
        Returns:
            Initial observation
        """
        self.task_id = task_id
        self.scenario = copy.deepcopy(get_scenario(task_id))
        self.ground_truth = self.scenario["ground_truth"]
        self.episode_active = True
        self.steps_taken = 0
        self.max_steps = self.scenario["max_steps"]
        self.cumulative_reward = 0.0
        self.actions_taken = []
        self.services_investigated = set()
        self.incident_resolved = False
        self.correct_root_cause = False
        self.correct_fix = False
        self._fix_applied = False
        self._services_restarted = set()
        self._configs_updated = {}

        observation = Observation(
            alerts=self.scenario["alerts"],
            available_services=self.scenario["services"],
            logs=None,
            metrics=None,
            service_status=None,
            config=None,
            diagnostic_result=None,
            action_history=[],
            steps_taken=0,
            max_steps=self.max_steps,
            steps_remaining=self.max_steps,
            message=f"INCIDENT ALERT: {self.scenario['name']}. {self.scenario['description']} You have {self.max_steps} steps to investigate and resolve.",
            task_id=task_id
        )
        self.last_observation = observation
        return observation

    def step(self, action: Action) -> StepResult:
        """
        Take an action in the environment.
        
        Args:
            action: The action to take
            
        Returns:
            StepResult containing observation, reward, done flag, and info
        """
        if not self.episode_active:
            return StepResult(
                observation=self._get_terminal_observation("Episode is not active. Call reset() first."),
                reward=Reward(step_reward=0.0, cumulative_reward=self.cumulative_reward, message="Episode not active"),
                done=True,
                info={"error": "Episode not active"}
            )

        self.steps_taken += 1
        self.actions_taken.append({
            "step": self.steps_taken,
            "action_type": action.action_type.value,
            "target_service": action.target_service,
            "parameters": action.parameters
        })

        # Validate service exists
        if action.target_service not in self.scenario["services"]:
            obs = self._get_observation(
                message=f"ERROR: Service '{action.target_service}' does not exist. Available: {self.scenario['services']}"
            )
            reward = self._compute_reward(action, valid=False)
            done = self._check_done()
            return StepResult(observation=obs, reward=reward, done=done, info=self._get_info())

        # Track investigation
        self.services_investigated.add(action.target_service)

        # Process action
        observation = self._process_action(action)
        reward = self._compute_reward(action, valid=True)
        done = self._check_done()

        self.last_observation = observation

        return StepResult(
            observation=observation,
            reward=reward,
            done=done,
            info=self._get_info()
        )

    def state(self) -> EnvironmentState:
        """Return the current environment state."""
        return EnvironmentState(
            task_id=self.task_id or "",
            episode_active=self.episode_active,
            steps_taken=self.steps_taken,
            max_steps=self.max_steps,
            cumulative_reward=self.cumulative_reward,
            actions_taken=self.actions_taken,
            incident_resolved=self.incident_resolved,
            correct_root_cause_identified=self.correct_root_cause,
            correct_fix_applied=self.correct_fix,
            services_investigated=list(self.services_investigated)
        )

    def get_tasks(self) -> list:
        """Return list of available tasks."""
        tasks = []
        for tid, scenario in SCENARIOS.items():
            tasks.append(TaskInfo(
                task_id=tid,
                name=scenario["name"],
                difficulty=scenario["difficulty"],
                description=scenario["description"],
                max_steps=scenario["max_steps"],
                available_actions=[a.value for a in ActionType],
                available_services=scenario["services"]
            ))
        return tasks

    def _process_action(self, action: Action) -> Observation:
        """Process an action and return the resulting observation."""
        target = action.target_service
        message = ""
        logs = None
        metrics = None
        service_status = None
        config = None
        diagnostic_result = None

        if action.action_type == ActionType.CHECK_LOGS:
            logs = self.scenario["logs"].get(target, f"No logs available for {target}")
            message = f"Retrieved logs for {target}"

        elif action.action_type == ActionType.CHECK_METRICS:
            svc_metrics = self.scenario["metrics"].get(target)
            if svc_metrics:
                metrics = {target: svc_metrics}
                message = f"Retrieved metrics for {target}"
            else:
                message = f"No metrics available for {target}"

        elif action.action_type == ActionType.CHECK_STATUS:
            service_status = {}
            for svc in self.scenario["services"]:
                service_status[svc] = self.scenario["service_status"].get(svc, "unknown")
            message = f"Health check results retrieved for all services"

        elif action.action_type == ActionType.CHECK_CONFIG:
            cfg = self.scenario["configs"].get(target)
            if cfg:
                config = {target: cfg}
                message = f"Configuration retrieved for {target}"
            else:
                message = f"No configuration available for {target}"

        elif action.action_type == ActionType.RESTART_SERVICE:
            self._services_restarted.add(target)
            if target == self.ground_truth.correct_fix_target and self.ground_truth.correct_fix_action == ActionType.RESTART_SERVICE:
                self.correct_fix = True
                self._fix_applied = True
                message = f"Service {target} restarted successfully. Service is now recovering."
                # Update status
                self.scenario["service_status"][target] = "recovering"
            elif target in self.ground_truth.red_herring_services:
                message = f"Service {target} restarted, but it was already healthy. Unnecessary restart."
            else:
                message = f"Service {target} restarted."

        elif action.action_type == ActionType.ROLLBACK_DEPLOY:
            if target == self.ground_truth.correct_fix_target and self.ground_truth.correct_fix_action == ActionType.ROLLBACK_DEPLOY:
                self.correct_fix = True
                self._fix_applied = True
                cfg = self.scenario["configs"].get(target, {})
                prev = cfg.get("previous_version", "unknown")
                message = f"Deployment rolled back for {target} to {prev}. Service recovering."
                self.scenario["service_status"][target] = "recovering"
            else:
                message = f"Rollback attempted for {target}, but no recent deployment found or not the fix."

        elif action.action_type == ActionType.SCALE_UP:
            replicas = action.parameters.get("replicas", 2) if action.parameters else 2
            message = f"Scaled up {target} by {replicas} replicas."

        elif action.action_type == ActionType.UPDATE_CONFIG:
            if action.parameters:
                self._configs_updated[target] = action.parameters
                # Check if this is the correct fix for medium task
                if (target == self.ground_truth.correct_fix_target and 
                    self.ground_truth.correct_fix_action == ActionType.UPDATE_CONFIG):
                    if self.ground_truth.correct_fix_params:
                        if any(k in action.parameters for k in self.ground_truth.correct_fix_params):
                            self.correct_fix = True
                            self._fix_applied = True
                            message = f"Configuration updated for {target}. Fix applied."
                        else:
                            message = f"Configuration updated for {target}, but may not resolve the issue."
                    else:
                        message = f"Configuration updated for {target}."
                else:
                    message = f"Configuration updated for {target}."
            else:
                message = f"No parameters provided for config update on {target}."

        elif action.action_type == ActionType.RUN_DIAGNOSTIC:
            diag = self.scenario["diagnostics"].get(target, {})
            command = "default"
            if action.parameters and "command" in action.parameters:
                command = action.parameters["command"]
            diagnostic_result = diag.get(command, diag.get("default", f"No diagnostic available for {target}"))
            message = f"Diagnostic ran on {target}"

            # Check if running diagnostic IS the fix (medium task: kill query)
            if (target == self.ground_truth.correct_fix_target and 
                self.ground_truth.correct_fix_action == ActionType.RUN_DIAGNOSTIC):
                if action.parameters and self.ground_truth.correct_fix_params:
                    if action.parameters.get("command") in ["kill_query", "kill_process"]:
                        self.correct_fix = True
                        self._fix_applied = True
                        message += " Query/process killed. Database connections freeing up."

        elif action.action_type == ActionType.RESOLVE:
            self.incident_resolved = True
            if action.parameters and "root_cause" in action.parameters:
                agent_root_cause = action.parameters["root_cause"].lower()
                # Check if agent identified correct root cause
                match_count = sum(
                    1 for kw in self.ground_truth.root_cause_keywords
                    if kw.lower() in agent_root_cause
                )
                if match_count >= 2:
                    self.correct_root_cause = True
                    message = f"Incident resolved! Root cause correctly identified."
                else:
                    message = f"Incident marked as resolved, but root cause assessment may be incorrect."
            else:
                message = "Incident marked as resolved without root cause identification."

            # End episode on resolve
            self.episode_active = False

        return self._get_observation(
            message=message,
            logs=logs,
            metrics=metrics,
            service_status=service_status,
            config=config,
            diagnostic_result=diagnostic_result
        )

    def _compute_reward(self, action: Action, valid: bool) -> Reward:
        """Compute reward for the action taken."""
        step_reward = 0.0
        breakdown = {}

        if not valid:
            step_reward = -0.05
            breakdown["invalid_action"] = -0.05
        else:
            target = action.target_service

            # Reward for investigating relevant services
            if action.action_type in [ActionType.CHECK_LOGS, ActionType.CHECK_METRICS, 
                                       ActionType.CHECK_STATUS, ActionType.RUN_DIAGNOSTIC,
                                       ActionType.CHECK_CONFIG]:
                if target in self.ground_truth.relevant_services:
                    step_reward += 0.05
                    breakdown["relevant_investigation"] = 0.05
                elif target in self.ground_truth.affected_services:
                    step_reward += 0.02
                    breakdown["affected_investigation"] = 0.02
                elif target in self.ground_truth.red_herring_services:
                    step_reward -= 0.01
                    breakdown["red_herring_investigation"] = -0.01

            # Reward for correct fix
            if action.action_type in [ActionType.RESTART_SERVICE, ActionType.ROLLBACK_DEPLOY,
                                       ActionType.SCALE_UP, ActionType.UPDATE_CONFIG,
                                       ActionType.RUN_DIAGNOSTIC]:
                if self.correct_fix and self._fix_applied:
                    step_reward += 0.25
                    breakdown["correct_fix"] = 0.25
                elif target in self.ground_truth.red_herring_services:
                    step_reward -= 0.10
                    breakdown["unnecessary_action_on_healthy_service"] = -0.10
                elif action.action_type in [ActionType.RESTART_SERVICE, ActionType.ROLLBACK_DEPLOY]:
                    if target not in self.ground_truth.affected_services:
                        step_reward -= 0.08
                        breakdown["destructive_action_wrong_target"] = -0.08

            # Reward for resolve
            if action.action_type == ActionType.RESOLVE:
                if self.correct_root_cause:
                    step_reward += 0.30
                    breakdown["correct_root_cause"] = 0.30
                else:
                    step_reward -= 0.10
                    breakdown["wrong_root_cause"] = -0.10

                if self.correct_fix:
                    step_reward += 0.10
                    breakdown["fix_before_resolve"] = 0.10
                else:
                    step_reward -= 0.05
                    breakdown["resolved_without_fix"] = -0.05

                # Time efficiency bonus
                efficiency = max(0, 1 - (self.steps_taken / self.max_steps))
                efficiency_bonus = efficiency * 0.10
                step_reward += efficiency_bonus
                breakdown["time_efficiency"] = round(efficiency_bonus, 4)

        # Clamp step reward
        step_reward = max(-1.0, min(1.0, step_reward))
        self.cumulative_reward += step_reward

        return Reward(
            step_reward=round(step_reward, 4),
            cumulative_reward=round(self.cumulative_reward, 4),
            breakdown=breakdown,
            message=f"Step {self.steps_taken}/{self.max_steps}"
        )

    def _check_done(self) -> bool:
        """Check if the episode is done."""
        if self.incident_resolved:
            self.episode_active = False
            return True
        if self.steps_taken >= self.max_steps:
            self.episode_active = False
            return True
        return False

    def _get_observation(self, message: str = "", logs=None, metrics=None,
                         service_status=None, config=None, 
                         diagnostic_result=None) -> Observation:
        """Build an observation."""
        return Observation(
            alerts=self.scenario["alerts"],
            available_services=self.scenario["services"],
            logs=logs,
            metrics=metrics,
            service_status=service_status,
            config=config,
            diagnostic_result=diagnostic_result,
            action_history=self.actions_taken,
            steps_taken=self.steps_taken,
            max_steps=self.max_steps,
            steps_remaining=self.max_steps - self.steps_taken,
            message=message,
            task_id=self.task_id
        )

    def _get_terminal_observation(self, message: str) -> Observation:
        """Get observation for terminal state."""
        return Observation(
            alerts=[],
            available_services=[],
            action_history=self.actions_taken,
            steps_taken=self.steps_taken,
            max_steps=self.max_steps,
            steps_remaining=0,
            message=message,
            task_id=self.task_id or ""
        )

    def _get_info(self) -> dict:
        """Get info dict."""
        info = {
            "steps_taken": self.steps_taken,
            "max_steps": self.max_steps,
            "incident_resolved": self.incident_resolved,
            "correct_root_cause": self.correct_root_cause,
            "correct_fix": self.correct_fix,
            "services_investigated": list(self.services_investigated),
            "cumulative_reward": round(self.cumulative_reward, 4)
        }
        if not self.episode_active:
            info["final_score"] = self._compute_final_score()
        return info

    def _compute_final_score(self) -> float:
        """Compute the final score (0.0 - 1.0) for the episode."""
        score = 0.0

        # Root cause identification (30%)
        if self.correct_root_cause:
            score += 0.30

        # Correct fix applied (25%)
        if self.correct_fix:
            score += 0.25

        # Investigation quality (20%)
        relevant_investigated = len(
            self.services_investigated & set(self.ground_truth.relevant_services)
        )
        total_relevant = len(self.ground_truth.relevant_services)
        if total_relevant > 0:
            investigation_score = relevant_investigated / total_relevant
            score += 0.20 * investigation_score

        # Efficiency (15%)
        if self.incident_resolved:
            efficiency = max(0, 1 - (self.steps_taken / (self.max_steps * 1.5)))
            score += 0.15 * efficiency

        # Penalty for unnecessary destructive actions (up to -10%)
        unnecessary_restarts = len(
            self._services_restarted - set(self.ground_truth.affected_services)
        )
        penalty = min(0.10, unnecessary_restarts * 0.03)
        score -= penalty

        # Incident resolved bonus (10%)
        if self.incident_resolved:
            score += 0.10

        return round(max(0.0, min(1.0, score)), 4)
