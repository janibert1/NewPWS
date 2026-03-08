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
class ProjectConfig:
    airframe: AirframeConfig = field(default_factory=AirframeConfig)
    propulsion: PropulsionConfig = field(default_factory=PropulsionConfig)
    solar: SolarConfig = field(default_factory=SolarConfig)
    battery: BatteryConfig = field(default_factory=BatteryConfig)
    mission: MissionConfig = field(default_factory=MissionConfig)

    def max_panel_cells_from_wing(self, packing_factor: float = 0.72) -> int:
        usable_area = self.airframe.wing_area_m2 * packing_factor
        cell_area = self.solar.cell_size_m * self.solar.cell_size_m
        return int(math.floor(usable_area / cell_area))
