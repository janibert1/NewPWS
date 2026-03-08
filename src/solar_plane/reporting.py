from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List

from .config import ProjectConfig


def write_csv(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_markdown_report(
    project: ProjectConfig,
    stall_speed: float,
    best_row: Dict[str, float],
    mission_speed: float,
    propulsion: Dict[str, float],
    mission_summary: Dict[str, float],
    reserve_wh: float,
    bay_theoretical_wh: float,
    battery_rows: List[Dict[str, object]],
) -> str:
    motor_ok = "YES" if propulsion["within_motor_limit"] >= 0.5 else "NO"
    esc_ok = "YES" if propulsion["within_esc_limit"] >= 0.5 else "NO"
    strict_fit = [row for row in battery_rows if row["strict_fit"]]
    reserve_fit = [row for row in battery_rows if row["strict_fit"] and row["meets_30min_reserve"]]
    strict_fit_names = ", ".join(row["name"] for row in strict_fit) if strict_fit else "None"
    reserve_fit_names = ", ".join(row["name"] for row in reserve_fit) if reserve_fit else "None"

    return f"""# Solar Plane Sizing Report

## Inputs Used
- Mass: {project.airframe.mass_kg:.2f} kg
- Wing span: {project.airframe.wing_span_m:.2f} m
- Wing area: {project.airframe.wing_area_m2:.3f} m^2
- Aspect ratio: {project.airframe.aspect_ratio:.2f}
- Drag model: CD = CD0 + k*CL^2 with CD0={project.airframe.cd0:.3f}, e={project.airframe.oswald_efficiency:.2f}
- Solar cells: {project.solar.cell_count} cells of {project.solar.cell_size_m*1000:.0f}x{project.solar.cell_size_m*1000:.0f} mm
- Battery: {project.battery.chemistry}, {project.battery.capacity_wh:.1f} Wh

## Aerodynamics and Power
- Stall speed estimate: {stall_speed:.2f} m/s
- Best endurance cruise speed: {best_row["speed_mps"]:.2f} m/s
- Recommended mission cruise speed (stall margin): {mission_speed:.2f} m/s
- Propulsion electrical power at best endurance speed: {best_row["power_required_w"]:.2f} W
- Avionics + cellular stack power: {project.avionics.total_power_w:.2f} W
- Total electrical power at best endurance speed: {best_row["power_required_total_w"]:.2f} W
- Lift coefficient at best endurance speed: CL={best_row["cl"]:.3f}
- Drag coefficient at best endurance speed: CD={best_row["cd"]:.4f}

## Motor + Prop Compatibility (Estimated)
- Motor: {project.propulsion.motor_name}
- Prop: {project.propulsion.prop_diameter_in:.0f}x{project.propulsion.prop_pitch_in:.1f} slowfly
- Estimated loaded RPM: {propulsion["loaded_rpm"]:.0f} rpm
- Estimated current: {propulsion["estimated_current_a"]:.1f} A
- Estimated electrical power: {propulsion["estimated_electrical_power_w"]:.1f} W
- Estimated static thrust: {propulsion["estimated_static_thrust_n"]:.1f} N ({propulsion["estimated_static_thrust_kgf"]:.2f} kgf)
- Pitch speed estimate: {propulsion["pitch_speed_mps"]:.2f} m/s
- Within motor current limit: {motor_ok}
- Within ESC current limit: {esc_ok}

## Day Simulation (Winter profile)
- Simulation window: {project.mission.simulation_start_hour:.1f}h to {project.mission.simulation_end_hour:.1f}h
- Minimum state of charge: {mission_summary["min_soc_pct"]:.1f}%
- Final state of charge at end of simulation: {mission_summary["final_soc_pct"]:.1f}%
- Maximum state of charge: {mission_summary["max_soc_pct"]:.1f}%
- Battery first hits empty at hour: {"never" if mission_summary["first_empty_hour"] < 0 else f'{mission_summary["first_empty_hour"]:.2f}'}

## Battery Bay Feasibility
- Battery bay limit: {project.battery.max_depth_mm:.0f} x {project.battery.max_width_mm:.0f} x {project.battery.max_height_mm:.0f} mm
- Theoretical energy upper bound in that volume (~450 Wh/L): {bay_theoretical_wh:.2f} Wh
- 30-minute reserve target (at best-endurance electrical power, 80% usable): {reserve_wh:.2f} Wh
- Strict-fit candidate batteries from researched list: {strict_fit_names}
- Strict-fit batteries that also meet the reserve target: {reserve_fit_names}

## Notes
- Propeller current/thrust are still model estimates. Validate with a bench wattmeter before flight.
- If measured current at full throttle is above {project.propulsion.motor_max_current_a:.0f} A, reduce prop diameter/pitch or limit throttle.
- For presentation accuracy, include both this model and your measured test data.
"""
