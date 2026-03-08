from __future__ import annotations

import argparse
import copy
import math
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from solar_plane import ProjectConfig, best_endurance_speed
from solar_plane.battery import (
    default_battery_options,
    evaluate_battery_options,
    reserve_energy_wh,
    theoretical_bay_energy_wh,
)
from solar_plane.calculations import (
    auxiliary_electrical_power_w,
    electrical_power_required_w,
    propulsion_estimate,
    simulate_day,
    solar_input_power_w,
    speed_sweep,
    stall_speed_mps,
    summarize_day,
    total_electrical_power_required_w,
)


def tex_escape(text: str) -> str:
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("$", "\\$")
        .replace("#", "\\#")
        .replace("_", "\\_")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("~", "\\textasciitilde{}")
        .replace("^", "\\textasciicircum{}")
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build detailed LaTeX PDF report for the solar plane.")
    p.add_argument("--out-dir", type=Path, default=ROOT / "outputs", help="Output directory.")
    p.add_argument(
        "--tectonic",
        type=Path,
        default=ROOT / "tools" / "tectonic" / "tectonic.exe",
        help="Path to tectonic executable.",
    )
    return p.parse_args()


def compute_report_data(project: ProjectConfig) -> Dict[str, object]:
    v_stall = stall_speed_mps(project)
    v_min = max(1.25 * v_stall, 6.0)
    v_min = math.ceil(v_min / 0.25) * 0.25
    sweep = speed_sweep(project, v_min=v_min, v_max=20.0, v_step=0.25)
    best = best_endurance_speed(project, sweep)
    mission_speed = max(best["speed_mps"], 1.4 * v_stall)
    mission_power = total_electrical_power_required_w(project, mission_speed)
    propulsion_power_at_mission = electrical_power_required_w(project, mission_speed)
    avionics_power = auxiliary_electrical_power_w(project)
    propulsion = propulsion_estimate(project)
    day_rows = simulate_day(project, cruise_speed_mps=mission_speed)
    day_summary = summarize_day(day_rows)

    reserve_wh_30 = reserve_energy_wh(best["power_required_total_w"], reserve_minutes=30.0, usable_fraction=0.80)
    reserve_wh_20 = reserve_energy_wh(best["power_required_total_w"], reserve_minutes=20.0, usable_fraction=0.80)
    min_capacity_mah_30 = reserve_wh_30 / project.battery.nominal_voltage_v * 1000.0
    bay_wh_450 = theoretical_bay_energy_wh(project, volumetric_density_wh_l=450.0)
    bay_wh_550 = theoretical_bay_energy_wh(project, volumetric_density_wh_l=550.0)

    battery_options = evaluate_battery_options(project, reserve_wh_30, default_battery_options())
    strict_rows = [r for r in battery_options if r["strict_fit"]]
    relaxed_depth_58_rows = [r for r in battery_options if r["depth_mm"] <= 58 and r["height_mm"] <= project.battery.max_height_mm]

    # Cell reference from SolarInnova CSE125P-6BB: Vmp=0.55V, Voc=0.64V, Imp=8.46A.
    vmp_cell = 0.55
    voc_cell = 0.64
    imp_cell = 8.46
    n_cells = project.solar.cell_count
    panel_vmp_21s = n_cells * vmp_cell
    panel_voc_21s = n_cells * voc_cell
    panel_pmp_21s = panel_vmp_21s * imp_cell
    n_series_for_3s_buck_min = math.ceil(13.5 / vmp_cell)
    n_series_for_3s_buck_robust = math.ceil(15.0 / vmp_cell)

    mppt_options = [
        {
            "name": "Genasun GVB-8-Li-CV",
            "topology": "Boost MPPT (complete controller)",
            "charge_profile": "Custom Li-ion CV setpoint (12.6V possible)",
            "key_specs": "5-27V panel input, up to 8A output (114W at 14.2V)",
            "fit_21_cells": "Yes; 21S panel Vmp ~11.6V is within boost range",
            "source_url": "https://sunforgellc.com/gvb-8/",
        },
        {
            "name": "Genasun GV-10-Li-CV",
            "topology": "Buck MPPT (complete controller)",
            "charge_profile": "Custom Li-ion CV profile available",
            "key_specs": "10A output class; requires panel Vmp above battery charge voltage",
            "fit_21_cells": "No for robust margin with 3S Li-ion at 12.6V",
            "source_url": "https://sunforgellc.com/gv-10/",
        },
        {
            "name": "TI BQ25798EVM",
            "topology": "Buck-boost dev board (complete EVM)",
            "charge_profile": "1-4 cell battery support via configuration",
            "key_specs": "Integrated MPPT function, advanced control and integration effort",
            "fit_21_cells": "Yes technically, but high development complexity",
            "source_url": "https://www.ti.com/product/BQ25798",
        },
    ]

    return {
        "v_stall": v_stall,
        "sweep": sweep,
        "best": best,
        "mission_speed": mission_speed,
        "mission_power": mission_power,
        "mission_propulsion_power": propulsion_power_at_mission,
        "avionics_power": avionics_power,
        "propulsion": propulsion,
        "day_rows": day_rows,
        "day_summary": day_summary,
        "reserve_wh_30": reserve_wh_30,
        "reserve_wh_20": reserve_wh_20,
        "min_capacity_mah_30": min_capacity_mah_30,
        "bay_wh_450": bay_wh_450,
        "bay_wh_550": bay_wh_550,
        "battery_options": battery_options,
        "strict_rows": strict_rows,
        "relaxed_depth_58_rows": relaxed_depth_58_rows,
        "vmp_cell": vmp_cell,
        "voc_cell": voc_cell,
        "imp_cell": imp_cell,
        "panel_vmp_21s": panel_vmp_21s,
        "panel_voc_21s": panel_voc_21s,
        "panel_pmp_21s": panel_pmp_21s,
        "n_series_for_3s_buck_min": n_series_for_3s_buck_min,
        "n_series_for_3s_buck_robust": n_series_for_3s_buck_robust,
        "mppt_options": mppt_options,
    }


