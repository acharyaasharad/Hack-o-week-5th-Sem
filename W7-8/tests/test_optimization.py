"""Unit tests for FlexibleLoadOptimizer: energy conservation, power constraints, and infeasibility."""

import pytest
from services.optimization import FlexibleLoadOptimizer


@pytest.fixture
def sample_24h_base():
    # Typical 24-hour load curve (kW)
    return [
        18.0, 16.5, 15.0, 14.0, 14.5, 16.0,
        22.0, 27.5, 31.0, 33.0, 32.5, 31.0,
        30.0, 29.5, 28.0, 30.0, 34.0, 38.0,
        42.0, 44.0, 40.5, 35.0, 26.0, 20.0,
    ]


def test_energy_conservation(sample_24h_base):
    optimizer = FlexibleLoadOptimizer()
    required = 55.0
    res = optimizer.solve(
        base_demand=sample_24h_base,
        required_energy=required,
        max_power=10.0,
        start_hour=0,
        end_hour=23,
    )

    assert res["success"] is True
    assert res["summary"]["energy_conserved"] is True
    # Verify sum of allocated schedule matches required energy within tolerance
    cost_sched = res["scenarios"]["cost_focused"]["schedule"]
    assert abs(sum(cost_sched) - required) < 1e-3

    bal_sched = res["scenarios"]["balanced"]["schedule"]
    assert abs(sum(bal_sched) - required) < 1e-3


def test_power_limits_and_unavailable_hours(sample_24h_base):
    optimizer = FlexibleLoadOptimizer()
    max_p = 8.0
    unavail = [18, 19, 20]
    res = optimizer.solve(
        base_demand=sample_24h_base,
        required_energy=40.0,
        max_power=max_p,
        unavailable_hours=unavail,
    )

    for scenario_name in ["cost_focused", "balanced"]:
        sched = res["scenarios"][scenario_name]["schedule"]
        for h, val in enumerate(sched):
            assert val <= max_p + 1e-5
            if h in unavail:
                assert val == 0.0


def test_infeasible_demand_rejected(sample_24h_base):
    optimizer = FlexibleLoadOptimizer()
    # 3 eligible hours * 5.0 kW max = 15.0 kWh deliverable, but requesting 50.0 kWh
    with pytest.raises(ValueError, match="Infeasible optimization"):
        optimizer.solve(
            base_demand=sample_24h_base,
            required_energy=50.0,
            max_power=5.0,
            start_hour=1,
            end_hour=3,
        )


def test_balanced_peak_reduction(sample_24h_base):
    optimizer = FlexibleLoadOptimizer()
    res = optimizer.solve(
        base_demand=sample_24h_base,
        required_energy=45.0,
        max_power=10.0,
        objective_type="balanced",
        peak_penalty_weight=1.0,
    )

    base_peak = res["summary"]["baseline_peak"]
    opt_peak = res["summary"]["optimized_peak"]
    assert opt_peak <= base_peak
