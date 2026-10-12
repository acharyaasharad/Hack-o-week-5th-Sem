"""Constrained flexible load optimizer using SciPy linprog.
Simulates demand-side management (e.g., EV fleet charging, HVAC shifting)
under Time-Of-Use tariffs and peak-demand constraints.
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
import numpy as np
from scipy.optimize import linprog

import config

logger = logging.getLogger(__name__)


class FlexibleLoadOptimizer:
    """Solves linear programming models for flexible electricity load shifting."""

    def __init__(self):
        pass

    def solve(
        self,
        base_demand: List[float],
        required_energy: float = config.OPTIMIZATION_DEFAULTS["required_energy"],
        max_power: float = config.OPTIMIZATION_DEFAULTS["max_power"],
        start_hour: int = config.OPTIMIZATION_DEFAULTS["start_hour"],
        end_hour: int = config.OPTIMIZATION_DEFAULTS["end_hour"],
        unavailable_hours: Optional[List[int]] = None,
        tariffs: Optional[List[float]] = None,
        objective_type: str = "balanced",
        peak_penalty_weight: float = config.OPTIMIZATION_DEFAULTS["peak_penalty_weight"],
    ) -> Dict[str, Any]:
        """Solves optimal load scheduling and benchmarks baseline, cost-focused, and balanced scenarios.
        
        Args:
            base_demand: List of 24 hourly base load values (e.g. kW).
            required_energy: Total energy that must be delivered (e.g. kWh).
            max_power: Max flexible power deliverable per hour (e.g. kW).
            start_hour: Earliest allowed hour [0, 23].
            end_hour: Latest allowed hour [0, 23].
            unavailable_hours: List of forbidden hours receiving zero load.
            tariffs: List of 24 hourly tariffs ($/kWh).
            objective_type: 'cost' or 'balanced'.
            peak_penalty_weight: Trade-off parameter lambda for peak demand minimization.
        """
        # 1. Input Validations
        if not base_demand or len(base_demand) != 24:
            raise ValueError(f"Base demand must contain exactly 24 hourly values (received {len(base_demand) if base_demand else 0}).")

        if required_energy <= 0:
            raise ValueError(f"Required flexible energy must be positive (received {required_energy}).")

        if max_power <= 0:
            raise ValueError(f"Maximum hourly power must be positive (received {max_power}).")

        if not (0 <= start_hour <= 23 and 0 <= end_hour <= 23):
            raise ValueError("Start and end hours must be between 0 and 23.")

        if start_hour > end_hour:
            raise ValueError(f"Start hour ({start_hour}) cannot be greater than end hour ({end_hour}).")

        unavail_set = set(unavailable_hours or [])
        tariffs_list = list(tariffs or config.DEFAULT_TOU_TARIFF)
        if len(tariffs_list) != 24:
            raise ValueError(f"Tariff schedule must contain exactly 24 hourly rates (received {len(tariffs_list)}).")

        # 2. Feasibility Pre-Check
        # Identify eligible hours
        eligible_hours = [
            h for h in range(24)
            if start_hour <= h <= end_hour and h not in unavail_set
        ]

        max_deliverable = len(eligible_hours) * max_power
        if max_deliverable < required_energy:
            raise ValueError(
                f"Infeasible optimization: Required energy ({required_energy:.1f} kWh) exceeds "
                f"maximum deliverable energy ({max_deliverable:.1f} kWh) across the {len(eligible_hours)} eligible hours. "
                f"Please increase max power, widen the time window, or reduce required energy."
            )

        # 3. Solve Scenarios
        # Scenario A: Baseline (Earliest / Uncontrolled Greedy charging)
        baseline_sched = self._compute_baseline_schedule(
            required_energy=required_energy,
            max_power=max_power,
            eligible_hours=eligible_hours,
        )

        # Scenario B: Cost-Focused LP (lambda = 0)
        cost_sched, cost_peak_var, cost_feasible, cost_msg = self._solve_linprog(
            base_demand=base_demand,
            required_energy=required_energy,
            max_power=max_power,
            eligible_hours=eligible_hours,
            tariffs=tariffs_list,
            peak_penalty=0.0,
        )
        if not cost_feasible:
            raise RuntimeError(f"Cost optimization solver failed: {cost_msg}")

        # Scenario C: Balanced Cost & Peak Reduction LP (lambda > 0)
        balanced_sched, balanced_peak_var, bal_feasible, bal_msg = self._solve_linprog(
            base_demand=base_demand,
            required_energy=required_energy,
            max_power=max_power,
            eligible_hours=eligible_hours,
            tariffs=tariffs_list,
            peak_penalty=max(0.01, peak_penalty_weight),
        )
        if not bal_feasible:
            raise RuntimeError(f"Balanced optimization solver failed: {bal_msg}")

        # Choose selected schedule based on user objective
        if objective_type == "cost":
            chosen_sched = cost_sched
            chosen_name = "Cost-Focused Optimization"
        else:
            chosen_sched = balanced_sched
            chosen_name = "Balanced Cost & Peak Optimization"

        # 4. Scenario Metrics Compilation
        baseline_metrics = self._evaluate_scenario(base_demand, baseline_sched, tariffs_list)
        cost_metrics = self._evaluate_scenario(base_demand, cost_sched, tariffs_list)
        balanced_metrics = self._evaluate_scenario(base_demand, balanced_sched, tariffs_list)
        chosen_metrics = self._evaluate_scenario(base_demand, chosen_sched, tariffs_list)

        # Cost and peak deltas relative to baseline
        cost_savings_pct = round(
            ((baseline_metrics["flexible_cost"] - chosen_metrics["flexible_cost"]) / (baseline_metrics["flexible_cost"] if baseline_metrics["flexible_cost"] > 0 else 1.0)) * 100.0,
            2,
        )
        peak_reduction_pct = round(
            ((baseline_metrics["combined_peak"] - chosen_metrics["combined_peak"]) / (baseline_metrics["combined_peak"] if baseline_metrics["combined_peak"] > 0 else 1.0)) * 100.0,
            2,
        )

        # Hourly table for charts
        hourly_breakdown = []
        for h in range(24):
            hourly_breakdown.append({
                "hour": h,
                "hour_label": f"{h:02d}:00",
                "tariff": round(tariffs_list[h], 3),
                "base_demand": round(base_demand[h], 1),
                "baseline_flex": round(baseline_sched[h], 2),
                "baseline_combined": round(base_demand[h] + baseline_sched[h], 2),
                "cost_optimal_flex": round(cost_sched[h], 2),
                "cost_combined": round(base_demand[h] + cost_sched[h], 2),
                "balanced_flex": round(balanced_sched[h], 2),
                "balanced_combined": round(base_demand[h] + balanced_sched[h], 2),
                "is_unavailable": h in unavail_set,
                "is_within_window": start_hour <= h <= end_hour,
            })

        return {
            "success": True,
            "objective_type": objective_type,
            "selected_scenario_name": chosen_name,
            "parameters": {
                "required_energy": required_energy,
                "max_power": max_power,
                "start_hour": start_hour,
                "end_hour": end_hour,
                "unavailable_hours": sorted(list(unavail_set)),
                "peak_penalty_weight": peak_penalty_weight,
                "demand_unit": "kW",
                "energy_unit": "kWh",
                "currency_symbol": "$",
            },
            "summary": {
                "baseline_peak": baseline_metrics["combined_peak"],
                "optimized_peak": chosen_metrics["combined_peak"],
                "peak_reduction_pct": peak_reduction_pct,
                "baseline_cost": baseline_metrics["flexible_cost"],
                "optimized_cost": chosen_metrics["flexible_cost"],
                "cost_savings_pct": cost_savings_pct,
                "scheduled_energy": chosen_metrics["total_scheduled_energy"],
                "energy_conserved": abs(chosen_metrics["total_scheduled_energy"] - required_energy) < 1e-4,
            },
            "scenarios": {
                "baseline": baseline_metrics,
                "cost_focused": cost_metrics,
                "balanced": balanced_metrics,
            },
            "hourly_schedule": hourly_breakdown,
            "disclaimer": "Simulation Model: Load shifting calculations represent synthetic mathematical optimization, not certified commercial tariff guarantees.",
        }

    def _compute_baseline_schedule(
        self,
        required_energy: float,
        max_power: float,
        eligible_hours: List[int],
    ) -> List[float]:
        """Greedy immediate allocation: charges at max power as soon as available until energy is satisfied."""
        sched = [0.0] * 24
        remaining = required_energy
        for h in sorted(eligible_hours):
            if remaining <= 0:
                break
            allocated = min(remaining, max_power)
            sched[h] = allocated
            remaining -= allocated
        return sched

    def _solve_linprog(
        self,
        base_demand: List[float],
        required_energy: float,
        max_power: float,
        eligible_hours: List[int],
        tariffs: List[float],
        peak_penalty: float = 0.0,
    ) -> Tuple[List[float], float, bool, str]:
        """Sets up and solves the linear program:
        
        Variables: z = [x_0, x_1, ..., x_23, P_max]^T (dimension 25)
        Objective: Minimize sum(tariff_t * x_t) + peak_penalty * P_max
        Subject to:
          sum(x_t) = required_energy
          x_t + base_t <= P_max  ==>  x_t - P_max <= -base_t  for all t
          0 <= x_t <= max_power (if eligible) else x_t = 0
          P_max >= 0
        """
        T = 24
        n_vars = T + 1

        # 1. Objective Vector c
        c = np.zeros(n_vars)
        for t in range(T):
            c[t] = tariffs[t]
        c[T] = peak_penalty  # coefficient for P_max

        # 2. Equality Constraint: sum(x_t) = required_energy
        A_eq = np.zeros((1, n_vars))
        A_eq[0, :T] = 1.0
        A_eq[0, T] = 0.0
        b_eq = np.array([required_energy])

        # 3. Inequality Constraints: x_t - P_max <= -base_demand[t]
        A_ub = np.zeros((T, n_vars))
        b_ub = np.zeros(T)
        for t in range(T):
            A_ub[t, t] = 1.0
            A_ub[t, T] = -1.0
            b_ub[t] = -base_demand[t]

        # 4. Bounds
        bounds = []
        for t in range(T):
            if t in eligible_hours:
                bounds.append((0.0, max_power))
            else:
                bounds.append((0.0, 0.0))
        # Bounds for P_max
        bounds.append((0.0, None))

        # 5. Solve via interior-point / highs
        res = linprog(
            c=c,
            A_ub=A_ub,
            b_ub=b_ub,
            A_eq=A_eq,
            b_eq=b_eq,
            bounds=bounds,
            method="highs",
        )

        if res.success:
            x_sol = [max(0.0, round(float(res.x[t]), 3)) for t in range(T)]
            p_max_sol = float(res.x[T])
            return x_sol, p_max_sol, True, "Optimization converged successfully."
        else:
            return [0.0] * T, 0.0, False, res.message

    def _evaluate_scenario(
        self,
        base_demand: List[float],
        schedule: List[float],
        tariffs: List[float],
    ) -> Dict[str, Any]:
        """Calculates energy totals, peak demand, and costs for a given load schedule."""
        combined = [base_demand[t] + schedule[t] for t in range(24)]
        base_peak = max(base_demand)
        combined_peak = max(combined)
        
        total_energy = sum(schedule)
        flex_cost = sum(schedule[t] * tariffs[t] for t in range(24))
        base_cost = sum(base_demand[t] * tariffs[t] for t in range(24))
        total_cost = base_cost + flex_cost

        return {
            "schedule": [round(x, 2) for x in schedule],
            "combined_demand": [round(c, 2) for c in combined],
            "base_peak": round(base_peak, 2),
            "combined_peak": round(combined_peak, 2),
            "peak_delta": round(combined_peak - base_peak, 2),
            "total_scheduled_energy": round(total_energy, 2),
            "flexible_cost": round(flex_cost, 2),
            "base_cost": round(base_cost, 2),
            "total_cost": round(total_cost, 2),
        }
