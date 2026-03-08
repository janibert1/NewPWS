from __future__ import annotations

import math
from typing import Dict, List

from .config import ProjectConfig, SEA_LEVEL_DENSITY_KG_M3


def induced_drag_factor(project: ProjectConfig) -> float:
    ar = project.airframe.aspect_ratio
    e = project.airframe.oswald_efficiency
    return 1.0 / (math.pi * e * ar)


def stall_speed_mps(project: ProjectConfig, rho: float = SEA_LEVEL_DENSITY_KG_M3) -> float:
    w = project.airframe.weight_newton
    s = project.airframe.wing_area_m2
    cl_max = project.airframe.cl_max
    return math.sqrt((2.0 * w) / (rho * s * cl_max))


def aerodynamic_state(project: ProjectConfig, speed_mps: float, rho: float = SEA_LEVEL_DENSITY_KG_M3) -> Dict[str, float]:
    q = 0.5 * rho * speed_mps * speed_mps
    cl = project.airframe.weight_newton / (q * project.airframe.wing_area_m2)
    k = induced_drag_factor(project)
    cd = project.airframe.cd0 + k * cl * cl
    drag_n = q * project.airframe.wing_area_m2 * cd
    return {"q": q, "cl": cl, "cd": cd, "drag_n": drag_n}


def electrical_power_required_w(project: ProjectConfig, speed_mps: float) -> float:
    aero = aerodynamic_state(project, speed_mps)
    shaft_power_w = (aero["drag_n"] * speed_mps) / project.propulsion.prop_efficiency
    chain_eta = project.propulsion.motor_efficiency * project.propulsion.esc_efficiency
    return shaft_power_w / chain_eta


def speed_sweep(project: ProjectConfig, v_min: float, v_max: float, v_step: float = 0.25) -> List[Dict[str, float]]:
    rows: List[Dict[str, float]] = []
    v = v_min
    while v <= v_max + 1e-9:
        aero = aerodynamic_state(project, v)
        rows.append(
            {
                "speed_mps": v,
                "cl": aero["cl"],
                "cd": aero["cd"],
                "drag_n": aero["drag_n"],
                "power_required_w": electrical_power_required_w(project, v),
            }
        )
        v += v_step
    return rows


def best_endurance_speed(project: ProjectConfig, sweep_rows: List[Dict[str, float]]) -> Dict[str, float]:
    return min(sweep_rows, key=lambda row: row["power_required_w"])


def propulsion_estimate(project: ProjectConfig, rho: float = SEA_LEVEL_DENSITY_KG_M3) -> Dict[str, float]:
    p = project.propulsion
    voltage = p.battery_voltage_v
    no_load_rpm = p.motor_kv_rpm_per_volt * voltage

    safe_current_a = min(p.motor_max_current_a, p.esc_max_current_a) * p.current_safety_factor
    max_shaft_power_w = safe_current_a * voltage * p.motor_efficiency * p.esc_efficiency

    d = p.prop_diameter_m
    n_from_power = (max_shaft_power_w / (p.cp_static * rho * d**5)) ** (1.0 / 3.0)
    rpm_from_power = n_from_power * 60.0
    rpm_loaded = min(no_load_rpm * p.loaded_rpm_factor, rpm_from_power)

    n = rpm_loaded / 60.0
    shaft_power_w = p.cp_static * rho * n**3 * d**5
    electrical_power_w = shaft_power_w / (p.motor_efficiency * p.esc_efficiency)
    current_a = electrical_power_w / voltage
    thrust_n = p.ct_static * rho * n**2 * d**4
    pitch_speed_mps = p.prop_pitch_m * n

    return {
        "voltage_v": voltage,
        "no_load_rpm": no_load_rpm,
        "loaded_rpm": rpm_loaded,
        "safe_current_target_a": safe_current_a,
        "estimated_current_a": current_a,
        "estimated_electrical_power_w": electrical_power_w,
        "estimated_static_thrust_n": thrust_n,
        "estimated_static_thrust_kgf": thrust_n / 9.81,
        "pitch_speed_mps": pitch_speed_mps,
        "within_motor_limit": float(current_a <= p.motor_max_current_a),
        "within_esc_limit": float(current_a <= p.esc_max_current_a),
    }


def irradiance_w_m2(project: ProjectConfig, hour: float) -> float:
    m = project.mission
    if hour < m.sunrise_hour or hour > m.sunset_hour:
        return 0.0
    day_fraction = (hour - m.sunrise_hour) / (m.sunset_hour - m.sunrise_hour)
    return m.peak_irradiance_w_m2 * math.sin(math.pi * day_fraction)


def solar_input_power_w(project: ProjectConfig, hour: float) -> float:
    return irradiance_w_m2(project, hour) * project.solar.panel_area_m2 * project.solar.chain_efficiency


def simulate_day(project: ProjectConfig, cruise_speed_mps: float) -> List[Dict[str, float]]:
    dt_h = project.mission.time_step_minutes / 60.0
    battery_wh = project.battery.capacity_wh * project.battery.start_soc
    required_power_w = electrical_power_required_w(project, cruise_speed_mps)

    rows: List[Dict[str, float]] = []
    t = project.mission.simulation_start_hour
    while t <= project.mission.simulation_end_hour + 1e-9:
        p_solar = solar_input_power_w(project, t)
        p_net = p_solar - required_power_w

        if p_net >= 0:
            battery_wh += p_net * dt_h * project.battery.charge_efficiency
        else:
            battery_wh += p_net * dt_h / project.battery.discharge_efficiency

        battery_wh = max(0.0, min(project.battery.capacity_wh, battery_wh))
        soc = battery_wh / project.battery.capacity_wh if project.battery.capacity_wh > 0 else 0.0

        rows.append(
            {
                "hour": t,
                "irradiance_w_m2": irradiance_w_m2(project, t),
                "solar_input_w": p_solar,
                "required_power_w": required_power_w,
                "net_power_w": p_net,
                "battery_wh": battery_wh,
                "soc_pct": soc * 100.0,
            }
        )
        t += dt_h

    return rows


def summarize_day(sim_rows: List[Dict[str, float]]) -> Dict[str, float]:
    min_soc = min(row["soc_pct"] for row in sim_rows)
    max_soc = max(row["soc_pct"] for row in sim_rows)
    final_soc = sim_rows[-1]["soc_pct"]
    min_batt_wh = min(row["battery_wh"] for row in sim_rows)

    first_empty_hour = -1.0
    for row in sim_rows:
        if row["battery_wh"] <= 1e-9:
            first_empty_hour = row["hour"]
            break

    return {
        "min_soc_pct": min_soc,
        "max_soc_pct": max_soc,
        "final_soc_pct": final_soc,
        "min_battery_wh": min_batt_wh,
        "first_empty_hour": first_empty_hour,
    }
