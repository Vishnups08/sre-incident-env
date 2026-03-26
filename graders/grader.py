"""
Grader for SRE Incident Response Environment.

Evaluates agent performance on each task, producing a deterministic
score between 0.0 and 1.0.
"""

from typing import Dict, Any, List
from env.models import GroundTruth


class SREGrader:
    """
    Grades agent performance on SRE incident response tasks.
    
    Scoring breakdown:
    - Root cause identification: 30%
    - Correct fix applied: 25%
    - Investigation quality: 20%
    - Time efficiency: 15%
    - Resolution completeness: 10%
    """

    def __init__(self):
        pass

    def grade(
        self,
        task_id: str,
        ground_truth: GroundTruth,
        actions_taken: List[Dict[str, Any]],
        steps_taken: int,
        max_steps: int,
        incident_resolved: bool,
        correct_root_cause: bool,
        correct_fix: bool,
        services_investigated: List[str],
        services_restarted: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Grade an episode.
        
        Returns:
            Dictionary with:
            - score: float (0.0 to 1.0)
            - breakdown: dict with component scores
            - feedback: str with human-readable feedback
        """
        breakdown = {}
        feedback_items = []

        # 1. Root Cause Identification (30%)
        if correct_root_cause:
            breakdown["root_cause"] = 0.30
            feedback_items.append("✅ Correctly identified root cause")
        else:
            # Partial credit: did they investigate the right service?
            relevant_investigated = len(
                set(services_investigated) & set(ground_truth.relevant_services)
            )
            if relevant_investigated > 0:
                partial = 0.10 * (relevant_investigated / len(ground_truth.relevant_services))
                breakdown["root_cause"] = round(partial, 4)
                feedback_items.append(f"⚠️ Investigated relevant services but didn't identify root cause (partial: {partial:.2f})")
            else:
                breakdown["root_cause"] = 0.0
                feedback_items.append("❌ Did not identify root cause")

        # 2. Correct Fix Applied (25%)
        if correct_fix:
            breakdown["correct_fix"] = 0.25
            feedback_items.append("✅ Applied correct fix")
        else:
            # Partial credit: did they try to fix the right service?
            fix_attempted_on_right = any(
                a["target_service"] == ground_truth.correct_fix_target and
                a["action_type"] in ["restart_service", "rollback_deploy", "update_config", "run_diagnostic"]
                for a in actions_taken
            )
            if fix_attempted_on_right:
                breakdown["correct_fix"] = 0.08
                feedback_items.append("⚠️ Attempted fix on correct service but wrong action (partial: 0.08)")
            else:
                breakdown["correct_fix"] = 0.0
                feedback_items.append("❌ Did not apply correct fix")

        # 3. Investigation Quality (20%)
        relevant_services = set(ground_truth.relevant_services)
        affected_services = set(ground_truth.affected_services)
        red_herrings = set(ground_truth.red_herring_services)
        investigated = set(services_investigated)

        relevant_found = len(investigated & relevant_services)
        relevant_total = len(relevant_services)
        red_herrings_investigated = len(investigated & red_herrings)

        investigation_score = 0.0
        if relevant_total > 0:
            investigation_score = (relevant_found / relevant_total) * 0.15
        
        # Bonus for NOT investigating red herrings
        if red_herrings_investigated == 0 and len(red_herrings) > 0:
            investigation_score += 0.05
            feedback_items.append("✅ Avoided all red herring services")
        elif red_herrings_investigated > 0:
            penalty = min(0.05, red_herrings_investigated * 0.015)
            investigation_score -= penalty
            feedback_items.append(f"⚠️ Investigated {red_herrings_investigated} red herring service(s)")

        breakdown["investigation_quality"] = round(max(0, investigation_score), 4)
        feedback_items.append(f"Investigation: found {relevant_found}/{relevant_total} relevant services")

        # 4. Time Efficiency (15%)
        if incident_resolved:
            optimal = ground_truth.optimal_steps
            if steps_taken <= optimal:
                efficiency_score = 0.15
                feedback_items.append(f"✅ Optimal or better efficiency ({steps_taken} steps, optimal: {optimal})")
            elif steps_taken <= optimal * 1.5:
                efficiency_score = 0.15 * (1 - (steps_taken - optimal) / (optimal * 1.5))
                efficiency_score = max(0.05, efficiency_score)
                feedback_items.append(f"⚠️ Reasonable efficiency ({steps_taken} steps, optimal: {optimal})")
            else:
                efficiency_score = 0.03
                feedback_items.append(f"❌ Poor efficiency ({steps_taken} steps, optimal: {optimal})")
        else:
            efficiency_score = 0.0
            feedback_items.append("❌ Incident not resolved — no efficiency score")

        breakdown["time_efficiency"] = round(efficiency_score, 4)

        # 5. Resolution Completeness (10%)
        if incident_resolved and correct_root_cause and correct_fix:
            breakdown["resolution_completeness"] = 0.10
            feedback_items.append("✅ Complete resolution: identified cause, applied fix, resolved incident")
        elif incident_resolved:
            breakdown["resolution_completeness"] = 0.04
            feedback_items.append("⚠️ Incident resolved but incomplete (missing root cause or fix)")
        else:
            breakdown["resolution_completeness"] = 0.0
            feedback_items.append("❌ Incident not resolved")

        # Penalty for unnecessary destructive actions
        penalty = 0.0
        if services_restarted:
            unnecessary = set(services_restarted) - affected_services
            if unnecessary:
                penalty = min(0.10, len(unnecessary) * 0.03)
                feedback_items.append(f"⚠️ Penalty: {len(unnecessary)} unnecessary service restart(s) (-{penalty:.2f})")

        # Calculate final score
        total_score = sum(breakdown.values()) - penalty
        total_score = round(max(0.0, min(1.0, total_score)), 4)

        breakdown["penalty_unnecessary_actions"] = -round(penalty, 4)

        feedback = "\n".join(feedback_items)

        return {
            "score": total_score,
            "breakdown": breakdown,
            "feedback": feedback,
            "task_id": task_id,
            "steps_taken": steps_taken,
            "max_steps": max_steps,
            "incident_resolved": incident_resolved,
        }