def achievable_flight_hours(project: ProjectConfig, mission_speed: float, battery_wh: float, with_solar: bool) -> float:
    sim_project = copy.deepcopy(project)
    sim_project.battery.capacity_wh = battery_wh
    sim_project.battery.start_soc = 1.0
    if not with_solar:
        sim_project.mission.peak_irradiance_w_m2 = 0.0

    rows = simulate_day(sim_project, cruise_speed_mps=mission_speed)
    summary = summarize_day(rows)
    if summary["first_empty_hour"] < 0:
        return sim_project.mission.simulation_end_hour - sim_project.mission.simulation_start_hour
    return max(0.0, summary["first_empty_hour"] - sim_project.mission.simulation_start_hour)


def simulate_max_duration_hours(project: ProjectConfig, speed_mps: float, start_hour: float, max_hours: float = 24.0) -> float:
    battery_cap_wh = project.battery.capacity_wh
    battery_wh = battery_cap_wh * project.battery.start_soc
    if battery_wh <= 0:
        return 0.0

    dt_h = project.mission.time_step_minutes / 60.0
    p_req = total_electrical_power_required_w(project, speed_mps)

    t = 0.0
    while t < max_hours - 1e-9:
        step = min(dt_h, max_hours - t)
        hour = (start_hour + t) % 24.0
        p_solar = solar_input_power_w(project, hour)
        p_net = p_solar - p_req

        if p_net >= 0:
            delta_wh = p_net * step * project.battery.charge_efficiency
            battery_wh = min(battery_cap_wh, battery_wh + delta_wh)
            t += step
            continue

        discharge_rate_whph = (-p_net) / project.battery.discharge_efficiency
        need_wh = discharge_rate_whph * step

        if need_wh >= battery_wh:
            t += battery_wh / discharge_rate_whph if discharge_rate_whph > 1e-9 else 0.0
            return t

        battery_wh -= need_wh
        t += step

    return max_hours


def compute_time_distance_envelope(project: ProjectConfig, sweep: List[Dict[str, float]]) -> Dict[str, object]:
    speed_candidates = sorted({row["speed_mps"] for row in sweep}, reverse=True)
    start_candidates = [h / 6.0 for h in range(0, 24 * 6)]  # every 10 minutes

    combos: List[Dict[str, float]] = []
    for v in speed_candidates:
        for start in start_candidates:
            dur_h = simulate_max_duration_hours(project, v, start, max_hours=24.0)
            dist_km = v * dur_h * 3.6
            combos.append(
                {
                    "speed_mps": v,
                    "start_hour": start,
                    "duration_h": dur_h,
                    "distance_km": dist_km,
                }
            )

    max_dist_km = max(combo["distance_km"] for combo in combos)
    max_plot_dist_km = int(min(500, math.floor(max_dist_km)))

    envelope_rows: List[Dict[str, float]] = []
    for d_km in range(1, max_plot_dist_km + 1):
        best = None
        best_time = float("inf")
        for combo in combos:
            if combo["distance_km"] + 1e-9 < d_km:
                continue
            t_h = d_km / (combo["speed_mps"] * 3.6)
            if t_h < best_time:
                best_time = t_h
                best = combo
        if best is None:
            continue
        envelope_rows.append(
            {
                "distance_km": float(d_km),
                "time_h": best_time,
                "speed_mps": best["speed_mps"],
                "start_hour": best["start_hour"],
            }
        )

    sample_distances = [10, 25, 50, 75, 100, 150, 200, 250, 300]
    sample_rows: List[Dict[str, float]] = []
    for target in sample_distances:
        candidates = [r for r in envelope_rows if abs(r["distance_km"] - target) < 0.5]
        if candidates:
            sample_rows.append(candidates[0])

    return {
        "rows": envelope_rows,
        "samples": sample_rows,
        "max_distance_km": max_dist_km,
    }


