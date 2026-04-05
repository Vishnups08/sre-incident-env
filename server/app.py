"""
SRE Incident Response Environment — FastAPI Application

OpenEnv-compatible API with step(), reset(), state() endpoints,
plus /tasks, /grader, and /baseline endpoints.
"""

import os
import json
import traceback
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from env.environment import SREIncidentEnv
from env.models import Action, ActionType
from graders.grader import SREGrader


# Global environment instance
env = SREIncidentEnv()
grader = SREGrader()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚨 SRE Incident Response Environment starting...")
    print(f"Available tasks: {[t.task_id for t in env.get_tasks()]}")
    yield
    print("Environment shutting down...")


app = FastAPI(
    title="SRE Incident Response Environment",
    description=(
        "An OpenEnv-compatible environment that simulates production incident "
        "response. AI agents must diagnose, investigate, and resolve system "
        "incidents like a Site Reliability Engineer."
    ),
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================
# Request/Response Models
# ========================

class ResetRequest(BaseModel):
    task_id: str = "easy_crashed_deploy"


class StepRequest(BaseModel):
    action_type: str
    target_service: str
    parameters: Optional[Dict[str, Any]] = None


class BaselineRequest(BaseModel):
    openai_api_key: Optional[str] = None


# ========================
# OpenEnv Core Endpoints
# ========================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": "SRE Incident Response",
        "version": "1.0.0",
        "endpoints": {
            "reset": "POST /reset",
            "step": "POST /step",
            "state": "GET /state",
            "tasks": "GET /tasks",
            "grader": "GET /grader",
            "baseline": "POST /baseline"
        }
    }


