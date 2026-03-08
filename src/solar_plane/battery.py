from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .config import ProjectConfig


@dataclass
class BatteryOption:
    name: str
    chemistry: str
    cells: int
    capacity_mah: int
    voltage_v: float
    mass_g: float
    depth_mm: float
    width_mm: float
    height_mm: float
    source_url: str

    @property
    def energy_wh(self) -> float:
        return self.capacity_mah / 1000.0 * self.voltage_v


def default_battery_options() -> List[BatteryOption]:
    return [
        BatteryOption(
            name="Thunder Power Pro Lite V2 3S 500mAh 70C",
            chemistry="LiPo",
            cells=3,
            capacity_mah=500,
            voltage_v=11.1,
            mass_g=49,
            depth_mm=53,
            width_mm=30,
            height_mm=13,
            source_url="https://www.chiefaircraft.com/downloads/tp-lipo.pdf",
        ),
        BatteryOption(
            name="Thunder Power Pro Lite V2 3S 750mAh 70C",
            chemistry="LiPo",
            cells=3,
            capacity_mah=750,
            voltage_v=11.1,
            mass_g=69,
            depth_mm=55,
            width_mm=31,
            height_mm=18,
            source_url="https://www.chiefaircraft.com/downloads/tp-lipo.pdf",
        ),
        BatteryOption(
            name="Tattu R-Line 3S 650mAh 75C",
            chemistry="LiPo",
            cells=3,
            capacity_mah=650,
            voltage_v=11.1,
            mass_g=70,
            depth_mm=58,
            width_mm=31,
            height_mm=16,
            source_url="https://www.gensace.de/tattu-r-line-650mah-11-1v-75c-3s1p-lipo-battery-pack-with-xt30-plug.html",
        ),
        BatteryOption(
            name="Tattu R-Line 3S 850mAh 75C",
            chemistry="LiPo",
            cells=3,
            capacity_mah=850,
            voltage_v=11.1,
            mass_g=91,
            depth_mm=58,
            width_mm=30,
            height_mm=22,
            source_url="https://www.gensace.de/tattu-r-line-version-4-0-850mah-11-1v-75c-3s1p-lipo-battery-pack-with-xt30-plug.html",
        ),
    ]


def battery_bay_volume_liters(project: ProjectConfig) -> float:
    b = project.battery
    mm3 = b.max_width_mm * b.max_height_mm * b.max_depth_mm
    return mm3 * 1e-6


def theoretical_bay_energy_wh(project: ProjectConfig, volumetric_density_wh_l: float = 450.0) -> float:
    return battery_bay_volume_liters(project) * volumetric_density_wh_l


def reserve_energy_wh(power_w: float, reserve_minutes: float = 30.0, usable_fraction: float = 0.80) -> float:
    ideal_wh = power_w * reserve_minutes / 60.0
    return ideal_wh / usable_fraction


def evaluate_battery_options(project: ProjectConfig, required_wh: float, options: List[BatteryOption]) -> List[Dict[str, object]]:
    b = project.battery
    rows: List[Dict[str, object]] = []
    for option in options:
        strict_fit = (
            option.width_mm <= b.max_width_mm
            and option.height_mm <= b.max_height_mm
            and option.depth_mm <= b.max_depth_mm
        )
        width_relaxed_fit = (
            option.width_mm <= b.max_width_mm + b.width_overrun_allowed_mm
            and option.height_mm <= b.max_height_mm
            and option.depth_mm <= b.max_depth_mm
        )
        rows.append(
            {
                "name": option.name,
                "capacity_mah": option.capacity_mah,
                "energy_wh": round(option.energy_wh, 2),
                "mass_g": option.mass_g,
                "depth_mm": option.depth_mm,
                "width_mm": option.width_mm,
                "height_mm": option.height_mm,
                "strict_fit": strict_fit,
                "fit_if_width_overrun_only": width_relaxed_fit,
                "meets_30min_reserve": option.energy_wh >= required_wh,
                "source_url": option.source_url,
            }
        )
    return rows
