from __future__ import annotations

from typing import Dict, List

from .config import ProjectConfig


def build_parts_list(project: ProjectConfig) -> List[Dict[str, str]]:
    solar_w_peak = (
        project.mission.peak_irradiance_w_m2
        * project.solar.panel_area_m2
        * project.solar.chain_efficiency
    )
    inv = project.inventory

    def entry(
        *,
        owned: bool,
        item: str,
        spec: str,
        qty: str,
        est_mass_g: str,
        est_cost_usd: str,
    ) -> Dict[str, str]:
        return {
            "category": "Owned" if owned else "Needed",
            "item": item,
            "spec": spec,
            "qty": qty,
            "est_mass_g": est_mass_g,
            "est_cost_usd": "0" if owned else est_cost_usd,
            "status": "Have" if owned else "Buy",
        }

    rows = [
        entry(
            owned=inv.has_motor,
            item="Brushless motor",
            spec=f"{project.propulsion.motor_name}",
            qty="1",
            est_mass_g="120",
            est_cost_usd="35",
        ),
        entry(
            owned=inv.has_propeller,
            item="Propeller",
            spec=f"Turnigy Slowfly {project.propulsion.prop_diameter_in:.0f}x{project.propulsion.prop_pitch_in:.1f} (CW)",
            qty="1-2",
            est_mass_g="22",
            est_cost_usd="6",
        ),
        entry(
            owned=inv.has_esc,
            item="ESC",
            spec=f"{project.propulsion.esc_max_current_a:.0f}A brushless ESC (with BEC preferred)",
            qty="1",
            est_mass_g="45",
            est_cost_usd="20",
        ),
        entry(
            owned=inv.has_servos,
            item="Servos",
            spec="9g class micro servos",
            qty="4",
            est_mass_g="36",
            est_cost_usd="24",
        ),
        entry(
            owned=inv.has_solar_cells,
            item="Solar cells",
            spec=f"Monocrystalline {project.solar.cell_size_m*1000:.0f}x{project.solar.cell_size_m*1000:.0f} mm, qty {project.solar.cell_count}",
            qty=str(project.solar.cell_count),
            est_mass_g="300",
            est_cost_usd="120",
        ),
        entry(
            owned=inv.has_battery_pack,
            item="Battery pack",
            spec=(
                f"3S LiPo in bay <= {project.battery.max_depth_mm:.0f}x"
                f"{project.battery.max_width_mm:.0f}x{project.battery.max_height_mm:.0f} mm,"
                f" target >= {project.battery.capacity_wh:.2f} Wh"
            ),
            qty="1",
            est_mass_g="49-90",
            est_cost_usd="18-35",
        ),
        entry(
            owned=inv.has_solar_mppt,
            item="Solar MPPT charger",
            spec="TI BQ25798EVM buck-boost MPPT charger module (3S Li-ion profile, I2C configurable)",
            qty="1",
            est_mass_g="45",
            est_cost_usd="179",
        ),
        entry(
            owned=inv.has_structural_material,
            item="Airframe + spar material",
            spec="Carbon spars/tubes and foam/balsa/skin structural set",
            qty="1 set",
            est_mass_g="550",
            est_cost_usd="100",
        ),
        entry(
            owned=inv.has_control_linkages,
            item="Control linkages",
            spec="Pushrods, horns, clevises, servo arms",
            qty="1 set",
            est_mass_g="45",
            est_cost_usd="18",
        ),
        entry(
            owned=inv.has_wire_and_connectors,
            item="Connectors + wire kit",
            spec="XT60, heatshrink, silicone wire 14/18/22 AWG",
            qty="1 set",
            est_mass_g="80",
            est_cost_usd="20",
        ),
        entry(
            owned=inv.has_elrs_transmitter,
            item="RC transmitter",
            spec="EdgeTX radio with ELRS 2.4 GHz",
            qty="1",
            est_mass_g="0",
            est_cost_usd="80-220",
        ),
        entry(
            owned=inv.has_elrs_receiver,
            item="ELRS receiver",
            spec="2.4 GHz ELRS receiver with CRSF or PWM output for fixed wing",
            qty="1",
            est_mass_g="3-10",
            est_cost_usd="18-45",
        ),
        entry(
            owned=inv.has_flight_controller,
            item="Flight controller",
            spec=project.avionics.flight_controller_name,
            qty="1",
            est_mass_g="15",
            est_cost_usd="45",
        ),
        entry(
            owned=inv.has_companion_computer,
            item="Companion computer",
            spec=project.avionics.companion_name,
            qty="1",
            est_mass_g="12",
            est_cost_usd="15",
        ),
        entry(
            owned=inv.has_lte_modem,
            item="LTE modem",
            spec=f"{project.avionics.modem_name} + SIM",
            qty="1",
            est_mass_g="20",
            est_cost_usd="25-55",
        ),
        entry(
            owned=inv.has_lte_modem,
            item="LTE antennas",
            spec="Main + diversity LTE antennas (as required by modem board)",
            qty="1 set",
            est_mass_g="8",
            est_cost_usd="8-20",
        ),
        entry(
            owned=inv.has_gps_compass,
            item="GPS + compass module",
            spec="M10-class GNSS with integrated compass for RTL/AUTO reliability",
            qty="1",
            est_mass_g="18",
            est_cost_usd="25-60",
        ),
        entry(
            owned=False,
            item="Companion power regulator",
            spec="Dedicated 5V rail for Pi and separate 3.8-4.0V high-pulse rail for LTE modem",
            qty="1 set",
            est_mass_g="30",
            est_cost_usd="18",
        ),
        entry(
            owned=False,
            item="MPPT branch fuse",
            spec="10A inline fuse between MPPT output and battery",
            qty="1",
            est_mass_g="8",
            est_cost_usd="6",
        ),
        entry(
            owned=False,
            item="Main battery fuse + holder",
            spec="40A automotive blade fuse on battery propulsion branch",
            qty="1",
            est_mass_g="10",
            est_cost_usd="8",
        ),
        entry(
            owned=False,
            item="Power monitor",
            spec="Inline watt meter/current sensor (>=60A)",
            qty="1",
            est_mass_g="25",
            est_cost_usd="20",
        ),
        entry(
            owned=False,
            item="UART/power harness parts",
            spec="Dupont/JST-SH pigtails for FC UART, crimp pins, and heatshrink strain relief",
            qty="1 set",
            est_mass_g="12",
            est_cost_usd="10",
        ),
        entry(
            owned=False,
            item="Spare propellers",
            spec=f"Additional {project.propulsion.prop_diameter_in:.0f}x{project.propulsion.prop_pitch_in:.1f} slowfly props",
            qty="3",
            est_mass_g="66",
            est_cost_usd="15",
        ),
    ]

    rows.append(
        {
            "category": "Design Target",
            "item": "Peak solar electrical input",
            "spec": f"Approx {solar_w_peak:.1f} W at {project.mission.peak_irradiance_w_m2:.0f} W/m^2 sun",
            "qty": "-",
            "est_mass_g": "-",
            "est_cost_usd": "-",
            "status": "Calculated",
        }
    )
    return rows
