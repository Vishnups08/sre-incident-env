"""
Task 2: Medium — Slow API Responses

Scenario: All API responses are slow because a massive analytics query
on the production database is consuming all connection pool resources.

Optimal steps: 5
Expected baseline score: 0.3 - 0.6
"""

MEDIUM_TASK_ID = "medium_slow_api"

MEDIUM_TASK_INFO = {
    "task_id": MEDIUM_TASK_ID,
    "name": "Slow API Responses",
    "difficulty": "medium",
    "description": (
        "Users reporting extremely slow page loads. API P99 latency at 8+ seconds. "
        "No recent deployments. Find the root cause and fix it."
    ),
    "hints": [
        "Multiple services are slow — look for a common dependency",
        "Check database metrics and connection pool usage",
        "Run diagnostics to find long-running queries"
    ],
    "optimal_path": [
        "check_metrics(api-gateway) → High latency but gateway is fine",
        "check_metrics(database) → CPU 92%, connections 200/200 (full!)",
        "check_logs(database) → See analytics query consuming connections",
        "run_diagnostic(database, command=show_active_queries) → Find the query",
        "run_diagnostic(database, command=kill_query, pid=12847) → Kill it",
        "resolve(root_cause='analytics query exhausted connection pool')"
    ]
}
