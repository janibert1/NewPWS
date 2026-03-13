from dataclasses import dataclass, field
import math


GRAVITY_MPS2 = 9.81
SEA_LEVEL_DENSITY_KG_M3 = 1.225


@dataclass
class AirframeConfig:
    # User baseline was 1.70 kg without servos/wiring/MPPT.
    # Default includes typical additions: +0.036 +0.080 +0.035 = 1.851 kg.
    mass_kg: float = 1.851
    wing_span_m: float = 3.0
    wing_area_m2: float = 0.60
    cd0: float = 0.038
    oswald_efficiency: float = 0.82
    cl_max: float = 1.20

    @property
    def weight_newton(self) -> float:
        return self.mass_kg * GRAVITY_MPS2

    @property
    def aspect_ratio(self) -> float:
        return (self.wing_span_m ** 2) / self.wing_area_m2


@dataclass
class PropulsionConfig:
    motor_name: str = "D3530 1100KV"
    motor_kv_rpm_per_volt: float = 1100.0
    motor_max_current_a: float = 35.0
    esc_max_current_a: float = 50.0
    prop_diameter_in: float = 14.0
    prop_pitch_in: float = 4.7
    battery_voltage_v: float = 11.1
    motor_efficiency: float = 0.85
    esc_efficiency: float = 0.97
    prop_efficiency: float = 0.72
    current_safety_factor: float = 0.80
    ct_static: float = 0.075
    cp_static: float = 0.050
    loaded_rpm_factor: float = 0.70

    @property
    def prop_diameter_m(self) -> float:
        return self.prop_diameter_in * 0.0254

    @property
    def prop_pitch_m(self) -> float:
        return self.prop_pitch_in * 0.0254


@dataclass
class SolarConfig:
    cell_size_m: float = 0.125
    cell_count: int = 21
    cell_efficiency: float = 0.235
    mppt_efficiency: float = 0.95
    wiring_efficiency: float = 0.97

    @property
    def panel_area_m2(self) -> float:
        return self.cell_count * self.cell_size_m * self.cell_size_m

    @property
    def chain_efficiency(self) -> float:
        return self.cell_efficiency * self.mppt_efficiency * self.wiring_efficiency


@dataclass
class BatteryConfig:
    chemistry: str = "LiPo 3S pack"
    capacity_wh: float = 8.33
    nominal_voltage_v: float = 11.1
    max_width_mm: float = 31.0
    max_height_mm: float = 19.0
    max_depth_mm: float = 54.0
    width_overrun_allowed_mm: float = 3.0
    charge_efficiency: float = 0.95
    discharge_efficiency: float = 0.97
    start_soc: float = 1.00


@dataclass
class InventoryConfig:
    # Current project inventory state.
    has_motor: bool = True
    has_propeller: bool = True
    has_esc: bool = True
    has_servos: bool = True
    has_solar_cells: bool = True
    has_battery_pack: bool = True
    has_solar_mppt: bool = True
    has_structural_material: bool = True
    has_control_linkages: bool = True
    has_wire_and_connectors: bool = True
    has_elrs_transmitter: bool = True

    # Pending purchases.
    has_elrs_receiver: bool = False
    has_flight_controller: bool = False
    has_companion_computer: bool = False
    has_lte_modem: bool = False
    has_gps_compass: bool = False


@dataclass
class MissionConfig:
    simulation_start_hour: float = 8.0
    simulation_end_hour: float = 16.0
    sunrise_hour: float = 8.0
    sunset_hour: float = 16.0
    peak_irradiance_w_m2: float = 850.0
    time_step_minutes: float = 2.0

    @property
    def daylight_hours(self) -> float:
        return max(0.0, self.sunset_hour - self.sunrise_hour)


@dataclass
class AvionicsConfig:
    flight_controller_name: str = "SpeedyBee F405 Wing APP"
    companion_name: str = "Raspberry Pi Zero 2 W"
    modem_name: str = "A7670 LTE modem"
    rc_link_name: str = "ELRS 2.4 GHz (CRSF)"
    primary_c2_link: str = "ELRS"
    lte_role: str = "Telemetry/backup only"
    protocol_fc_to_pi: str = "UART MAVLink"
    software_bridge: str = "mavlink-router"
    gcs_name: str = "QGroundControl"
    flight_controller_power_w: float = 1.0
    companion_power_w: float = 1.8
    modem_avg_power_w: float = 3.0
    modem_peak_current_a: float = 2.0
    modem_supply_v_min: float = 3.4
    modem_supply_v_typ: float = 4.0
    pi_supply_voltage_v: float = 5.1
    pi_supply_current_a: float = 2.0
    use_dedicated_pi_regulator: bool = True
    use_dedicated_modem_regulator: bool = True
    modem_regulator_current_a: float = 3.0
    modem_bulk_cap_uf: float = 1000.0
    requires_gps_for_rtl_auto: bool = True
    misc_power_w: float = 0.5

    @property
    def total_power_w(self) -> float:
        return self.flight_controller_power_w + self.companion_power_w + self.modem_avg_power_w + self.misc_power_w


@dataclass
class ProjectConfig:
    airframe: AirframeConfig = field(default_factory=AirframeConfig)
    propulsion: PropulsionConfig = field(default_factory=PropulsionConfig)
    solar: SolarConfig = field(default_factory=SolarConfig)
    battery: BatteryConfig = field(default_factory=BatteryConfig)
    inventory: InventoryConfig = field(default_factory=InventoryConfig)
    mission: MissionConfig = field(default_factory=MissionConfig)
    avionics: AvionicsConfig = field(default_factory=AvionicsConfig)

    def max_panel_cells_from_wing(self, packing_factor: float = 0.72) -> int:
        usable_area = self.airframe.wing_area_m2 * packing_factor
        cell_area = self.solar.cell_size_m * self.solar.cell_size_m
        return int(math.floor(usable_area / cell_area))
