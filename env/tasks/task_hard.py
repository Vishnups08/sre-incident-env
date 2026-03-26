"""
Task 3: Hard — Cascading Failure

Scenario: Memory leak in user-session-service caused OOM crash.
This cascaded: sessions down → auth fails → API retries → notification queue 
backs up → cache pressure. The source service has NO alert.

Optimal steps: 8
Expected baseline score: 0.05 - 0.3
"""

HARD_TASK_ID = "hard_cascading_failure"

HARD_TASK_INFO = {
    "task_id": HARD_TASK_ID,
    "name": "Cascading Failure",
    "difficulty": "hard",
    "description": (
        "Multiple alerts firing: auth failures, API timeouts, notification queue "
        "backup, cache pressure. Find the root cause of this cascading failure."
    ),
    "hints": [
        "Not all alerts point to the root cause — some are symptoms",
        "Look for services that are DOWN, not just degraded",
        "The root cause service might not have an alert",
        "Trace the dependency chain"
    ],
    "optimal_path": [
        "check_status(all) → Notice user-session-service is DOWN",
        "check_logs(user-session-service) → OOM killer, process terminated",
        "check_logs(auth-service) → Cannot reach user-session-service",
        "check_metrics(user-session-service) → 0 everything (it's dead)",
        "run_diagnostic(user-session-service) → Memory leak, OOM at 20:07",
        "restart_service(user-session-service) → Bring it back",
        "update_config(notification-service, clear_queue=true) → Clear queue",
        "resolve(root_cause='memory leak in user-session-service OOM cascading failure')"
    ]
}
