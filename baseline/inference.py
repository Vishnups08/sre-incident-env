"""
Baseline Inference Script for SRE Incident Response Environment.

Uses the OpenAI API to run an LLM agent against the environment.
Reads API key from OPENAI_API_KEY environment variable.
Produces reproducible baseline scores on all 3 tasks.
"""

import os
import json
import sys
from typing import Optional

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
# print(f"DEBUG: sys.path[0] = {sys.path[0]}")
# print(f"DEBUG: parent_dir exists: {os.path.exists(os.path.join(parent_dir, 'env'))}")

from env.environment import SREIncidentEnv
from env.models import Action, ActionType, Observation, Alert, ServiceMetrics, StepResult, Reward, EnvironmentState
from graders.grader import SREGrader
from env.scenarios import get_all_task_ids, get_scenario


SYSTEM_PROMPT = """You are an expert Site Reliability Engineer (SRE) responding to a production incident.

You must investigate the incident by checking logs, metrics, service status, and running diagnostics.
Then apply the correct fix and resolve the incident with the root cause.

Available actions:
- check_logs: View recent logs of a service
- check_metrics: View CPU, memory, latency, error rate metrics
- check_status: Health check all services
- check_config: View service configuration
- restart_service: Restart a service (use carefully!)
- rollback_deploy: Rollback to previous deployment version
- scale_up: Add instances (parameters: {"replicas": N})
- update_config: Update configuration (parameters: {"key": "value"})
- run_diagnostic: Run diagnostic command (parameters: {"command": "..."})
- resolve: Declare root cause and close incident (parameters: {"root_cause": "description"})

Respond with a JSON object:
{
    "thinking": "your reasoning about what to do next",
    "action_type": "one of the action types above",
    "target_service": "service name",
    "parameters": {} or null
}
"""


