# Solar Plane Sizing Report

## Inputs Used
- Mass: 1.85 kg
- Wing span: 3.00 m
- Wing area: 0.600 m^2
- Aspect ratio: 15.00
- Drag model: CD = CD0 + k*CL^2 with CD0=0.038, e=0.82
- Solar cells: 21 cells of 125x125 mm
- Battery: LiPo 3S pack, 8.3 Wh
- RC link: ELRS 2.4 GHz (CRSF)
- LTE role: Telemetry/backup only

## Aerodynamics and Power
- Stall speed estimate: 6.42 m/s
- Best endurance cruise speed: 8.25 m/s
- Recommended mission cruise speed (stall margin): 8.98 m/s
- Propulsion electrical power at best endurance speed: 17.95 W
- Avionics + cellular stack power: 6.30 W
- Total electrical power at best endurance speed: 24.25 W
- Lift coefficient at best endurance speed: CL=0.726
- Drag coefficient at best endurance speed: CD=0.0516

## Motor + Prop Compatibility (Estimated)
- Motor: D3530 1100KV
- Prop: 14x4.7 slowfly
- Estimated loaded RPM: 5417 rpm
- Estimated current: 28.0 A
- Estimated electrical power: 310.8 W
- Estimated static thrust: 12.0 N (1.22 kgf)
- Pitch speed estimate: 10.78 m/s
- Within motor current limit: YES
- Within ESC current limit: YES

## Day Simulation (Winter profile)
- Simulation window: 8.0h to 16.0h
- Minimum state of charge: 0.0%
- Final state of charge at end of simulation: 0.0%
- Maximum state of charge: 100.0%
- Battery first hits empty at hour: 8.33

## Battery Bay Feasibility
- Battery bay limit: 54 x 31 x 19 mm
- Theoretical energy upper bound in that volume (~450 Wh/L): 14.31 Wh
- 30-minute reserve target (at best-endurance electrical power, 80% usable): 15.16 Wh
- Strict-fit candidate batteries from researched list: Thunder Power Pro Lite V2 3S 500mAh 70C
- Strict-fit batteries that also meet the reserve target: None

## Integration Checks
- [PASS] Primary RC control link: ELRS 2.4 GHz (CRSF). Keep ELRS as primary C2 and LTE as telemetry/backup only.
- [WARN] GPS/compass for RTL/AUTO: RTL/AUTO reliability requires GPS lock and compass heading.
- [PASS] LTE modem power rail: Dedicated rail 4.0V, regulator 3.0A, bulk cap 1000uF.
- [PASS] Pi Zero 2 W power rail: Configured dedicated 5.1V rail at 2.0A.
- [WARN] Static thrust margin: Estimated static thrust-to-weight ratio: 0.66.
- [WARN] Winter mission energy margin: battery reaches empty at 8.33h
- [WARN] Battery reserve fit in bay: No strict-fit battery meets the 30-minute reserve target.

## Recommended Fixes
- GPS/compass for RTL/AUTO: Add an M10 GPS+compass module and run compass/GPS calibration in ArduPilot.
- Static thrust margin: Reduce AUW, use a larger/more efficient prop setup, or use assisted launch if margin remains low.
- Winter mission energy margin: Increase battery energy, reduce avionics load, or reduce cruise speed to maintain reserve margin.
- Battery reserve fit in bay: Enlarge battery bay, lower power draw, or relax reserve requirement with a documented risk decision.

## Notes
- Propeller current/thrust are still model estimates. Validate with a bench wattmeter before flight.
- If measured current at full throttle is above 35 A, reduce prop diameter/pitch or limit throttle.
- For presentation accuracy, include both this model and your measured test data.
