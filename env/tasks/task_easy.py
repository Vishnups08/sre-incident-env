"""
Task 1: Easy — Crashed After Deploy

Scenario: Payment service deployed a bad version, causing NullPointerExceptions.
The agent needs to check logs, identify it's a bad deployment, and rollback.

Optimal steps: 3
Expected baseline score: 0.7 - 0.9
"""

EASY_TASK_ID = "easy_crashed_deploy"

EASY_TASK_INFO = {
    "task_id": EASY_TASK_ID,
    "name": "Crashed After Deploy",
    "difficulty": "easy",
    "description": (
        "The payment-service was deployed 10 minutes ago and is now "
        "returning HTTP 500 errors. Diagnose and fix the issue."
    ),
    "hints": [
        "Start by checking logs of the alerting service",
        "Look for recent deployments",
        "Consider rollback if deployment caused the issue"
    ],
    "optimal_path": [
        "check_logs(payment-service) → See NullPointerException after v2.4.1 deploy",
        "rollback_deploy(payment-service) → Rollback to v2.4.0",
        "resolve(root_cause='bad deployment v2.4.1 caused null pointer exception')"
    ]
}
