from env.models import (
    Alert, Severity, ServiceMetrics, GroundTruth, ActionType
)

SCENARIOS = {
    # =========================================================
    # TASK 1: EASY — Crashed After Deploy
    # =========================================================
    "easy_crashed_deploy": {
        "name": "Crashed After Deploy",
        "difficulty": "easy",
        "description": (
            "The payment-service was deployed 10 minutes ago and is now "
            "returning HTTP 500 errors at a high rate. Diagnose the issue "
            "and restore service."
        ),
        "max_steps": 10,
        "services": [
            "api-gateway",
            "payment-service",
            "auth-service",
            "user-service",
            "database"
        ],
        "alerts": [
            Alert(
                severity=Severity.CRITICAL,
                service="payment-service",
                message="HTTP 500 error rate exceeded 5% threshold — currently at 78%",
                timestamp="2024-04-01T14:32:00Z",
                alert_id="ALT-1001"
            ),
            Alert(
                severity=Severity.WARNING,
                service="api-gateway",
                message="Upstream payment-service returning elevated errors",
                timestamp="2024-04-01T14:32:15Z",
                alert_id="ALT-1002"
            )
        ],
        "logs": {
            "payment-service": (
                "[2024-04-01 14:22:00] INFO  Deployment v2.4.1 started\n"
                "[2024-04-01 14:22:05] INFO  Deployment v2.4.1 completed successfully\n"
                "[2024-04-01 14:22:10] INFO  Health check passed\n"
                "[2024-04-01 14:25:30] ERROR NullPointerException at PaymentHandler.java:142\n"
                "[2024-04-01 14:25:30] ERROR   at com.payment.PaymentHandler.processPayment(PaymentHandler.java:142)\n"
                "[2024-04-01 14:25:30] ERROR   at com.payment.PaymentController.handleRequest(PaymentController.java:89)\n"
                "[2024-04-01 14:25:31] ERROR NullPointerException at PaymentHandler.java:142\n"
                "[2024-04-01 14:25:32] ERROR NullPointerException at PaymentHandler.java:142\n"
                "[2024-04-01 14:26:00] WARN  Error rate threshold exceeded: 78%\n"
                "[2024-04-01 14:30:00] ERROR NullPointerException at PaymentHandler.java:142\n"
                "[2024-04-01 14:31:00] ERROR NullPointerException at PaymentHandler.java:142\n"
                "[2024-04-01 14:32:00] CRITICAL Alert triggered: HTTP 500 rate at 78%\n"
            ),
            "api-gateway": (
                "[2024-04-01 14:25:35] WARN  Upstream payment-service returned 500\n"
                "[2024-04-01 14:25:36] WARN  Upstream payment-service returned 500\n"
                "[2024-04-01 14:26:00] WARN  Circuit breaker OPEN for payment-service\n"
                "[2024-04-01 14:30:00] INFO  Retrying payment-service connection\n"
                "[2024-04-01 14:30:01] WARN  Upstream payment-service returned 500\n"
                "[2024-04-01 14:32:15] WARN  Alert: elevated upstream errors from payment-service\n"
            ),
            "auth-service": (
                "[2024-04-01 14:00:00] INFO  Auth-service running normally\n"
                "[2024-04-01 14:15:00] INFO  Token refresh completed for 1,247 sessions\n"
                "[2024-04-01 14:30:00] INFO  Health check passed\n"
            ),
            "user-service": (
                "[2024-04-01 14:00:00] INFO  User-service running normally\n"
                "[2024-04-01 14:20:00] INFO  Cache refreshed: 5,432 user profiles\n"
                "[2024-04-01 14:30:00] INFO  Health check passed\n"
            ),
            "database": (
                "[2024-04-01 14:00:00] INFO  Database running normally\n"
                "[2024-04-01 14:15:00] INFO  Connection pool: 45/200 active\n"
                "[2024-04-01 14:30:00] INFO  Connection pool: 47/200 active\n"
                "[2024-04-01 14:30:00] INFO  Replication lag: 0ms\n"
            ),
        },
        "metrics": {
            "payment-service": ServiceMetrics(
                cpu_percent=2.0,
                memory_percent=45.0,
                error_rate_percent=78.0,
                latency_p99_ms=50.0,
                requests_per_second=120.0,
                active_connections=85
            ),
            "api-gateway": ServiceMetrics(
                cpu_percent=30.0,
                memory_percent=60.0,
                error_rate_percent=35.0,
                latency_p99_ms=2000.0,
                requests_per_second=500.0,
                active_connections=200
            ),
            "auth-service": ServiceMetrics(
                cpu_percent=15.0,
                memory_percent=40.0,
                error_rate_percent=0.1,
                latency_p99_ms=50.0,
                requests_per_second=300.0,
                active_connections=100
            ),
            "user-service": ServiceMetrics(
                cpu_percent=10.0,
                memory_percent=35.0,
                error_rate_percent=0.05,
                latency_p99_ms=30.0,
                requests_per_second=200.0,
                active_connections=80
            ),
            "database": ServiceMetrics(
                cpu_percent=20.0,
                memory_percent=55.0,
                error_rate_percent=0.0,
                latency_p99_ms=5.0,
                requests_per_second=1000.0,
                active_connections=47
            ),
        },
        "service_status": {
            "api-gateway": "healthy",
            "payment-service": "unhealthy",
            "auth-service": "healthy",
            "user-service": "healthy",
            "database": "healthy"
        },
        "configs": {
            "payment-service": {
                "version": "v2.4.1",
                "previous_version": "v2.4.0",
                "deployed_at": "2024-04-01T14:22:00Z",
                "deployed_by": "ci-pipeline",
                "replicas": 3,
                "memory_limit": "512MB",
                "env_vars": {
                    "DB_HOST": "db-primary.internal",
                    "CACHE_TTL": "300",
                    "LOG_LEVEL": "INFO"
                }
            },
            "api-gateway": {
                "version": "v3.1.0",
                "deployed_at": "2024-03-25T10:00:00Z",
                "circuit_breaker_threshold": 50,
                "retry_count": 3,
                "timeout_ms": 5000
            },
            "auth-service": {
                "version": "v1.8.2",
                "deployed_at": "2024-03-20T08:00:00Z",
                "token_ttl_seconds": 3600,
                "max_sessions_per_user": 5
            },
            "user-service": {
                "version": "v2.1.0",
                "deployed_at": "2024-03-28T12:00:00Z",
                "cache_size": 10000,
                "cache_ttl": 600
            },
            "database": {
                "version": "PostgreSQL 15.2",
                "max_connections": 200,
                "connection_pool_size": 200,
                "replication_mode": "synchronous",
                "backup_schedule": "every 6 hours"
            }
        },
        "diagnostics": {
            "payment-service": {
                "default": (
                    "=== Payment Service Diagnostic ===\n"
                    "Status: UNHEALTHY\n"
                    "Last deploy: v2.4.1 at 2024-04-01T14:22:00Z\n"
                    "Previous version: v2.4.0\n"
                    "Error count (last 10m): 4,567\n"
                    "Error type: NullPointerException\n"
                    "Stack trace points to PaymentHandler.java:142\n"
                    "Change in v2.4.1: Refactored payment processing pipeline\n"
                    "RECOMMENDATION: Rollback to v2.4.0\n"
                ),
            },
            "api-gateway": {
                "default": (
                    "=== API Gateway Diagnostic ===\n"
                    "Status: HEALTHY (degraded due to upstream)\n"
                    "Circuit breaker: OPEN for payment-service\n"
                    "Other upstreams: all healthy\n"
                    "No issues with API gateway itself\n"
                )
            },
            "database": {
                "default": (
                    "=== Database Diagnostic ===\n"
                    "Status: HEALTHY\n"
                    "Active connections: 47/200\n"
                    "Slow queries: 0\n"
                    "Replication lag: 0ms\n"
                    "No issues detected\n"
                ),
                "show_active_queries": (
                    "=== Active Queries ===\n"
                    "1. SELECT * FROM payments WHERE status='pending' (2ms)\n"
                    "2. SELECT user_id FROM sessions WHERE active=true (1ms)\n"
                    "3. INSERT INTO audit_log VALUES (...) (3ms)\n"
                    "No long-running queries detected.\n"
                )
            }
        },
        "ground_truth": GroundTruth(
            root_cause="bad_deployment_null_pointer_exception_v2.4.1",
            root_cause_keywords=[
                "deploy", "deployment", "null", "nullpointer",
                "v2.4.1", "rollback", "payment", "exception",
                "bug", "code", "regression"
            ],
            correct_fix_action=ActionType.ROLLBACK_DEPLOY,
            correct_fix_target="payment-service",
            affected_services=["payment-service", "api-gateway"],
            relevant_services=["payment-service"],
            red_herring_services=["auth-service", "user-service", "database"],
            optimal_steps=3
        )
    },

    # =========================================================
    # TASK 2: MEDIUM — Slow API Responses
    # =========================================================
    "medium_slow_api": {
        "name": "Slow API Responses",
        "difficulty": "medium",
        "description": (
            "Users are reporting extremely slow page loads. API response "
            "times have spiked to 8+ seconds (normally 200ms). No recent "
            "deployments have been made. Find the root cause and fix it."
        ),
        "max_steps": 12,
        "services": [
            "api-gateway",
            "auth-service",
            "user-service",
            "order-service",
            "database",
            "cache-redis"
        ],
        "alerts": [
            Alert(
                severity=Severity.CRITICAL,
                service="api-gateway",
                message="P99 latency exceeded 5000ms threshold — currently at 8200ms",
                timestamp="2024-04-01T16:45:00Z",
                alert_id="ALT-2001"
            ),
            Alert(
                severity=Severity.WARNING,
                service="auth-service",
                message="Elevated response times detected — p99 at 3000ms",
                timestamp="2024-04-01T16:45:30Z",
                alert_id="ALT-2002"
            ),
            Alert(
                severity=Severity.WARNING,
                service="order-service",
                message="Request timeout rate at 15%",
                timestamp="2024-04-01T16:46:00Z",
                alert_id="ALT-2003"
            )
        ],
        "logs": {
            "api-gateway": (
                "[2024-04-01 16:40:00] INFO  Request processing normally\n"
                "[2024-04-01 16:42:00] WARN  Slow response from auth-service: 2500ms\n"
                "[2024-04-01 16:42:30] WARN  Slow response from order-service: 3200ms\n"
                "[2024-04-01 16:43:00] WARN  Slow response from user-service: 2800ms\n"
                "[2024-04-01 16:44:00] ERROR Request timeout after 5000ms\n"
                "[2024-04-01 16:44:30] ERROR Request timeout after 5000ms\n"
                "[2024-04-01 16:45:00] CRITICAL P99 latency at 8200ms\n"
            ),
            "auth-service": (
                "[2024-04-01 16:40:00] INFO  Processing auth requests normally\n"
                "[2024-04-01 16:42:00] WARN  Database query slow: 2000ms for session lookup\n"
                "[2024-04-01 16:43:00] WARN  Database connection wait time: 1500ms\n"
                "[2024-04-01 16:44:00] ERROR Database connection timeout\n"
                "[2024-04-01 16:45:00] WARN  Falling back to cache for session validation\n"
            ),
            "user-service": (
                "[2024-04-01 16:40:00] INFO  User-service running normally\n"
                "[2024-04-01 16:42:00] WARN  Database query slow: 1800ms\n"
                "[2024-04-01 16:43:00] WARN  Database connection pool wait: 2000ms\n"
                "[2024-04-01 16:44:00] ERROR Cannot acquire database connection\n"
            ),
            "order-service": (
                "[2024-04-01 16:40:00] INFO  Order-service running normally\n"
                "[2024-04-01 16:42:00] WARN  Database query slow: 3000ms\n"
                "[2024-04-01 16:43:00] ERROR Database connection pool exhausted\n"
                "[2024-04-01 16:44:00] ERROR Request timeout waiting for DB connection\n"
                "[2024-04-01 16:45:00] WARN  15% of requests timing out\n"
            ),
            "database": (
                "[2024-04-01 15:30:00] INFO  Database running normally\n"
                "[2024-04-01 15:35:00] INFO  New connection from analytics-user@10.0.5.22\n"
                "[2024-04-01 15:35:01] INFO  Query started: SELECT o.*, u.name, p.* FROM orders o "
                "JOIN users u ON o.user_id = u.id JOIN payments p ON o.id = p.order_id "
                "JOIN order_items oi ON o.id = oi.order_id WHERE o.created_at > '2023-01-01' "
                "ORDER BY o.created_at — estimated rows: 45,000,000\n"
                "[2024-04-01 16:00:00] WARN  Connection pool usage: 150/200\n"
                "[2024-04-01 16:30:00] WARN  Connection pool usage: 185/200\n"
                "[2024-04-01 16:40:00] CRITICAL Connection pool usage: 198/200\n"
                "[2024-04-01 16:42:00] CRITICAL Connection pool EXHAUSTED: 200/200\n"
                "[2024-04-01 16:42:00] WARN  Queries queueing for connections\n"
                "[2024-04-01 16:45:00] CRITICAL 47 queries waiting for connections\n"
            ),
            "cache-redis": (
                "[2024-04-01 16:40:00] INFO  Redis running normally\n"
                "[2024-04-01 16:42:00] INFO  Hit rate: 94%\n"
                "[2024-04-01 16:44:00] INFO  Hit rate: 91% (slightly lower due to increased traffic)\n"
                "[2024-04-01 16:45:00] WARN  Eviction rate increased: cache pressure from fallback queries\n"
            )
        },
        "metrics": {
            "api-gateway": ServiceMetrics(
                cpu_percent=45.0,
                memory_percent=60.0,
                error_rate_percent=15.0,
                latency_p99_ms=8200.0,
                requests_per_second=450.0,
                active_connections=350
            ),
            "auth-service": ServiceMetrics(
                cpu_percent=20.0,
                memory_percent=50.0,
                error_rate_percent=8.0,
                latency_p99_ms=3000.0,
                requests_per_second=280.0,
                active_connections=150
            ),
            "user-service": ServiceMetrics(
                cpu_percent=15.0,
                memory_percent=45.0,
                error_rate_percent=12.0,
                latency_p99_ms=2800.0,
                requests_per_second=180.0,
                active_connections=120
            ),
            "order-service": ServiceMetrics(
                cpu_percent=25.0,
                memory_percent=55.0,
                error_rate_percent=15.0,
                latency_p99_ms=5000.0,
                requests_per_second=100.0,
                active_connections=90
            ),
            "database": ServiceMetrics(
                cpu_percent=92.0,
                memory_percent=85.0,
                error_rate_percent=0.0,
                latency_p99_ms=3500.0,
                requests_per_second=2000.0,
                active_connections=200
            ),
            "cache-redis": ServiceMetrics(
                cpu_percent=10.0,
                memory_percent=70.0,
                error_rate_percent=0.0,
                latency_p99_ms=2.0,
                requests_per_second=5000.0,
                active_connections=100
            )
        },
        "service_status": {
            "api-gateway": "degraded",
            "auth-service": "degraded",
            "user-service": "degraded",
            "order-service": "degraded",
            "database": "healthy",
            "cache-redis": "healthy"
        },
        "configs": {
            "api-gateway": {
                "version": "v3.1.0",
                "deployed_at": "2024-03-25T10:00:00Z",
                "timeout_ms": 5000,
                "max_retries": 3
            },
            "auth-service": {
                "version": "v1.8.2",
                "deployed_at": "2024-03-20T08:00:00Z",
                "db_pool_size": 30,
                "db_timeout_ms": 5000
            },
            "user-service": {
                "version": "v2.1.0",
                "deployed_at": "2024-03-28T12:00:00Z",
                "db_pool_size": 25,
                "db_timeout_ms": 5000
            },
            "order-service": {
                "version": "v4.2.0",
                "deployed_at": "2024-03-15T09:00:00Z",
                "db_pool_size": 40,
                "db_timeout_ms": 5000
            },
            "database": {
                "version": "PostgreSQL 15.2",
                "max_connections": 200,
                "connection_pool_size": 200,
                "slow_query_threshold_ms": 1000,
                "statement_timeout_ms": 0,
                "max_parallel_workers": 4
            },
            "cache-redis": {
                "version": "Redis 7.2",
                "max_memory": "2GB",
                "eviction_policy": "allkeys-lru",
                "max_connections": 1000
            }
        },
        "diagnostics": {
            "api-gateway": {
                "default": (
                    "=== API Gateway Diagnostic ===\n"
                    "Status: DEGRADED\n"
                    "All upstreams reporting slow responses\n"
                    "No issues with gateway itself\n"
                    "Root cause appears to be downstream\n"
                )
            },
            "auth-service": {
                "default": (
                    "=== Auth Service Diagnostic ===\n"
                    "Status: DEGRADED\n"
                    "Database queries are slow\n"
                    "Waiting for database connections\n"
                    "Service code is healthy — DB dependency is the bottleneck\n"
                )
            },
            "database": {
                "default": (
                    "=== Database Diagnostic ===\n"
                    "Status: HEALTHY but OVERLOADED\n"
                    "Connection pool: 200/200 (FULL)\n"
                    "CPU: 92%\n"
                    "47 queries waiting for connections\n"
                    "Run 'show_active_queries' for details\n"
                ),
                "show_active_queries": (
                    "=== Active Queries (Top 10 by Duration) ===\n"
                    "1. [RUNNING 1h 10m] analytics-user@10.0.5.22: "
                    "SELECT o.*, u.name, p.* FROM orders o JOIN users u ON o.user_id = u.id "
                    "JOIN payments p ON o.id = p.order_id JOIN order_items oi ON o.id = oi.order_id "
                    "WHERE o.created_at > '2023-01-01' ORDER BY o.created_at "
                    "— scanning 45,000,000 rows, holding 150 connections\n"
                    "2. [RUNNING 3s] app-user: SELECT * FROM users WHERE id = 1234 (waiting for connection)\n"
                    "3. [RUNNING 2s] app-user: SELECT * FROM orders WHERE user_id = 5678 (waiting for connection)\n"
                    "4. [RUNNING 2s] app-user: SELECT session FROM sessions WHERE token = 'abc' (waiting for connection)\n"
                    "... 43 more queries waiting\n"
                    "\nROOT CAUSE: Query #1 is a massive analytics query running on production DB, "
                    "consuming 150 connections and causing pool exhaustion.\n"
                    "PID: 12847\n"
                ),
                "show_connections": (
                    "=== Connection Breakdown ===\n"
                    "analytics-user@10.0.5.22: 150 connections (!!)\n"
                    "auth-service: 25 connections\n"
                    "user-service: 12 connections\n"
                    "order-service: 10 connections\n"
                    "other: 3 connections\n"
                    "TOTAL: 200/200\n"
                )
            },
            "order-service": {
                "default": (
                    "=== Order Service Diagnostic ===\n"
                    "Status: DEGRADED\n"
                    "Cannot acquire database connections\n"
                    "Service code is healthy — DB dependency is the bottleneck\n"
                )
            },
            "cache-redis": {
                "default": (
                    "=== Redis Cache Diagnostic ===\n"
                    "Status: HEALTHY\n"
                    "Memory: 70%\n"
                    "Hit rate: 91%\n"
                    "Slightly elevated eviction rate due to fallback queries\n"
                    "No issues with Redis itself\n"
                )
            }
        },
        "ground_truth": GroundTruth(
            root_cause="database_connection_pool_exhaustion_from_analytics_query",
            root_cause_keywords=[
                "connection", "pool", "exhaustion", "exhausted",
                "analytics", "query", "long-running", "database",
                "kill", "pid", "12847", "45000000"
            ],
            correct_fix_action=ActionType.RUN_DIAGNOSTIC,
            correct_fix_target="database",
            correct_fix_params={"command": "kill_query", "pid": "12847"},
            affected_services=["database", "auth-service", "user-service", "order-service", "api-gateway"],
            relevant_services=["database"],
            red_herring_services=["cache-redis", "api-gateway"],
            optimal_steps=5
        )
    },

    # =========================================================
    # TASK 3: HARD — Cascading Failure
    # =========================================================
    "hard_cascading_failure": {
        "name": "Cascading Failure",
        "difficulty": "hard",
        "description": (
            "Multiple alerts are firing simultaneously across different services. "
            "Users cannot log in, API requests are timing out, notifications are "
            "backed up, and cache eviction rates are abnormal. Find the root cause "
            "of this cascading failure and resolve it."
        ),
        "max_steps": 15,
        "services": [
            "api-gateway",
            "auth-service",
            "user-session-service",
            "notification-service",
            "cache-redis",
            "database",
            "load-balancer"
        ],
        "alerts": [
            Alert(
                severity=Severity.CRITICAL,
                service="auth-service",
                message="Authentication failure rate at 65% — users cannot log in",
                timestamp="2024-04-01T20:15:00Z",
                alert_id="ALT-3001"
            ),
            Alert(
                severity=Severity.CRITICAL,
                service="api-gateway",
                message="Connection timeout rate at 40% — P99 latency 12000ms",
                timestamp="2024-04-01T20:15:30Z",
                alert_id="ALT-3002"
            ),
            Alert(
                severity=Severity.WARNING,
                service="notification-service",
                message="Message queue depth exceeded 50,000 — queue is backing up",
                timestamp="2024-04-01T20:16:00Z",
                alert_id="ALT-3003"
            ),
            Alert(
                severity=Severity.WARNING,
                service="cache-redis",
                message="Eviction rate 10x normal — memory pressure detected",
                timestamp="2024-04-01T20:16:30Z",
                alert_id="ALT-3004"
            )
        ],
        "logs": {
            "api-gateway": (
                "[2024-04-01 20:10:00] INFO  Request processing normally\n"
                "[2024-04-01 20:12:00] WARN  auth-service returning 503 for 30% of requests\n"
                "[2024-04-01 20:13:00] WARN  Retry storm detected — auth failures causing retries\n"
                "[2024-04-01 20:14:00] ERROR Connection pool to auth-service near capacity\n"
                "[2024-04-01 20:15:00] CRITICAL Timeout rate at 40%\n"
                "[2024-04-01 20:15:30] ERROR Retry queue depth: 15,000\n"
            ),
            "auth-service": (
                "[2024-04-01 20:10:00] INFO  Auth-service running normally\n"
                "[2024-04-01 20:11:00] WARN  Session validation failed — user-session-service unreachable\n"
                "[2024-04-01 20:11:30] ERROR Cannot connect to user-session-service: Connection refused\n"
                "[2024-04-01 20:12:00] ERROR Session validation fallback failed — no cached sessions\n"
                "[2024-04-01 20:12:30] WARN  Returning 503 for requests requiring session validation\n"
                "[2024-04-01 20:13:00] ERROR Auth failure rate: 45%\n"
                "[2024-04-01 20:14:00] ERROR Auth failure rate: 58%\n"
                "[2024-04-01 20:15:00] CRITICAL Auth failure rate: 65%\n"
                "[2024-04-01 20:15:00] INFO  Attempting reconnect to user-session-service...\n"
                "[2024-04-01 20:15:01] ERROR Reconnect failed: Connection refused\n"
            ),
            "user-session-service": (
                "[2024-04-01 19:00:00] INFO  Session service running normally\n"
                "[2024-04-01 19:30:00] INFO  Active sessions: 45,000\n"
                "[2024-04-01 19:45:00] WARN  Memory usage: 75%\n"
                "[2024-04-01 20:00:00] WARN  Memory usage: 88%\n"
                "[2024-04-01 20:05:00] ERROR Memory usage: 95% — GC unable to free memory\n"
                "[2024-04-01 20:07:00] ERROR java.lang.OutOfMemoryError: Java heap space\n"
                "[2024-04-01 20:07:00] ERROR   at com.sessions.SessionStore.addSession(SessionStore.java:89)\n"
                "[2024-04-01 20:07:00] ERROR   at com.sessions.SessionManager.createSession(SessionManager.java:45)\n"
                "[2024-04-01 20:07:01] FATAL Process killed by OOM killer (PID 8847)\n"
                "[2024-04-01 20:07:01] FATAL Service terminated\n"
            ),
            "notification-service": (
                "[2024-04-01 20:12:00] INFO  Processing notifications normally\n"
                "[2024-04-01 20:13:00] WARN  Incoming retry notifications from api-gateway surge\n"
                "[2024-04-01 20:14:00] WARN  Queue depth: 25,000 (normally 500)\n"
                "[2024-04-01 20:15:00] ERROR Queue depth: 50,000 — cannot keep up\n"
                "[2024-04-01 20:15:30] ERROR Failed notification delivery — auth-service returning 503\n"
                "[2024-04-01 20:16:00] WARN  Queue depth: 52,000 and growing\n"
                "[2024-04-01 20:16:00] WARN  Dead letter queue growing: 8,000 messages\n"
            ),
            "cache-redis": (
                "[2024-04-01 20:12:00] INFO  Redis running normally\n"
                "[2024-04-01 20:13:00] WARN  Sudden spike in GET requests — 10x normal rate\n"
                "[2024-04-01 20:13:30] INFO  Cache miss rate increasing — sessions not in cache\n"
                "[2024-04-01 20:14:00] WARN  Memory pressure — eviction rate 10x normal\n"
                "[2024-04-01 20:15:00] WARN  Eviction rate still elevated\n"
                "[2024-04-01 20:16:00] INFO  Requests are retry storms from auth-service session lookups\n"
            ),
            "database": (
                "[2024-04-01 20:10:00] INFO  Database running normally\n"
                "[2024-04-01 20:13:00] INFO  Slight increase in query rate\n"
                "[2024-04-01 20:15:00] INFO  Connection pool: 85/200\n"
                "[2024-04-01 20:16:00] INFO  Database healthy — no issues detected\n"
            ),
            "load-balancer": (
                "[2024-04-01 20:10:00] INFO  Load balancer healthy\n"
                "[2024-04-01 20:12:00] WARN  Backend auth-service health check failing for 1/3 instances\n"
                "[2024-04-01 20:15:00] INFO  Redistributing traffic to healthy auth-service instances\n"
                "[2024-04-01 20:16:00] WARN  All auth-service instances showing degraded performance\n"
            )
        },
        "metrics": {
            "api-gateway": ServiceMetrics(
                cpu_percent=75.0,
                memory_percent=70.0,
                error_rate_percent=40.0,
                latency_p99_ms=12000.0,
                requests_per_second=800.0,
                active_connections=500
            ),
            "auth-service": ServiceMetrics(
                cpu_percent=85.0,
                memory_percent=75.0,
                error_rate_percent=65.0,
                latency_p99_ms=8000.0,
                requests_per_second=400.0,
                active_connections=300
            ),
            "user-session-service": ServiceMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                error_rate_percent=100.0,
                latency_p99_ms=0.0,
                requests_per_second=0.0,
                active_connections=0
            ),
            "notification-service": ServiceMetrics(
                cpu_percent=90.0,
                memory_percent=80.0,
                error_rate_percent=30.0,
                latency_p99_ms=5000.0,
                requests_per_second=50.0,
                active_connections=200
            ),
            "cache-redis": ServiceMetrics(
                cpu_percent=60.0,
                memory_percent=92.0,
                error_rate_percent=0.0,
                latency_p99_ms=15.0,
                requests_per_second=20000.0,
                active_connections=500
            ),
            "database": ServiceMetrics(
                cpu_percent=30.0,
                memory_percent=55.0,
                error_rate_percent=0.0,
                latency_p99_ms=8.0,
                requests_per_second=1200.0,
                active_connections=85
            ),
            "load-balancer": ServiceMetrics(
                cpu_percent=20.0,
                memory_percent=30.0,
                error_rate_percent=0.0,
                latency_p99_ms=1.0,
                requests_per_second=2000.0,
                active_connections=1000
            )
        },
        "service_status": {
            "api-gateway": "degraded",
            "auth-service": "degraded",
            "user-session-service": "down",
            "notification-service": "degraded",
            "cache-redis": "healthy",
            "database": "healthy",
            "load-balancer": "healthy"
        },
        "configs": {
            "api-gateway": {
                "version": "v3.1.0",
                "retry_count": 3,
                "retry_backoff_ms": 100,
                "timeout_ms": 5000,
                "circuit_breaker_threshold": 60
            },
            "auth-service": {
                "version": "v1.8.2",
                "session_validation_required": True,
                "session_service_url": "http://user-session-service:8080",
                "session_cache_fallback": True,
                "session_cache_ttl": 300
            },
            "user-session-service": {
                "version": "v1.2.0",
                "deployed_at": "2024-03-10T10:00:00Z",
                "jvm_heap_size": "256MB",
                "max_sessions": 100000,
                "session_cleanup_interval_minutes": 60,
                "replicas": 1
            },
            "notification-service": {
                "version": "v2.0.1",
                "queue_max_depth": 100000,
                "retry_on_failure": True,
                "max_retries": 5,
                "dead_letter_queue_enabled": True
            },
            "cache-redis": {
                "version": "Redis 7.2",
                "max_memory": "2GB",
                "eviction_policy": "allkeys-lru"
            },
            "database": {
                "version": "PostgreSQL 15.2",
                "max_connections": 200,
                "connection_pool_size": 200
            },
            "load-balancer": {
                "version": "nginx 1.25",
                "health_check_interval": 10,
                "backend_timeout": 30
            }
        },
        "diagnostics": {
            "api-gateway": {
                "default": (
                    "=== API Gateway Diagnostic ===\n"
                    "Status: DEGRADED\n"
                    "High retry rate due to auth-service failures\n"
                    "Retry storm amplifying the problem\n"
                    "Gateway itself is healthy\n"
                )
            },
            "auth-service": {
                "default": (
                    "=== Auth Service Diagnostic ===\n"
                    "Status: DEGRADED\n"
                    "Cannot reach user-session-service for session validation\n"
                    "Connection refused on user-session-service:8080\n"
                    "Falling back to cache but cache hit rate dropping\n"
                    "Dependency: user-session-service is REQUIRED\n"
                )
            },
            "user-session-service": {
                "default": (
                    "=== User Session Service Diagnostic ===\n"
                    "Status: DOWN\n"
                    "Process not running (killed by OOM)\n"
                    "Last log: OutOfMemoryError at 20:07:00\n"
                    "JVM heap: 256MB (insufficient for 45,000 active sessions)\n"
                    "Memory grew steadily over 1 hour before OOM\n"
                    "Session cleanup job not keeping up with session creation rate\n"
                    "RECOMMENDATION: Restart service, increase heap size to 512MB+\n"
                    "ROOT CAUSE: Memory leak in SessionStore — sessions not being cleaned up\n"
                )
            },
            "notification-service": {
                "default": (
                    "=== Notification Service Diagnostic ===\n"
                    "Status: DEGRADED\n"
                    "Queue depth: 52,000\n"
                    "Incoming: retry notifications from API gateway\n"
                    "Failed deliveries because auth-service is down\n"
                    "Queue will recover once auth-service recovers\n"
                    "Dead letter queue: 8,000 messages\n"
                ),
                "show_queue": (
                    "=== Queue Details ===\n"
                    "Total messages: 52,000\n"
                    "Failed delivery: 35,000\n"
                    "Pending: 17,000\n"
                    "Dead letter: 8,000\n"
                    "Oldest message: 6 minutes ago\n"
                    "Most messages are retry/error notifications from API gateway\n"
                )
            },
            "cache-redis": {
                "default": (
                    "=== Redis Cache Diagnostic ===\n"
                    "Status: HEALTHY (under pressure)\n"
                    "Memory: 92% (high)\n"
                    "Spike in GET requests for session keys\n"
                    "Auth-service is hammering cache for session validation fallback\n"
                    "Cache itself is fine — the problem is upstream\n"
                )
            },
            "database": {
                "default": (
                    "=== Database Diagnostic ===\n"
                    "Status: HEALTHY\n"
                    "Connection pool: 85/200\n"
                    "No slow queries\n"
                    "No issues detected\n"
                )
            },
            "load-balancer": {
                "default": (
                    "=== Load Balancer Diagnostic ===\n"
                    "Status: HEALTHY\n"
                    "Routing traffic normally\n"
                    "Auth-service backends showing degraded health\n"
                    "Load balancer itself is fine\n"
                )
            }
        },
        "ground_truth": GroundTruth(
            root_cause="memory_leak_user_session_service_oom_cascading_failure",
            root_cause_keywords=[
                "memory", "leak", "oom", "out of memory", "session",
                "user-session-service", "heap", "crash", "killed",
                "cascading", "cascade"
            ],
            correct_fix_action=ActionType.RESTART_SERVICE,
            correct_fix_target="user-session-service",
            correct_fix_params=None,
            affected_services=[
                "user-session-service", "auth-service",
                "api-gateway", "notification-service", "cache-redis"
            ],
            relevant_services=["user-session-service", "auth-service"],
            red_herring_services=["cache-redis", "database", "load-balancer", "notification-service"],
            optimal_steps=8
        )
    }
}


def get_scenario(task_id: str) -> dict:
    """Get a scenario by task ID."""
    if task_id not in SCENARIOS:
        raise ValueError(f"Unknown task_id: {task_id}. Available: {list(SCENARIOS.keys())}")
    return SCENARIOS[task_id]


def get_all_task_ids() -> list:
    """Get all available task IDs."""
    return list(SCENARIOS.keys())