@app.post("/reset")
async def reset(request: ResetRequest = ResetRequest()):
    """
    Reset the environment to start a new episode.
    
    Args:
        task_id: One of 'easy_crashed_deploy', 'medium_slow_api', 'hard_cascading_failure'
    
    Returns:
        Initial observation
    """
    try:
        observation = env.reset(task_id=request.task_id)
        return {
            "observation": observation.model_dump(),
            "message": "Environment reset successfully",
            "task_id": request.task_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@app.post("/step")
async def step(request: StepRequest):
    """
    Take an action in the environment.
    
    Args:
        action_type: One of the available actions
        target_service: Service to apply action to
        parameters: Optional parameters for the action
        
    Returns:
        StepResult with observation, reward, done flag, and info
    """
    try:
        # Parse action type
        try:
            action_type = ActionType(request.action_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action_type: {request.action_type}. "
                       f"Available: {[a.value for a in ActionType]}"
            )

        action = Action(
            action_type=action_type,
            target_service=request.target_service,
            parameters=request.parameters
        )

        result = env.step(action)
        return {
            "observation": result.observation.model_dump(),
            "reward": result.reward.model_dump(),
            "done": result.done,
            "info": result.info
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step failed: {str(e)}")


@app.get("/state")
async def state():
    """Return the current environment state."""
    try:
        current_state = env.state()
        return current_state.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"State retrieval failed: {str(e)}")


# ========================
# Additional Endpoints
# ========================

@app.get("/tasks")
async def get_tasks():
    """
    Return list of available tasks and action schema.
    """
    tasks = env.get_tasks()
    return {
        "tasks": [t.model_dump() for t in tasks],
        "action_schema": {
            "action_type": {
                "type": "string",
                "enum": [a.value for a in ActionType],
                "description": "The type of action to take"
            },
            "target_service": {
                "type": "string",
                "description": "The service to apply the action to"
            },
            "parameters": {
                "type": "object",
                "description": "Optional parameters for the action",
                "nullable": True
            }
        }
    }


@app.get("/grader")
async def get_grader_score():
    """
    Return grader score after an episode is completed.
    Must be called after an episode ends (done=True).
    """
    try:
        current_state = env.state()
        
        if current_state.episode_active:
            return {
                "error": "Episode is still active. Complete the episode first.",
                "steps_taken": current_state.steps_taken,
                "max_steps": current_state.max_steps
            }

        if not current_state.task_id:
            return {
                "error": "No episode has been run. Call /reset first."
            }

        # Grade the episode
        from env.scenarios import get_scenario
        scenario = get_scenario(current_state.task_id)
        ground_truth = scenario["ground_truth"]

        result = grader.grade(
            task_id=current_state.task_id,
            ground_truth=ground_truth,
            actions_taken=current_state.actions_taken,
            steps_taken=current_state.steps_taken,
            max_steps=current_state.max_steps,
            incident_resolved=current_state.incident_resolved,
            correct_root_cause=current_state.correct_root_cause_identified,
            correct_fix=current_state.correct_fix_applied,
            services_investigated=current_state.services_investigated,
            services_restarted=[
                a["target_service"] for a in current_state.actions_taken
                if a["action_type"] in ["restart_service", "rollback_deploy"]
            ]
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grading failed: {str(e)}")


@app.post("/baseline")
async def run_baseline(request: BaselineRequest = BaselineRequest()):
    """
    Trigger baseline inference script and return scores for all 3 tasks.
    Uses OpenAI API (reads OPENAI_API_KEY from env or request).
    """
    api_key = request.openai_api_key or os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        # Run without API — use a simple heuristic agent instead
        return await _run_heuristic_baseline()
    
    try:
        from baseline.inference import run_baseline_all_tasks
        results = run_baseline_all_tasks(env, grader, api_key)
        return {
            "baseline_results": results,
            "model": "gpt-4o-mini",
            "message": "Baseline inference completed"
        }
    except Exception as e:
        # Fallback to heuristic
        return await _run_heuristic_baseline()


async def _run_heuristic_baseline():
    """Run a simple heuristic baseline agent (no LLM needed)."""
    from env.scenarios import get_all_task_ids
    
    results = {}
    
    for task_id in get_all_task_ids():
        test_env = SREIncidentEnv()
        obs = test_env.reset(task_id)
        
        # Simple heuristic: check status, check logs of first alerting service,
        # then try to resolve
        actions_sequence = _get_heuristic_actions(task_id, obs)
        
        for action_dict in actions_sequence:
            try:
                action = Action(
                    action_type=ActionType(action_dict["action_type"]),
                    target_service=action_dict["target_service"],
                    parameters=action_dict.get("parameters")
                )
                result = test_env.step(action)
                if result.done:
                    break
            except Exception:
                continue
        
        # Get final score
        state = test_env.state()
        from env.scenarios import get_scenario
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
        
        results[task_id] = {
            "score": grade_result["score"],
            "breakdown": grade_result["breakdown"],
            "feedback": grade_result["feedback"]
        }
    
    return {
        "baseline_results": results,
        "model": "heuristic-agent",
        "message": "Heuristic baseline completed (no LLM API key provided)"
    }


def _get_heuristic_actions(task_id: str, obs) -> list:
    """Get heuristic actions for baseline."""
    if task_id == "easy_crashed_deploy":
        return [
            {"action_type": "check_status", "target_service": "payment-service"},
            {"action_type": "check_logs", "target_service": "payment-service"},
            {"action_type": "check_metrics", "target_service": "payment-service"},
            {"action_type": "rollback_deploy", "target_service": "payment-service"},
            {"action_type": "resolve", "target_service": "payment-service",
             "parameters": {"root_cause": "bad deployment v2.4.1 null pointer exception"}},
        ]
    elif task_id == "medium_slow_api":
        return [
            {"action_type": "check_metrics", "target_service": "api-gateway"},
            {"action_type": "check_metrics", "target_service": "database"},
            {"action_type": "check_logs", "target_service": "database"},
            {"action_type": "run_diagnostic", "target_service": "database",
             "parameters": {"command": "show_active_queries"}},
            {"action_type": "run_diagnostic", "target_service": "database",
             "parameters": {"command": "kill_query", "pid": "12847"}},
            {"action_type": "resolve", "target_service": "database",
             "parameters": {"root_cause": "database connection pool exhaustion from analytics query"}},
        ]
    elif task_id == "hard_cascading_failure":
        return [
            {"action_type": "check_status", "target_service": "api-gateway"},
            {"action_type": "check_logs", "target_service": "auth-service"},
            {"action_type": "check_logs", "target_service": "user-session-service"},
            {"action_type": "check_metrics", "target_service": "user-session-service"},
            {"action_type": "run_diagnostic", "target_service": "user-session-service"},
            {"action_type": "restart_service", "target_service": "user-session-service"},
            {"action_type": "resolve", "target_service": "user-session-service",
             "parameters": {"root_cause": "memory leak user-session-service OOM cascading failure"}},
        ]
    return []


def main():
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("server.app:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()