def generate_plots(project: ProjectConfig, data: Dict[str, object], out_dir: Path) -> Dict[str, str]:
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    sweep = data["sweep"]
    day_rows = data["day_rows"]
    mission_power = data["mission_power"]
    mission_speed = data["mission_speed"]
    best_speed = data["best"]["speed_mps"]

    speeds = [row["speed_mps"] for row in sweep]
    power = [row["power_required_w"] for row in sweep]

    plt.style.use("seaborn-v0_8-whitegrid")

    plt.figure(figsize=(7.2, 4.2))
    plt.plot(speeds, power, color="#004D40", linewidth=2.0, label="Electrical power required")
    plt.axvline(best_speed, color="#D81B60", linestyle="--", linewidth=1.4, label=f"Best endurance {best_speed:.2f} m/s")
    plt.xlabel("Airspeed [m/s]")
    plt.ylabel("Power [W]")
    plt.title("Power Required vs Airspeed")
    plt.legend(loc="best")
    p1 = fig_dir / "power_vs_speed.png"
    plt.tight_layout()
    plt.savefig(p1, dpi=220)
    plt.close()

    hours = [row["hour"] for row in day_rows]
    solar_in = [row["solar_input_w"] for row in day_rows]
    load = [row["required_power_w"] for row in day_rows]

    plt.figure(figsize=(7.2, 4.2))
    plt.plot(hours, solar_in, color="#F9A825", linewidth=2.0, label="Solar electrical input")
    plt.plot(hours, load, color="#283593", linewidth=2.0, label="Cruise electrical load")
    plt.xlabel("Hour of day")
    plt.ylabel("Power [W]")
    plt.title("Day Profile: Solar Input vs Flight Power")
    plt.legend(loc="best")
    p2 = fig_dir / "solar_vs_load.png"
    plt.tight_layout()
    plt.savefig(p2, dpi=220)
    plt.close()

    soc = [row["soc_pct"] for row in day_rows]
    plt.figure(figsize=(7.2, 4.2))
    plt.plot(hours, soc, color="#2E7D32", linewidth=2.2)
    plt.ylim(0, 105)
    plt.xlabel("Hour of day")
    plt.ylabel("Battery state of charge [%]")
    plt.title("Battery SOC Through Flight Window")
    p3 = fig_dir / "soc_vs_time.png"
    plt.tight_layout()
    plt.savefig(p3, dpi=220)
    plt.close()

    capacities = list(range(4, 21))
    dur_no_solar = [achievable_flight_hours(project, mission_speed, c, with_solar=False) for c in capacities]
    dur_winter = [achievable_flight_hours(project, mission_speed, c, with_solar=True) for c in capacities]

    plt.figure(figsize=(7.2, 4.2))
    plt.plot(capacities, dur_no_solar, color="#C62828", linewidth=2.0, label="No solar (worst case)")
    plt.plot(capacities, dur_winter, color="#1565C0", linewidth=2.0, label="Winter daylight profile")
    plt.axhline(
        project.mission.simulation_end_hour - project.mission.simulation_start_hour,
        color="#616161",
        linestyle="--",
        linewidth=1.2,
        label="Full flight window",
    )
    plt.xlabel("Battery capacity [Wh]")
    plt.ylabel("Achievable flight duration [h]")
    plt.title(f"Flight Duration vs Battery Capacity at {mission_power:.1f} W Load")
    plt.legend(loc="best")
    p4 = fig_dir / "duration_vs_battery.png"
    plt.tight_layout()
    plt.savefig(p4, dpi=220)
    plt.close()

    envelope_rows = data["distance_time_envelope"]["rows"]
    dist = [row["distance_km"] for row in envelope_rows]
    time_h = [row["time_h"] for row in envelope_rows]
    speed_kmh = [row["speed_mps"] * 3.6 for row in envelope_rows]

    plt.figure(figsize=(7.4, 4.4))
    ax1 = plt.gca()
    ax1.plot(dist, time_h, color="#1B5E20", linewidth=2.2, label="Minimum feasible flight time")
    ax1.set_xlabel("Distance [km]")
    ax1.set_ylabel("Time [h]", color="#1B5E20")
    ax1.tick_params(axis="y", labelcolor="#1B5E20")
    ax1.set_title("Optimal Time vs Distance (No Ground Charging)")
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(dist, speed_kmh, color="#6A1B9A", linewidth=1.6, linestyle="--", label="Optimal cruise speed")
    ax2.set_ylabel("Speed [km/h]", color="#6A1B9A")
    ax2.tick_params(axis="y", labelcolor="#6A1B9A")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    p5 = fig_dir / "time_vs_distance_optimal.png"
    plt.tight_layout()
    plt.savefig(p5, dpi=220)
    plt.close()

    return {
        "power_vs_speed": "figures/power_vs_speed.png",
        "solar_vs_load": "figures/solar_vs_load.png",
        "soc_vs_time": "figures/soc_vs_time.png",
        "duration_vs_battery": "figures/duration_vs_battery.png",
        "time_vs_distance_optimal": "figures/time_vs_distance_optimal.png",
    }


