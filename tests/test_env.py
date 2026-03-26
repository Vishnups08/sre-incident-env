"""
Tests for SRE Incident Response Environment.
Validates OpenEnv spec compliance and grader correctness.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.environment import SREIncidentEnv
from env.models import Action, ActionType
from graders.grader import SREGrader
from env.scenarios import get_all_task_ids, get_scenario


def test_reset():
    """Test that reset() returns clean initial state."""
    env = SREIncidentEnv()
    
    for task_id in get_all_task_ids():
        obs = env.reset(task_id)
        assert obs.task_id == task_id
        assert obs.steps_taken == 0
        assert obs.steps_remaining > 0
        assert len(obs.alerts) > 0
        assert len(obs.available_services) > 0
        assert obs.logs is None
        assert obs.metrics is None
        assert len(obs.action_history) == 0
        print(f"  ✅ reset() works for {task_id}")
    
    print("✅ test_reset passed")


def test_step_returns_correct_types():
    """Test that step() returns proper types."""
    env = SREIncidentEnv()
    
    for task_id in get_all_task_ids():
        obs = env.reset(task_id)
        action = Action(
            action_type=ActionType.CHECK_STATUS,
            target_service=obs.available_services[0]
        )
        result = env.step(action)
        
        assert result.observation is not None
        assert result.reward is not None
        assert isinstance(result.done, bool)
        assert isinstance(result.info, dict)
        assert result.observation.steps_taken == 1
        assert result.reward.step_reward >= -1.0
        assert result.reward.step_reward <= 1.0
        print(f"  ✅ step() returns correct types for {task_id}")
    
    print("✅ test_step_returns_correct_types passed")


def test_state():
    """Test that state() returns current state."""
    env = SREIncidentEnv()
    env.reset("easy_crashed_deploy")
    
    state = env.state()
    assert state.task_id == "easy_crashed_deploy"
    assert state.episode_active == True
    assert state.steps_taken == 0
    assert state.cumulative_reward == 0.0
    
    action = Action(action_type=ActionType.CHECK_LOGS, target_service="payment-service")
    env.step(action)
    
    state = env.state()
    assert state.steps_taken == 1
    assert len(state.actions_taken) == 1
    assert "payment-service" in state.services_investigated
    
    print("✅ test_state passed")


def test_check_logs():
    """Test log retrieval."""
    env = SREIncidentEnv()
    env.reset("easy_crashed_deploy")
    
    action = Action(action_type=ActionType.CHECK_LOGS, target_service="payment-service")
    result = env.step(action)
    
    assert result.observation.logs is not None
    assert "NullPointerException" in result.observation.logs
    
    print("✅ test_check_logs passed")


def test_check_metrics():
    """Test metrics retrieval."""
    env = SREIncidentEnv()
    env.reset("easy_crashed_deploy")
    
    action = Action(action_type=ActionType.CHECK_METRICS, target_service="payment-service")
    result = env.step(action)
    
    assert result.observation.metrics is not None
    assert "payment-service" in result.observation.metrics
    metrics = result.observation.metrics["payment-service"]
    assert metrics.error_rate_percent == 78.0
    
    print("✅ test_check_metrics passed")


def test_check_status():
    """Test status check."""
    env = SREIncidentEnv()
    env.reset("easy_crashed_deploy")
    
    action = Action(action_type=ActionType.CHECK_STATUS, target_service="payment-service")
    result = env.step(action)
    
    assert result.observation.service_status is not None
    assert result.observation.service_status["payment-service"] == "unhealthy"
    assert result.observation.service_status["auth-service"] == "healthy"
    
    print("✅ test_check_status passed")


def test_easy_task_optimal():
    """Test optimal path for easy task."""
    env = SREIncidentEnv()
    env.reset("easy_crashed_deploy")
    
    # Step 1: Check logs
    result = env.step(Action(
        action_type=ActionType.CHECK_LOGS,
        target_service="payment-service"
    ))
    assert not result.done
    
    # Step 2: Rollback
    result = env.step(Action(
        action_type=ActionType.ROLLBACK_DEPLOY,
        target_service="payment-service"
    ))
    assert not result.done
    
    # Step 3: Resolve
    result = env.step(Action(
        action_type=ActionType.RESOLVE,
        target_service="payment-service",
        parameters={"root_cause": "bad deployment v2.4.1 caused null pointer exception"}
    ))
    assert result.done
    assert result.info["correct_root_cause"] == True
    assert result.info["correct_fix"] == True
    assert result.info["final_score"] >= 0.8
    
    print(f"  Score: {result.info['final_score']}")
    print("✅ test_easy_task_optimal passed")


def test_medium_task_optimal():
    """Test optimal path for medium task."""
    env = SREIncidentEnv()
    env.reset("medium_slow_api")
    
    # Check database metrics
    env.step(Action(action_type=ActionType.CHECK_METRICS, target_service="database"))
    
    # Check database logs
    env.step(Action(action_type=ActionType.CHECK_LOGS, target_service="database"))
    
    # Run diagnostic
    env.step(Action(
        action_type=ActionType.RUN_DIAGNOSTIC,
        target_service="database",
        parameters={"command": "show_active_queries"}
    ))
    
    # Kill the query
    env.step(Action(
        action_type=ActionType.RUN_DIAGNOSTIC,
        target_service="database",
        parameters={"command": "kill_query", "pid": "12847"}
    ))
    
    # Resolve
    result = env.step(Action(
        action_type=ActionType.RESOLVE,
        target_service="database",
        parameters={"root_cause": "database connection pool exhaustion from analytics query"}
    ))
    
    assert result.done
    assert result.info["correct_root_cause"] == True
    assert result.info["correct_fix"] == True
    assert result.info["final_score"] >= 0.7
    
    print(f"  Score: {result.info['final_score']}")
    print("✅ test_medium_task_optimal passed")


def test_hard_task_optimal():
    """Test optimal path for hard task."""
    env = SREIncidentEnv()
    env.reset("hard_cascading_failure")
    
    # Check all status
    env.step(Action(action_type=ActionType.CHECK_STATUS, target_service="api-gateway"))
    
    # Check auth logs (find dependency on session service)
    env.step(Action(action_type=ActionType.CHECK_LOGS, target_service="auth-service"))
    
    # Check session service logs
    env.step(Action(action_type=ActionType.CHECK_LOGS, target_service="user-session-service"))
    
    # Check session service metrics
    env.step(Action(action_type=ActionType.CHECK_METRICS, target_service="user-session-service"))
    
    # Run diagnostic on session service
    env.step(Action(
        action_type=ActionType.RUN_DIAGNOSTIC,
        target_service="user-session-service"
    ))
    
    # Restart session service
    env.step(Action(action_type=ActionType.RESTART_SERVICE, target_service="user-session-service"))
    
    # Resolve
    result = env.step(Action(
        action_type=ActionType.RESOLVE,
        target_service="user-session-service",
        parameters={"root_cause": "memory leak in user-session-service caused OOM crash cascading failure"}
    ))
    
    assert result.done
    assert result.info["correct_root_cause"] == True
    assert result.info["correct_fix"] == True
    assert result.info["final_score"] >= 0.7
    
    print(f"  Score: {result.info['final_score']}")
    print("✅ test_hard_task_optimal passed")


def test_grader_scores_range():
    """Test that grader always produces scores between 0.0 and 1.0."""
    grader_instance = SREGrader()
    
    for task_id in get_all_task_ids():
        scenario = get_scenario(task_id)
        
        # Test worst case (no actions, not resolved)
        result = grader_instance.grade(
            task_id=task_id,
            ground_truth=scenario["ground_truth"],
            actions_taken=[],
            steps_taken=0,
            max_steps=scenario["max_steps"],
            incident_resolved=False,
            correct_root_cause=False,
            correct_fix=False,
            services_investigated=[],
        )
        assert 0.0 <= result["score"] <= 1.0, f"Score out of range: {result['score']}"
        
        # Test best case
        result = grader_instance.grade(
            task_id=task_id,
            ground_truth=scenario["ground_truth"],
            actions_taken=[{"action_type": "resolve", "target_service": "test", "step": 1, "parameters": None}],
            steps_taken=scenario["ground_truth"].optimal_steps,
            max_steps=scenario["max_steps"],
            incident_resolved=True,
            correct_root_cause=True,
            correct_fix=True,
            services_investigated=scenario["ground_truth"].relevant_services,
        )
        assert 0.0 <= result["score"] <= 1.0, f"Score out of range: {result['score']}"
        
        print(f"  ✅ Grader scores in range for {task_id} (worst: 0.0, best: {result['score']})")
    
    print("✅ test_grader_scores_range passed")


def test_episode_ends_at_max_steps():
    """Test that episode ends when max steps reached."""
    env = SREIncidentEnv()
    env.reset("easy_crashed_deploy")
    
    for i in range(20):  # More than max_steps
        result = env.step(Action(
            action_type=ActionType.CHECK_LOGS,
            target_service="payment-service"
        ))
        if result.done:
            break
    
    assert result.done == True
    assert env.state().episode_active == False
    
    print("✅ test_episode_ends_at_max_steps passed")


def test_invalid_service():
    """Test handling of invalid service name."""
    env = SREIncidentEnv()
    env.reset("easy_crashed_deploy")
    
    result = env.step(Action(
        action_type=ActionType.CHECK_LOGS,
        target_service="nonexistent-service"
    ))
    
    assert "ERROR" in result.observation.message or "does not exist" in result.observation.message
    assert result.reward.step_reward < 0
    
    print("✅ test_invalid_service passed")


def test_grader_deterministic():
    """Test that grader produces same score for same inputs."""
    grader_instance = SREGrader()
    scenario = get_scenario("easy_crashed_deploy")
    
    kwargs = dict(
        task_id="easy_crashed_deploy",
        ground_truth=scenario["ground_truth"],
        actions_taken=[{"action_type": "rollback_deploy", "target_service": "payment-service", "step": 1, "parameters": None}],
        steps_taken=3,
        max_steps=10,
        incident_resolved=True,
        correct_root_cause=True,
        correct_fix=True,
        services_investigated=["payment-service"],
    )
    
    score1 = grader_instance.grade(**kwargs)["score"]
    score2 = grader_instance.grade(**kwargs)["score"]
    score3 = grader_instance.grade(**kwargs)["score"]
    
    assert score1 == score2 == score3, f"Non-deterministic: {score1}, {score2}, {score3}"
    
    print("✅ test_grader_deterministic passed")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Running SRE Incident Response Environment Tests")
    print("="*60 + "\n")
    
    test_reset()
    test_step_returns_correct_types()
    test_state()
    test_check_logs()
    test_check_metrics()
    test_check_status()
    test_easy_task_optimal()
    test_medium_task_optimal()
    test_hard_task_optimal()
    test_grader_scores_range()
    test_episode_ends_at_max_steps()
    test_invalid_service()
    test_grader_deterministic()
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED ✅")
    print("="*60)
