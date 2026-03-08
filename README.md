# Solar Plane Project (Python Repo)

This repository converts your notebook work into normal Python files with a repeatable sizing workflow.

## What It Computes
- Stall speed estimate
- Best endurance cruise speed
- Electrical power required for level flight
- Motor + prop current/thrust estimate for your `D3530 1100KV` and `14x4.7` prop
- Winter-day battery state-of-charge simulation with solar input
- Improved parts list (owned vs needed)

## Project Layout
- `src/solar_plane/config.py`: all aircraft, motor, solar, battery, and mission assumptions
- `src/solar_plane/calculations.py`: aerodynamic, propulsion, and battery/solar calculations
- `src/solar_plane/parts.py`: better parts list builder
- `scripts/run_analysis.py`: one-command runner
- `legacy/`: notebook-converted scripts you already had

## Run
```powershell
python .\scripts\run_analysis.py
```

Build the detailed LaTeX PDF report (with wiring diagrams):
```powershell
python .\scripts\build_latex_report.py
```

Optional custom inputs:
```powershell
python .\scripts\run_analysis.py --mass-kg 1.85 --cell-count 26 --battery-wh 55 --peak-irradiance 900
```

## Outputs
Generated in `outputs/`:
- `design_report.md`
- `speed_sweep.csv`
- `day_simulation.csv`
- `parts_list.csv`
- `battery_options.csv`
- `solar_plane_detailed_report.tex`
- `solar_plane_detailed_report.pdf`
- `figures/power_vs_speed.png`
- `figures/solar_vs_load.png`
- `figures/soc_vs_time.png`
- `figures/duration_vs_battery.png`
- `figures/time_vs_distance_optimal.png`

## Accuracy Notes
- Aerodynamic power uses a classical drag polar: `CD = CD0 + k * CL^2`.
- Propulsion current/thrust are engineering estimates, not bench measurements.
- For best project accuracy, validate with:
  1. Static wattmeter test (`V`, `A`, `W`) at several throttle points
  2. Thrust stand measurement
  3. Glide test to calibrate `CD0`
