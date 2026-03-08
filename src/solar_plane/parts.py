from __future__ import annotations

from typing import Dict, List

from .config import ProjectConfig


def build_parts_list(project: ProjectConfig) -> List[Dict[str, str]]:
    solar_w_peak = (
        project.mission.peak_irradiance_w_m2
        * project.solar.panel_area_m2
        * project.solar.chain_efficiency
    )

    return [
        {
            "category": "Owned",
            "item": "Brushless motor",
            "spec": f"{project.propulsion.motor_name}",
            "qty": "1",
            "est_mass_g": "120",
            "est_cost_usd": "0",
            "status": "Have",
        },
        {
            "category": "Owned",
            "item": "Propeller",
            "spec": f"Turnigy Slowfly {project.propulsion.prop_diameter_in:.0f}x{project.propulsion.prop_pitch_in:.1f} (CW)",
            "qty": "1-2",
            "est_mass_g": "22",
            "est_cost_usd": "0",
            "status": "Have",
        },
        {
            "category": "Owned",
            "item": "ESC",
            "spec": f"{project.propulsion.esc_max_current_a:.0f}A brushless ESC (with BEC preferred)",
            "qty": "1",
            "est_mass_g": "45",
            "est_cost_usd": "0",
            "status": "Have",
        },
        {
            "category": "Owned",
            "item": "Servos",
            "spec": "9g class micro servos",
            "qty": "4",
            "est_mass_g": "36",
            "est_cost_usd": "0",
            "status": "Have",
        },
        {
            "category": "Owned",
            "item": "Solar cells",
            "spec": f"Monocrystalline {project.solar.cell_size_m*1000:.0f}x{project.solar.cell_size_m*1000:.0f} mm, qty {project.solar.cell_count}",
            "qty": str(project.solar.cell_count),
            "est_mass_g": "300",
            "est_cost_usd": "0",
            "status": "Have",
        },
        {
            "category": "Owned",
            "item": "Receiver + transmitter",
            "spec": "2.4 GHz RC link",
            "qty": "1 set",
            "est_mass_g": "30",
            "est_cost_usd": "0",
            "status": "Have",
        },
        {
            "category": "Needed",
            "item": "Battery pack",
            "spec": (
                f"3S LiPo in bay <= {project.battery.max_depth_mm:.0f}x"
                f"{project.battery.max_width_mm:.0f}x{project.battery.max_height_mm:.0f} mm,"
                f" target >= {project.battery.capacity_wh:.2f} Wh"
            ),
            "qty": "1",
            "est_mass_g": "49-90",
            "est_cost_usd": "18-35",
            "status": "Buy",
        },
        {
            "category": "Needed",
            "item": "Solar MPPT charger",
            "spec": "Genasun GVB-8-Li-CV boost MPPT controller (custom 12.6V Li-ion charge profile)",
            "qty": "1",
            "est_mass_g": "35",
            "est_cost_usd": "120-180",
            "status": "Buy",
        },
        {
            "category": "Needed",
            "item": "MPPT branch fuse",
            "spec": "10A inline fuse between MPPT output and battery",
            "qty": "1",
            "est_mass_g": "8",
            "est_cost_usd": "6",
            "status": "Buy",
        },
        {
            "category": "Needed",
            "item": "Power monitor",
            "spec": "Inline watt meter/current sensor (>=60A)",
            "qty": "1",
            "est_mass_g": "25",
            "est_cost_usd": "20",
            "status": "Buy",
        },
        {
            "category": "Needed",
            "item": "Fuse + holder",
            "spec": "40A automotive blade fuse on battery line",
            "qty": "1",
            "est_mass_g": "10",
            "est_cost_usd": "8",
            "status": "Buy",
        },
        {
            "category": "Needed",
            "item": "Spar material",
            "spec": "Carbon tube/spar caps sized for 3m span",
            "qty": "1 set",
            "est_mass_g": "150",
            "est_cost_usd": "45",
            "status": "Buy",
        },
        {
            "category": "Needed",
            "item": "Airframe material",
            "spec": "Foam or balsa skin + adhesive + covering film",
            "qty": "1 set",
            "est_mass_g": "400",
            "est_cost_usd": "55",
            "status": "Buy",
        },
        {
            "category": "Needed",
            "item": "Control linkages",
            "spec": "Pushrods, horns, clevises, servo arms",
            "qty": "1 set",
            "est_mass_g": "45",
            "est_cost_usd": "18",
            "status": "Buy",
        },
        {
            "category": "Needed",
            "item": "Connectors + wire kit",
            "spec": "XT60, heatshrink, silicone wire 14/18/22 AWG",
            "qty": "1 set",
            "est_mass_g": "80",
            "est_cost_usd": "20",
            "status": "Buy",
        },
        {
            "category": "Needed",
            "item": "Spare propellers",
            "spec": f"Additional {project.propulsion.prop_diameter_in:.0f}x{project.propulsion.prop_pitch_in:.1f} slowfly props",
            "qty": "3",
            "est_mass_g": "66",
            "est_cost_usd": "15",
            "status": "Buy",
        },
        {
            "category": "Design Target",
            "item": "Peak solar electrical input",
            "spec": f"Approx {solar_w_peak:.1f} W at {project.mission.peak_irradiance_w_m2:.0f} W/m^2 sun",
            "qty": "-",
            "est_mass_g": "-",
            "est_cost_usd": "-",
            "status": "Calculated",
        },
    ]