def run_single_task(env: SREIncidentEnv, grader: SREGrader, task_id: str, api_key: str) -> dict:
    """Run baseline agent on a single task."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except ImportError:
        print("OpenAI package not installed. Using heuristic baseline.")
        return run_heuristic_task(env, grader, task_id)

    obs = env.reset(task_id)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": format_observation(obs)}
    ]

    for step in range(obs.max_steps):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.0,  # Deterministic for reproducibility
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            response_text = response.choices[0].message.content
            action_data = json.loads(response_text)

            action = Action(
                action_type=ActionType(action_data["action_type"]),
                target_service=action_data["target_service"],
                parameters=action_data.get("parameters")
            )

            result = env.step(action)

            # Add to conversation
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": format_step_result(result)})

            if result.done:
                break

        except Exception as e:
            print(f"  Step {step + 1} error: {e}")
            continue

    # Grade
    state = env.state()
    scenario = get_scenario(task_id)
    
    grade_result = grader.grade(
        task_id=task_id,
        ground_truth=scenario["ground_truth"],
        actions_taken=state.actions_taken,
        steps_taken=state.steps_taken,
        max_steps=state.max_steps,
        incident_resolved=state.incident_resolved,
        correct_root_cause=state.correct_root_cause_identified,
        correct_fix=state.correct_fix_applied,
        services_investigated=state.services_investigated,
        services_restarted=[
            a["target_service"] for a in state.actions_taken
            if a["action_type"] in ["restart_service", "rollback_deploy"]
        ]
    )

    return grade_result


def run_heuristic_task(env: SREIncidentEnv, grader: SREGrader, task_id: str) -> dict:
    """Run heuristic baseline for a task."""
    obs = env.reset(task_id)
    
    heuristic_actions = {
        "easy_crashed_deploy": [
            Action(action_type=ActionType.CHECK_STATUS, target_service="payment-service"),
            Action(action_type=ActionType.CHECK_LOGS, target_service="payment-service"),
            Action(action_type=ActionType.ROLLBACK_DEPLOY, target_service="payment-service"),
            Action(action_type=ActionType.RESOLVE, target_service="payment-service",
                   parameters={"root_cause": "bad deployment v2.4.1 null pointer exception"}),
        ],
        "medium_slow_api": [
            Action(action_type=ActionType.CHECK_METRICS, target_service="api-gateway"),
            Action(action_type=ActionType.CHECK_METRICS, target_service="database"),
            Action(action_type=ActionType.CHECK_LOGS, target_service="database"),
            Action(action_type=ActionType.RUN_DIAGNOSTIC, target_service="database",
                   parameters={"command": "show_active_queries"}),
            Action(action_type=ActionType.RUN_DIAGNOSTIC, target_service="database",
                   parameters={"command": "kill_query", "pid": "12847"}),
            Action(action_type=ActionType.RESOLVE, target_service="database",
                   parameters={"root_cause": "database connection pool exhaustion from long running analytics query"}),
        ],
        "hard_cascading_failure": [
            Action(action_type=ActionType.CHECK_STATUS, target_service="api-gateway"),
            Action(action_type=ActionType.CHECK_LOGS, target_service="auth-service"),
            Action(action_type=ActionType.CHECK_LOGS, target_service="user-session-service"),
            Action(action_type=ActionType.RUN_DIAGNOSTIC, target_service="user-session-service"),
            Action(action_type=ActionType.RESTART_SERVICE, target_service="user-session-service"),
            Action(action_type=ActionType.RESOLVE, target_service="user-session-service",
                   parameters={"root_cause": "memory leak in user-session-service caused OOM cascading failure"}),
        ],
    }
    
    actions = heuristic_actions.get(task_id, [])
    for action in actions:
        result = env.step(action)
        if result.done:
            break
    
    state = env.state()
    scenario = get_scenario(task_id)
    
    return grader.grade(
        task_id=task_id,
        ground_truth=scenario["ground_truth"],
        actions_taken=state.actions_taken,
        steps_taken=state.steps_taken,
        max_steps=state.max_steps,
        incident_resolved=state.incident_resolved,
        correct_root_cause=state.correct_root_cause_identified,
        correct_fix=state.correct_fix_applied,
        services_investigated=state.services_investigated,
        services_restarted=[
            a["target_service"] for a in state.actions_taken
            if a["action_type"] in ["restart_service", "rollback_deploy"]
        ]
    )


def format_observation(obs) -> str:
    """Format observation for LLM."""
    parts = [
        f"=== INCIDENT ALERT ===",
        f"Task: {obs.task_id}",
        f"Message: {obs.message}",
        f"\nAlerts:"
    ]
    for alert in obs.alerts:
        parts.append(f"  [{alert.severity.value.upper()}] {alert.service}: {alert.message}")
    
    parts.append(f"\nAvailable services to investigate: {obs.available_services}")
    parts.append(f"Steps remaining: {obs.steps_remaining}/{obs.max_steps}")
    parts.append(f"\nWhat would you like to do? Respond with a JSON action.")
    
    return "\n".join(parts)


def format_step_result(result) -> str:
    """Format step result for LLM."""
    obs = result.observation
    parts = [
        f"=== STEP RESULT ===",
        f"Message: {obs.message}",
        f"Reward: {result.reward.step_reward} (cumulative: {result.reward.cumulative_reward})",
        f"Steps remaining: {obs.steps_remaining}/{obs.max_steps}",
    ]
    
    if obs.logs:
        parts.append(f"\n--- LOGS ---\n{obs.logs}")
    
    if obs.metrics:
        parts.append(f"\n--- METRICS ---")
        for svc, m in obs.metrics.items():
            parts.append(
                f"  {svc}: CPU={m.cpu_percent}%, MEM={m.memory_percent}%, "
                f"ERR={m.error_rate_percent}%, P99={m.latency_p99_ms}ms, "
                f"RPS={m.requests_per_second}, CONN={m.active_connections}"
            )
    
    if obs.service_status:
        parts.append(f"\n--- SERVICE STATUS ---")
        for svc, status in obs.service_status.items():
            parts.append(f"  {svc}: {status}")
    
    if obs.config:
        parts.append(f"\n--- CONFIG ---")
        parts.append(json.dumps(obs.config, indent=2))
    
    if obs.diagnostic_result:
        parts.append(f"\n--- DIAGNOSTIC RESULT ---\n{obs.diagnostic_result}")
    
    if result.done:
        parts.append(f"\n=== EPISODE ENDED ===")
        if "final_score" in result.info:
            parts.append(f"Final score: {result.info['final_score']}")
    else:
        parts.append(f"\nWhat would you like to do next?")
    
    return "\n".join(parts)


class RemoteSREEnv:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.current_state = None

    def reset(self, task_id: str):
        import httpx
        response = httpx.post(f"{self.base_url}/reset", json={"task_id": task_id})
        obs_data = response.json()["observation"]
        
        # Convert dict to models
        if "alerts" in obs_data:
            obs_data["alerts"] = [Alert(**a) for a in obs_data["alerts"]]
        if "metrics" in obs_data and obs_data["metrics"]:
            obs_data["metrics"] = {k: ServiceMetrics(**v) for k, v in obs_data["metrics"].items()}
        
        obs = Observation(**obs_data)
        return obs

    def step(self, action: Action):
        import httpx
        response = httpx.post(f"{self.base_url}/step", json=action.model_dump())
        res_data = response.json()
        
        obs_data = res_data["observation"]
        if "alerts" in obs_data:
            obs_data["alerts"] = [Alert(**a) for a in obs_data["alerts"]]
        if "metrics" in obs_data and obs_data["metrics"]:
            obs_data["metrics"] = {k: ServiceMetrics(**v) for k, v in obs_data["metrics"].items()}
        
        res_data["observation"] = Observation(**obs_data)
        res_data["reward"] = Reward(**res_data["reward"])
        
        return StepResult(**res_data)

    def state(self):
        import httpx
        response = httpx.get(f"{self.base_url}/state")
        return EnvironmentState(**response.json())


class BaselineAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.grader = SREGrader()

    def run_task(self, env, task_id: str):
        if self.api_key:
            return run_single_task(env, self.grader, task_id, self.api_key)
        else:
            return run_heuristic_task(env, self.grader, task_id)


def run_baseline_all_tasks(env, grader_instance, api_key: Optional[str]) -> dict:
    results = {}

    for task_id in get_all_task_ids():
        print(f"\n{'='*50}")
        print(f"Running baseline for: {task_id}")
        print(f"{'='*50}")
        
        if api_key:
            result = run_single_task(env, grader_instance, task_id, api_key)
        else:
            result = run_heuristic_task(env, grader_instance, task_id)
            
        results[task_id] = {
            "score": result["score"],
            "breakdown": result["breakdown"],
            "feedback": result["feedback"],
        }
        
        print(f"Score: {result['score']}")
        print(f"Feedback:\n{result['feedback']}")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, default="all", help="Task ID or 'all'")
    parser.add_argument("--server", type=str, default=None, help="Server URL (e.g. http://localhost:7860)")
    args = parser.parse_args()
    
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if args.server:
        print(f"Connecting to remote server: {args.server}")
        env = RemoteSREEnv(args.server)
    else:
        print("Using local environment.")
        env = SREIncidentEnv()
        
    grader_instance = SREGrader()
    
    if args.task == "all":
        results = run_baseline_all_tasks(env, grader_instance, api_key)
    else:
        if api_key:
            print(f"Running LLM baseline for: {args.task}")
            result = run_single_task(env, grader_instance, args.task, api_key)
        else:
            print(f"Running heuristic baseline for: {args.task}")
            result = run_heuristic_task(env, grader_instance, args.task)
            
        results = {args.task: result}
        print(f"Score: {result['score']}")
        print(f"Feedback:\n{result['feedback']}")
    
    print("\n" + "="*50)
    print("BASELINE RESULTS SUMMARY")
    print("="*50)
    for task_id, result in results.items():
        print(f"  {task_id}: {result['score']}")
    
    if len(results) > 1:
        print(f"\n  Average: {sum(r['score'] for r in results.values()) / len(results):.4f}")
