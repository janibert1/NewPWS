from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from solar_plane import ProjectConfig, best_endurance_speed, build_parts_list
from solar_plane.battery import default_battery_options, evaluate_battery_options, reserve_energy_wh, theoretical_bay_energy_wh
from solar_plane.calculations import (
    auxiliary_electrical_power_w,
    propulsion_estimate,
    simulate_day,
    speed_sweep,
    stall_speed_mps,
    summarize_day,
    total_electrical_power_required_w,
)
from solar_plane.reporting import build_markdown_report, write_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Solar plane sizing and mission calculator.")
    parser.add_argument("--mass-kg", type=float, default=1.851, help="Total aircraft mass in kg.")
    parser.add_argument("--cell-count", type=int, default=21, help="Number of 125x125 mm solar cells.")
    parser.add_argument("--battery-wh", type=float, default=8.33, help="Battery capacity in Wh.")
    parser.add_argument("--peak-irradiance", type=float, default=850.0, help="Peak irradiance W/m^2.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "outputs", help="Output directory.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project = ProjectConfig()
    project.airframe.mass_kg = args.mass_kg
    project.solar.cell_count = args.cell_count
    project.battery.capacity_wh = args.battery_wh
    project.mission.peak_irradiance_w_m2 = args.peak_irradiance

    v_stall = stall_speed_mps(project)
    v_min = max(1.25 * v_stall, 6.0)
    v_min = math.ceil(v_min / 0.25) * 0.25
    sweep = speed_sweep(project, v_min=v_min, v_max=20.0, v_step=0.25)
    best = best_endurance_speed(project, sweep)
    mission_speed = max(best["speed_mps"], 1.4 * v_stall)
    propulsion = propulsion_estimate(project)
    sim_rows = simulate_day(project, cruise_speed_mps=mission_speed)
    mission_summary = summarize_day(sim_rows)
    parts = build_parts_list(project)
    reserve_wh = reserve_energy_wh(best["power_required_total_w"], reserve_minutes=30.0, usable_fraction=0.80)
    battery_rows = evaluate_battery_options(project, reserve_wh, default_battery_options())
    bay_theoretical_wh = theoretical_bay_energy_wh(project, volumetric_density_wh_l=450.0)

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "speed_sweep.csv", sweep)
    write_csv(out_dir / "day_simulation.csv", sim_rows)
    write_csv(out_dir / "parts_list.csv", parts)
    write_csv(out_dir / "battery_options.csv", battery_rows)

    report = build_markdown_report(
        project=project,
        stall_speed=v_stall,
        best_row=best,
        mission_speed=mission_speed,
        propulsion=propulsion,
        mission_summary=mission_summary,
        reserve_wh=reserve_wh,
        bay_theoretical_wh=bay_theoretical_wh,
        battery_rows=battery_rows,
    )
    (out_dir / "design_report.md").write_text(report, encoding="utf-8")

    print(f"Stall speed: {v_stall:.2f} m/s")
    print(f"Best endurance speed: {best['speed_mps']:.2f} m/s")
    print(f"Mission cruise speed used: {mission_speed:.2f} m/s")
    print(f"Propulsion-only power at best endurance: {best['power_required_w']:.2f} W")
    print(f"Avionics + cellular power budget: {auxiliary_electrical_power_w(project):.2f} W")
    print(f"Total electrical power at best endurance: {total_electrical_power_required_w(project, best['speed_mps']):.2f} W")
    print(f"30-min reserve target (usable): {reserve_wh:.2f} Wh")
    print(f"Theoretical battery-bay ceiling (~450 Wh/L): {bay_theoretical_wh:.2f} Wh")
    print(f"Estimated full-throttle current: {propulsion['estimated_current_a']:.1f} A")
    print(f"Report written to: {out_dir / 'design_report.md'}")


if __name__ == "__main__":
    main()
