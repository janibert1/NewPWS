# GPS/Compass + Current & Voltage Sensing — Phase 2

Companion to `docs/rc_link_flight_controller_wiring_guide.md`. Two
independent jobs: GPS + compass for RTL/AUTO reliability, and
current/voltage sensing split into a flight-critical tier (FC's built-in
sensing) and a logging tier (the ACS712/voltage-divider modules bought
separately, activated once the Phase 3 companion computer exists).

## GPS + compass

Matek's GPS port is a single 6-pin connector combining UART + I2C + power
(typically 5V / TX / RX / SCL / SDA / GND). Cheap GPS+compass modules like
the M10G-5883 don't always use the same pin order even if the connector
shape matches.

**Check before plugging in:** trace both sides against the FC manual and
module datasheet. Wire signal-to-signal — 5V->5V, GND->GND, TX->RX, RX->TX,
SDA->SDA, SCL->SCL — and build a short adapter cable if the pin order
doesn't match rather than trusting the connector shape to be correct by
default. A wrong pin order can put 5V where GND is expected and kill the
module.

1. Wire signal-to-signal as above.
2. Mount away from power wiring — the compass is magnetically sensitive.
   Keep it clear of the ESC, motor leads, and boost converter; use a mast
   or tail mount if the wing root is too close to high-current wiring.
3. Software: set `COMPASS_EXTERNAL = 1`, run compass calibration (rotate
   the whole plane through all axes, away from metal/cars), and set
   `COMPASS_ORIENT` to match the module's physical mounting orientation
   relative to the FC's forward direction.
4. Confirm 3D GPS lock with healthy HDOP outdoors before trusting
   RTL/AUTO — this is what turns the "GPS/compass for RTL/AUTO"
   integration check from WARN to PASS.

## Current & voltage sensing — two tiers

**Tier 1 — flight-critical:** the FC's built-in BAT+/BAT- sensing (already
wired in Phase 1). Configure `BATT_MONITOR` for the Matek F405-WING's
onboard analog voltage+current sensor. This drives real failsafe actions
(`BATT_FS_LOW_ACT`, `BATT_FS_CRT_ACT`) — it's the number ArduPilot actually
acts on.

**Tier 2 — logging/backup:** the 2x ACS712 (20A) and 2x voltage-divider
modules already bought. Not flight-critical, not wired to the FC — they log
independently once the companion computer exists in Phase 3. Wire them now
and terminate the leads near the planned Pi location.

| Sensor | Placement | Why |
|---|---|---|
| ACS712 #1 | In series on the propulsion battery-to-ESC line | Redundant with the FC's built-in sensing — an independent second reading. |
| ACS712 #2 | In series on the solar charge line (boost output, after the diode/fuse) | Nothing currently monitors solar charge current — genuinely new coverage, not redundant. |
| Voltage sensor #1 | Across the main 3S battery bus | Redundant logging against the FC's built-in voltage sensing. |
| Voltage sensor #2 | Across the boost converter output (same point as TP2 in `docs/solar_array_wiring_guide.md`) | Turns the one-time multimeter check from the solar guide into a permanent monitored point — flags if the trim pot drifts. |

**Missing part:** neither the ACS712 modules nor the voltage sensors can
plug directly into the Raspberry Pi — the Pi Zero 2 W has no analog input
pins on its GPIO header. Reading these four analog signals needs a small
I2C ADC breakout (e.g. `ADS1115`, 4 channels, a couple of euros) between the
sensors and the Pi. Not currently in the parts list — add one before Phase 3.

All four sensors can be physically wired into their in-line positions now;
they won't do anything until the ADS1115 + Pi + logging script exist in
Phase 3.