def build_report_tex(project: ProjectConfig, data: Dict[str, object], fig_paths: Dict[str, str]) -> str:
    strict_text = ", ".join(tex_escape(str(r["name"])) for r in data["strict_rows"]) if data["strict_rows"] else "None from researched list."
    relaxed_text = (
        ", ".join(tex_escape(str(r["name"])) for r in data["relaxed_depth_58_rows"])
        if data["relaxed_depth_58_rows"]
        else "None."
    )

    battery_table_lines: List[str] = []
    for row in data["battery_options"]:
        strict = "Yes" if row["strict_fit"] else "No"
        reserve = "Yes" if row["meets_30min_reserve"] else "No"
        battery_table_lines.append(
            f"{tex_escape(str(row['name']))} & "
            f"{row['capacity_mah']} & {row['energy_wh']:.2f} & {row['mass_g']:.0f} & "
            f"{row['depth_mm']:.0f}x{row['width_mm']:.0f}x{row['height_mm']:.0f} & "
            f"{strict} & {reserve} \\\\"
        )
    battery_table = "\n".join(battery_table_lines)

    mppt_lines: List[str] = []
    for row in data["mppt_options"]:
        mppt_lines.append(
            f"{tex_escape(row['name'])} & "
            f"{tex_escape(row['topology'])} & "
            f"{tex_escape(row['key_specs'])} & "
            f"{tex_escape(row['fit_21_cells'])} \\\\"
        )
    mppt_table = "\n".join(mppt_lines)

    first_empty = data["day_summary"]["first_empty_hour"]
    first_empty_text = "never" if first_empty < 0 else f"{first_empty:.2f}h"
    envelope_samples_lines: List[str] = []
    for s in data["distance_time_envelope"]["samples"]:
        envelope_samples_lines.append(
            f"\\item {s['distance_km']:.0f} km: {s['time_h']:.2f} h, "
            f"optimal speed {s['speed_mps']*3.6:.1f} km/h, optimal start {s['start_hour']:.2f}h"
        )
    envelope_samples = "\n".join(envelope_samples_lines) if envelope_samples_lines else "\\item No feasible samples in selected range."

    return rf"""
\documentclass[11pt]{{article}}
\usepackage[margin=1in]{{geometry}}
\usepackage{{booktabs}}
\usepackage{{longtable}}
\usepackage{{array}}
\usepackage{{graphicx}}
\usepackage{{siunitx}}
\usepackage{{tikz}}
\usetikzlibrary{{positioning,arrows.meta}}
\usepackage{{hyperref}}
\usepackage{{float}}
\usepackage{{xcolor}}
\title{{Solar Plane Design Report (Detailed, with MPPT + Graphs)}}
\author{{Project workspace: C:\textbackslash Users\textbackslash Janal\textbackslash NewPWS}}
\date{{\today}}

\begin{{document}}
\maketitle

\section*{{1. Project Inputs and Constraints}}
\begin{{itemize}}
  \item Airframe mass used in analysis: \SI{{{project.airframe.mass_kg:.3f}}}{{kg}} (your \SI{{1.70}}{{kg}} baseline plus servos, wiring, MPPT allowance).
  \item Wing geometry: span \SI{{{project.airframe.wing_span_m:.2f}}}{{m}}, area \SI{{{project.airframe.wing_area_m2:.3f}}}{{m^2}}, aspect ratio {project.airframe.aspect_ratio:.2f}.
  \item Solar cells: {project.solar.cell_count} cells of \SI{{125}}{{mm}} x \SI{{125}}{{mm}} mono.
  \item Battery bay hard limits: depth \SI{{{project.battery.max_depth_mm:.0f}}}{{mm}}, width \SI{{{project.battery.max_width_mm:.0f}}}{{mm}} (+\SI{{{project.battery.width_overrun_allowed_mm:.0f}}}{{mm}} tolerated), height \SI{{{project.battery.max_height_mm:.0f}}}{{mm}}.
  \item Existing propulsion hardware: D3530 1100KV, 14x4.7 slow-fly prop (CW), 50A ESC.
\end{{itemize}}
\subsection*{{Chosen control/telemetry chain (user-selected)}}
\begin{{itemize}}
  \item SpeedyBee F405
  \item UART MAVLink link to Raspberry Pi Zero 2 W
  \item mavlink-router on Pi
  \item A7670 LTE modem for WAN uplink
  \item Internet tunnel to QGroundControl
\end{{itemize}}
\begin{{itemize}}
  \item Avionics power included in calculations: FC \SI{{{project.avionics.flight_controller_power_w:.1f}}}{{W}} + Pi \SI{{{project.avionics.companion_power_w:.1f}}}{{W}} + LTE modem avg \SI{{{project.avionics.modem_avg_power_w:.1f}}}{{W}} + misc \SI{{{project.avionics.misc_power_w:.1f}}}{{W}} = \SI{{{project.avionics.total_power_w:.1f}}}{{W}}.
  \item Compatibility check: UART level is 3.3V on Pi GPIO UART and typical FC UART logic, so direct serial data interface is valid when grounds are shared.
  \item Risk 1 (power): A7670-class LTE modules have high TX current pulses; do not power the modem from Pi 5V pin. Use a dedicated regulator and local bulk capacitance.
  \item Risk 2 (control): cellular latency/coverage can drop unexpectedly; keep ELRS as primary C2 and use LTE for telemetry/backup control path.
  \item Risk 3 (firmware headroom): F405 targets can be flash-limited for advanced ArduPilot feature sets; verify your exact target build fits required features before finalizing.
\end{{itemize}}

\section*{{2. Core Performance Results}}
\begin{{itemize}}
  \item Estimated stall speed: \SI{{{data["v_stall"]:.2f}}}{{m/s}}
  \item Best-endurance speed: \SI{{{data["best"]["speed_mps"]:.2f}}}{{m/s}}
  \item Mission speed used (1.4 x stall margin): \SI{{{data["mission_speed"]:.2f}}}{{m/s}}
  \item Propulsion electrical power at best-endurance speed: \SI{{{data["best"]["power_required_w"]:.2f}}}{{W}}
  \item Total electrical power at best-endurance speed (propulsion + avionics): \SI{{{data["best"]["power_required_total_w"]:.2f}}}{{W}}
  \item Total electrical power at mission speed: \SI{{{data["mission_power"]:.2f}}}{{W}} (propulsion \SI{{{data["mission_propulsion_power"]:.2f}}}{{W}} + avionics \SI{{{data["avionics_power"]:.2f}}}{{W}})
  \item Motor estimate: loaded RPM \SI{{{data["propulsion"]["loaded_rpm"]:.0f}}}{{rpm}}, current \SI{{{data["propulsion"]["estimated_current_a"]:.1f}}}{{A}}, static thrust \SI{{{data["propulsion"]["estimated_static_thrust_n"]:.1f}}}{{N}}
\end{{itemize}}

\section*{{3. Flight Power and Duration Graphs}}
\begin{{figure}}[H]
\centering
\includegraphics[width=0.9\linewidth]{{{fig_paths["power_vs_speed"]}}}
\caption{{Propulsion electrical power required vs airspeed.}}
\end{{figure}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.9\linewidth]{{{fig_paths["solar_vs_load"]}}}
\caption{{Day profile power balance: solar input vs total cruise load (propulsion + avionics).}}
\end{{figure}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.9\linewidth]{{{fig_paths["soc_vs_time"]}}}
\caption{{Battery state of charge through the daylight mission window.}}
\end{{figure}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.9\linewidth]{{{fig_paths["duration_vs_battery"]}}}
\caption{{Flight duration versus battery capacity (with and without solar support).}}
\end{{figure}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.92\linewidth]{{{fig_paths["time_vs_distance_optimal"]}}}
\caption{{Time vs distance envelope without ground charging. For each distance, speed and departure time are optimized to minimize total flight time.}}
\end{{figure}}

\textbf{{Sample optimal points (no ground charging, battery starts at {project.battery.start_soc*100:.0f}\% SOC):}}
\begin{{itemize}}
{envelope_samples}
\end{{itemize}}

\section*{{4. Battery Feasibility for Your Battery Bay}}
\begin{{itemize}}
  \item 30-minute reserve target: \SI{{{data["reserve_wh_30"]:.2f}}}{{Wh}} (minimum \SI{{{data["min_capacity_mah_30"]:.0f}}}{{mAh}} at 3S nominal).
  \item 20-minute reserve target: \SI{{{data["reserve_wh_20"]:.2f}}}{{Wh}}.
  \item Theoretical max energy in bay (450--550 Wh/L): \SI{{{data["bay_wh_450"]:.2f}}}{{Wh}} to \SI{{{data["bay_wh_550"]:.2f}}}{{Wh}}.
  \item Daylight simulation minimum SOC: {data["day_summary"]["min_soc_pct"]:.1f}\%, final SOC: {data["day_summary"]["final_soc_pct"]:.1f}\%, first empty time: {first_empty_text}.
\end{{itemize}}

\subsection*{{Researched battery options}}
\begin{{longtable}}{{p{{5.8cm}} r r r c c c}}
\toprule
Pack & mAh & Wh & g & D x W x H (mm) & Strict fit & Meets 30-min reserve \\
\midrule
\endhead
{battery_table}
\bottomrule
\end{{longtable}}

\textbf{{Strict-fit options found:}} {strict_text}

\textbf{{If depth can extend to about 58 mm:}} {relaxed_text}

\section*{{5. Proper MPPT Controller Selection (Module-level, not chip-only)}}
Using your 21-cell panel as one series string:
\[
V_{{MP,array}} \approx 21 \cdot {data["vmp_cell"]:.2f} = {data["panel_vmp_21s"]:.2f}\ \mathrm{{V}},\quad
V_{{OC,array}} \approx 21 \cdot {data["voc_cell"]:.2f} = {data["panel_voc_21s"]:.2f}\ \mathrm{{V}}
\]
This panel voltage is below robust buck-MPPT headroom for charging a 3S Li-ion pack at \SI{{12.6}}{{V}}.
For buck topologies, practical cell count is about {data["n_series_for_3s_buck_min"]} (minimum) to {data["n_series_for_3s_buck_robust"]} (recommended margin).
Therefore, with 21 cells, a \textbf{{boost or buck-boost MPPT}} is the correct architecture.

\subsection*{{MPPT module options}}
\begin{{longtable}}{{p{{3.6cm}} p{{3.4cm}} p{{5.1cm}} p{{3.0cm}}}}
\toprule
Model & Topology & Key specs & Fits current 21-cell panel? \\
\midrule
\endhead
{mppt_table}
\bottomrule
\end{{longtable}}

\textbf{{Recommended for your build:}} Genasun GVB-8-Li-CV with custom 3S Li-ion charge profile (\SI{{12.6}}{{V}} CV), because it is a complete boost MPPT controller and matches low panel voltage operation.

\subsection*{{Required supporting components around MPPT}}
\begin{{itemize}}
  \item PV fuse near panel positive lead, sized around 1.25x panel Isc branch current.
  \item Dedicated MPPT-to-battery branch fuse (about 10A for an 8A-class controller).
  \item Main battery fuse for propulsion branch (about 40A with your ESC/motor class).
  \item XT60 (or equivalent) connectors and 16--14 AWG wire on high-current paths.
\end{{itemize}}

\section*{{6. Wiring Diagram A: Power Architecture}}
\begin{{figure}}[H]
\centering
\resizebox{{0.98\linewidth}}{{!}}{{%
\begin{{tikzpicture}}[
    node distance=1.3cm and 1.1cm,
    block/.style={{draw, rounded corners, align=center, minimum width=2.1cm, minimum height=0.8cm, fill=blue!5}},
    io/.style={{draw, rounded corners, align=center, minimum width=2.1cm, minimum height=0.8cm, fill=green!6}},
    safety/.style={{draw, rounded corners, align=center, minimum width=1.8cm, minimum height=0.8cm, fill=red!6}},
    line/.style={{-{{Latex[length=2mm]}}, thick}}
]
\node[io] (solar) {{Solar Array\\(21 cells)}};
\node[safety, right=of solar] (sfuse) {{PV Fuse\\2--3A}};
\node[block, right=of sfuse] (mppt) {{GVB-8-Li-CV\\Boost MPPT}};
\node[safety, right=of mppt] (mfuse) {{MPPT Fuse\\10A}};
\node[safety, right=of mfuse] (bfuse) {{Main Fuse\\40A}};
\node[io, right=of bfuse] (battery) {{3S Battery\\Bay-limited}};

\node[block, below=1.3cm of battery] (esc) {{50A ESC\\+ BEC}};
\node[io, left=of esc] (motor) {{D3530 +\\14x4.7}};
\node[block, below=1.3cm of esc] (rx) {{Receiver}};
\node[io, left=of rx] (servos) {{Servos x4}};

\draw[line] (solar) -- (sfuse);
\draw[line] (sfuse) -- (mppt);
\draw[line] (mppt) -- (mfuse);
\draw[line] (mfuse) -- (bfuse);
\draw[line] (bfuse) -- (battery);
\draw[line] (battery) -- (esc);
\draw[line] (esc) -- (motor);
\draw[line] (esc) -- node[right] {{BEC 5V}} (rx);
\draw[line] (rx) -- (servos);
\end{{tikzpicture}}
}}
\caption{{Recommended power wiring with dedicated MPPT branch protection.}}
\end{{figure}}

\section*{{7. Wiring Diagram B: Signal and Channel Mapping}}
\begin{{figure}}[H]
\centering
\resizebox{{0.92\linewidth}}{{!}}{{%
\begin{{tikzpicture}}[
    node distance=1.4cm and 1.7cm,
    block/.style={{draw, rounded corners, align=center, minimum width=3.0cm, minimum height=1.0cm, fill=blue!5}},
    io/.style={{draw, rounded corners, align=center, minimum width=3.2cm, minimum height=1.0cm, fill=green!6}},
    line/.style={{-{{Latex[length=2.2mm]}}, thick}}
]
\node[block] (tx) {{Transmitter}};
\node[block, right=of tx] (rx) {{Receiver (CH1..CH6)}};
\node[io, right=of rx, yshift=1.2cm] (ail) {{CH1: Aileron Servo(s)}};
\node[io, right=of rx, yshift=0.0cm] (elev) {{CH2: Elevator Servo}};
\node[io, right=of rx, yshift=-1.2cm] (thr) {{CH3: ESC Signal}};
\node[io, right=of rx, yshift=-2.4cm] (aux) {{CH4/CH5: Rudder or Aux}};

\draw[line] (tx) -- node[above] {{2.4 GHz link}} (rx);
\draw[line] (rx) -- (ail);
\draw[line] (rx) -- (elev);
\draw[line] (rx) -- (thr);
\draw[line] (rx) -- (aux);
\end{{tikzpicture}}
}}
\caption{{Signal wiring map. Verify channel assignments in transmitter before motor power-up.}}
\end{{figure}}

\section*{{8. Pin-level Wiring (Exact Connector Mapping)}}
\subsection*{{8.1 Shared power-bus rule}}
Battery+, MPPT output+, and ESC+ are intentionally on the same positive DC bus node (through their branch fuses). Continuity between those + points is expected. A fault is only + to - continuity.

\subsection*{{8.2 Receiver and ESC 3-wire lead pin mapping}}
{{\small
\begin{{longtable}}{{>{{\raggedright\arraybackslash}}p{{3.2cm}} >{{\raggedright\arraybackslash}}p{{2.0cm}} >{{\raggedright\arraybackslash}}p{{3.5cm}} >{{\raggedright\arraybackslash}}p{{3.5cm}}}}
\toprule
Wire color (typical) & Pin function & Connect to receiver pin row & Notes \\
\midrule
\endhead
White/Yellow/Orange & Signal (S) & CH3 signal pin & ESC throttle command line \\
Red & +5V BEC output & CH3 + pin (receiver power rail) & Powers receiver and servos if ESC has BEC \\
Black/Brown & Ground (GND) & CH3 - pin & Must share common ground with all RC signal devices \\
\bottomrule
\end{{longtable}}
}}

\subsection*{{8.3 Servo connector mapping}}
{{\small
\begin{{longtable}}{{>{{\raggedright\arraybackslash}}p{{2.4cm}} >{{\raggedright\arraybackslash}}p{{2.6cm}} >{{\raggedright\arraybackslash}}p{{3.8cm}} >{{\raggedright\arraybackslash}}p{{3.8cm}}}}
\toprule
Receiver channel & Control surface & Pin order on receiver & Typical wire colors \\
\midrule
\endhead
CH1 & Aileron & S / + / - & Orange or white / red / brown-black \\
CH2 & Elevator & S / + / - & Orange or white / red / brown-black \\
CH4 (optional) & Rudder & S / + / - & Orange or white / red / brown-black \\
CH5/CH6 (optional) & Aux, flaps, telemetry trigger & S / + / - & Orange or white / red / brown-black \\
\bottomrule
\end{{longtable}}
}}

\subsection*{{8.4 MPPT and high-current wiring map}}
{{\small
\begin{{longtable}}{{>{{\raggedright\arraybackslash}}p{{3.8cm}} >{{\raggedright\arraybackslash}}p{{3.2cm}} >{{\raggedright\arraybackslash}}p{{4.0cm}}}}
\toprule
Connection & Wire/fuse recommendation & Purpose \\
\midrule
\endhead
Solar+ to MPPT IN+ & PV fuse 2-3A near panel & Protect panel branch from short faults \\
MPPT OUT+ to battery bus+ & 10A fuse near battery bus & Protect charger branch and wiring \\
Battery bus+ to ESC+ & 40A main fuse near battery & Protect propulsion high-current branch \\
All negatives (solar/MPPT/battery/ESC) & Common ground return bus & Required for charger and RC signal reference \\
\bottomrule
\end{{longtable}}
}}

\subsection*{{8.5 Pre-power checklist}}
\begin{{enumerate}}
  \item Remove propeller before bench wiring and ESC setup.
  \item Confirm no hard short between main bus + and - (ohmmeter should not read near-zero steady value).
  \item Confirm expected continuity between battery+, MPPT+, and ESC+ bus points.
  \item Power receiver/ESC first from battery only, verify channel directions.
  \item Connect solar and MPPT last, then confirm charging current with a wattmeter.
\end{{enumerate}}

\section*{{9. Wiring Diagram C: Pin-level Connector Orientation}}
\begin{{figure}}[H]
\centering
\resizebox{{0.96\linewidth}}{{!}}{{%
\begin{{tikzpicture}}[
    node distance=1.1cm and 1.2cm,
    box/.style={{draw, rounded corners, align=center, minimum width=2.8cm, minimum height=0.9cm, fill=blue!5}},
    pin/.style={{draw, align=center, minimum width=1.4cm, minimum height=0.6cm}},
    line/.style={{-{{Latex[length=2mm]}}, thick}}
]
\node[box] (rx) {{Receiver CH3 port}};
\node[pin, right=2.3cm of rx, fill=yellow!18] (sig) {{S}};
\node[pin, below=0.05cm of sig, fill=red!12] (vcc) {{+5V}};
\node[pin, below=0.05cm of vcc, fill=gray!18] (gnd) {{GND}};

\node[box, left=2.3cm of rx] (esclead) {{ESC 3-wire lead}};
\node[pin, left=2.0cm of sig, fill=yellow!18] (escsig) {{White/Yellow}};
\node[pin, left=2.0cm of vcc, fill=red!12] (escvcc) {{Red}};
\node[pin, left=2.0cm of gnd, fill=gray!18] (escgnd) {{Black/Brown}};

\draw[line] (esclead) -- (rx);
\draw[line] (escsig) -- (sig);
\draw[line] (escvcc) -- (vcc);
\draw[line] (escgnd) -- (gnd);
\end{{tikzpicture}}
}}
\caption{{ESC lead to receiver CH3 mapping. Keep signal, +5V and GND aligned in the same row orientation.}}
\end{{figure}}

\section*{{10. LW-PLA and Carbon Tube Build Notes}}
\begin{{itemize}}
  \item LW-PLA should be printed hot enough for foaming expansion; tune flow down after expansion to reduce mass.
  \item Carbon tubes should carry main bending loads in wing spar caps or spar tube; printed parts should primarily transfer loads into tubes.
  \item Reinforce wing root and motor mount interfaces with local carbon doublers or thicker load-spreading printed inserts.
\end{{itemize}}

\section*{{11. Sources}}
\begin{{enumerate}}
  \item Solar cell electrical reference (CSE125P-6BB): \url{{https://solarinnova.net/en/product/cell-cse125p-6bb/}}
  \item Genasun GVB-8 boost MPPT controller page: \url{{https://sunforgellc.com/gvb-8/}}
  \item Genasun GVB-8 datasheet/user manual: \url{{https://sunforgellc.com/wp-content/uploads/2017/11/GENASUN-GVB-Boost-Manual.pdf}}
  \item Genasun GV-10 MPPT controller page: \url{{https://sunforgellc.com/gv-10/}}
  \item TI BQ25798 product page (buck-boost charger with MPPT support): \url{{https://www.ti.com/product/BQ25798}}
  \item TI BQ24650 datasheet: \url{{https://www.ti.com/lit/gpn/bq24650}}
  \item TI BQ24650 EVM user guide: \url{{https://www.ti.com/lit/ug/sluu444a/sluu444a.pdf}}
  \item SpeedyBee F405 product/target reference: \url{{https://www.speedybee.com/speedybee-f405-wing-app-fixed-wing-flight-controller/}}
  \item ArduPilot note on F4 flash constraints: \url{{https://ardupilot.org/copter/docs/common-limited-firmware.html}}
  \item SIMCom A7670 hardware design guide (power supply and burst current guidance): \url{{https://simcom.ee/documents/A76XX/A76XX%20Series_Hardware%20Design_V1.07.pdf}}
  \item MAVLink Router project/documentation: \url{{https://github.com/mavlink-router/mavlink-router}}
  \item QGroundControl project: \url{{https://qgroundcontrol.com/}}
  \item Thunder Power LiPo dimensions/spec chart: \url{{https://www.chiefaircraft.com/downloads/tp-lipo.pdf}}
  \item Tattu 650mAh 3S product page (dimensions): \url{{https://www.gensace.de/tattu-r-line-650mah-11-1v-75c-3s1p-lipo-battery-pack-with-xt30-plug.html}}
  \item Tattu 850mAh 3S product page (dimensions): \url{{https://www.gensace.de/tattu-r-line-version-4-0-850mah-11-1v-75c-3s1p-lipo-battery-pack-with-xt30-plug.html}}
  \item colorFabb LW-PLA product and print guidance: \url{{https://colorfabb.com/lw-pla-natural?srsltid=AfmBOopoCdZegtz2AIdR2wfQZQ5N8a1ba9hLJxQFUnUGR92Ve8g7Qy2D}}
  \item eSUN LW-PLA material data: \url{{https://www.esun3d.com/epla-lw-product/}}
  \item Easy Composites carbon tube data sheet: \url{{https://www.easycomposites.co.uk/pub/media/pdf/carbon-fibre-tube-data-sheet.pdf}}
\end{{enumerate}}

\end{{document}}
"""


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    project = ProjectConfig()
    data = compute_report_data(project)
    data["distance_time_envelope"] = compute_time_distance_envelope(project, data["sweep"])
    fig_paths = generate_plots(project, data, out_dir)
    tex = build_report_tex(project, data, fig_paths)

    tex_path = out_dir / "solar_plane_detailed_report.tex"
    pdf_path = out_dir / "solar_plane_detailed_report.pdf"
    tex_path.write_text(tex, encoding="utf-8")

    if args.tectonic.exists():
        cmd = [str(args.tectonic), "--outdir", str(out_dir), str(tex_path)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            print(proc.stdout)
            print(proc.stderr)
            raise SystemExit(f"Tectonic failed with code {proc.returncode}")
        if pdf_path.exists():
            print(f"PDF written: {pdf_path}")
    else:
        print(f"Tectonic not found at: {args.tectonic}")
        print(f"LaTeX source written: {tex_path}")


if __name__ == "__main__":
    main()
