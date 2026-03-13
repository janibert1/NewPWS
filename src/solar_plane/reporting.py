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


def integration_checks(
    project: ProjectConfig,
    propulsion: Dict[str, float],
    mission_summary: Dict[str, float],
    reserve_fit: List[Dict[str, object]],
) -> List[Dict[str, str]]:
    checks: List[Dict[str, str]] = []

    rc_is_elrs = "elrs" in project.avionics.rc_link_name.lower()
    checks.append(
        {
            "name": "Primary RC control link",
            "status": "PASS" if rc_is_elrs else "WARN",
            "detail": f"{project.avionics.rc_link_name}. Keep ELRS as primary C2 and LTE as telemetry/backup only.",
            "fix": "Set receiver protocol to ELRS/CRSF and verify failsafe before flight.",
        }
    )

    gps_ready = project.inventory.has_gps_compass or (not project.avionics.requires_gps_for_rtl_auto)
    checks.append(
        {
            "name": "GPS/compass for RTL/AUTO",
            "status": "PASS" if gps_ready else "WARN",
            "detail": "RTL/AUTO reliability requires GPS lock and compass heading.",
            "fix": "Add an M10 GPS+compass module and run compass/GPS calibration in ArduPilot.",
        }
    )

    lte_rail_ok = (
        project.avionics.use_dedicated_modem_regulator
        and project.avionics.modem_regulator_current_a >= project.avionics.modem_peak_current_a
        and project.avionics.modem_bulk_cap_uf >= 1000.0
        and project.avionics.modem_supply_v_min <= project.avionics.modem_supply_v_typ <= 4.2
    )
    checks.append(
        {
            "name": "LTE modem power rail",
            "status": "PASS" if lte_rail_ok else "WARN",
            "detail": (
                f"Dedicated rail {project.avionics.modem_supply_v_typ:.1f}V, regulator "
                f"{project.avionics.modem_regulator_current_a:.1f}A, bulk cap {project.avionics.modem_bulk_cap_uf:.0f}uF."
            ),
            "fix": "Use a dedicated 3.8-4.0V regulator and >=1000uF low-ESR local capacitor near modem VBAT.",
        }
    )

    pi_rail_ok = project.avionics.use_dedicated_pi_regulator and project.avionics.pi_supply_current_a >= 2.0
    checks.append(
        {
            "name": "Pi Zero 2 W power rail",
            "status": "PASS" if pi_rail_ok else "WARN",
            "detail": f"Configured dedicated {project.avionics.pi_supply_voltage_v:.1f}V rail at {project.avionics.pi_supply_current_a:.1f}A.",
            "fix": "Use a separate >=2A 5V regulator; do not power Pi and LTE modem from the same weak rail.",
        }
    )

    thrust_ratio = propulsion["estimated_static_thrust_kgf"] / project.airframe.mass_kg if project.airframe.mass_kg > 1e-9 else 0.0
    thrust_ok = thrust_ratio >= 0.70
    checks.append(
        {
            "name": "Static thrust margin",
            "status": "PASS" if thrust_ok else "WARN",
            "detail": f"Estimated static thrust-to-weight ratio: {thrust_ratio:.2f}.",
            "fix": "Reduce AUW, use a larger/more efficient prop setup, or use assisted launch if margin remains low.",
        }
    )

    day_survival_ok = mission_summary["first_empty_hour"] < 0
    empty_text = "no battery empty event in mission window" if day_survival_ok else f"battery reaches empty at {mission_summary['first_empty_hour']:.2f}h"
    checks.append(
        {
            "name": "Winter mission energy margin",
            "status": "PASS" if day_survival_ok else "WARN",
            "detail": empty_text,
            "fix": "Increase battery energy, reduce avionics load, or reduce cruise speed to maintain reserve margin.",
        }
    )

    reserve_fit_ok = len(reserve_fit) > 0
    checks.append(
        {
            "name": "Battery reserve fit in bay",
            "status": "PASS" if reserve_fit_ok else "WARN",
            "detail": "Strict-fit batteries meeting the 30-minute reserve target were found." if reserve_fit_ok else "No strict-fit battery meets the 30-minute reserve target.",
            "fix": "Enlarge battery bay, lower power draw, or relax reserve requirement with a documented risk decision.",
        }
    )

    return checks


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
    checks = integration_checks(project, propulsion, mission_summary, reserve_fit)
    check_lines = "\n".join(f"- [{row['status']}] {row['name']}: {row['detail']}" for row in checks)
    fix_lines = "\n".join(f"- {row['name']}: {row['fix']}" for row in checks if row["status"] != "PASS")
    if not fix_lines:
        fix_lines = "- No blocking issues detected in the configured checks."

    return f"""# Solar Plane Sizing Report

## Inputs Used
- Mass: {project.airframe.mass_kg:.2f} kg
- Wing span: {project.airframe.wing_span_m:.2f} m
- Wing area: {project.airframe.wing_area_m2:.3f} m^2
- Aspect ratio: {project.airframe.aspect_ratio:.2f}
- Drag model: CD = CD0 + k*CL^2 with CD0={project.airframe.cd0:.3f}, e={project.airframe.oswald_efficiency:.2f}
- Solar cells: {project.solar.cell_count} cells of {project.solar.cell_size_m*1000:.0f}x{project.solar.cell_size_m*1000:.0f} mm
- Battery: {project.battery.chemistry}, {project.battery.capacity_wh:.1f} Wh
- RC link: {project.avionics.rc_link_name}
- LTE role: {project.avionics.lte_role}

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

## Integration Checks
{check_lines}

## Recommended Fixes
{fix_lines}

## Notes
- Propeller current/thrust are still model estimates. Validate with a bench wattmeter before flight.
- If measured current at full throttle is above {project.propulsion.motor_max_current_a:.0f} A, reduce prop diameter/pitch or limit throttle.
- For presentation accuracy, include both this model and your measured test data.
"""
