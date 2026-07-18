# RC Link & Flight Controller Wiring Guide — ELRS → Matek F405-WING V2 → Servos/ESC

Companion to `outputs/design_report.md` and `docs/solar_array_wiring_guide.md`.
Covers Phase 1 of the avionics build: getting to a plane that flies on
manual control, before any GPS/AUTO or telemetry features are added.

**Supersedes** the wiring diagrams in `outputs/solar_plane_detailed_report.tex`
(sections 6-9), which show receiver channels wired directly to servos/ESC.
That's pre-flight-controller RC wiring and no longer applies now that ELRS
and the Matek FC are in the signal path — see "Why this changes the wiring"
below. Those sections will be replaced once the full avionics stack is wired
and the LaTeX report is regenerated.

## Build roadmap

| Phase | Status | Scope |
|---|---|---|
| 0 — Solar array + charging | Wiring in progress | 21 cells -> boost converter -> 3S battery. See `docs/solar_array_wiring_guide.md`. |
| 1 — Manual RC flight | This guide | ELRS RX -> Matek F405-WING V2 -> servos + ESC/motor. ArduPlane flash and setup. |
| 2 — GPS/compass + current/voltage sensing | Next | M10 GPS+compass for RTL/AUTO. Open decision: FC built-in sensing vs the ACS712/voltage-divider modules bought separately. |
| 3 — Companion computer + LTE telemetry | Later | Pi Zero 2 W + A7670 modem, secondary/test feature on top of manual control. Open decision: cellular relay architecture. |

## Why this changes the wiring

A plain RC receiver sends one PWM wire per channel — aileron channel to
aileron servo, throttle channel to ESC, directly. ELRS in CRSF mode doesn't
work that way: the receiver sends all channels digitally down a single
serial connection into the flight controller. The FC decodes them and
drives its own servo outputs according to `SERVOx_FUNCTION` parameters set
in software — which physical pad does what is a software assignment, not a
wiring choice.

Practically: the receiver gets one connection to the FC. Servos and the ESC
get their own connections to the FC's own output pads — never to the
receiver directly.

## Connection map

| From | To | Wires | Note |
|---|---|---|---|
| ELRS receiver | FC UART (RX-capable) | 5V, GND, CRSF signal | Use a plain (non-inverted) UART — CRSF isn't inverted like FrSky SBUS. Check the V2 board's silkscreen/manual for which UART Matek recommends for RX. |
| Aileron servos x2 | FC servo pad | signal / + / - | Share one S-pad via a Y-lead, or use two pads with `SERVOx_FUNCTION` = Aileron / Aileron2. |
| Elevator servo | FC servo pad | signal / + / - | |
| Rudder servo | FC servo pad | signal / + / - | |
| ESC signal lead | FC servo pad | signal (+ only if using ESC's BEC) | Pick one source for the servo-rail + wire — ESC BEC or a dedicated regulator, never both. |
| Battery bus | FC BAT+/BAT- | power | Own fuse, separate from the ESC's propulsion feed. Also feeds the FC's built-in voltage/current sensing on most F405-WING revisions. |
| Battery bus | ESC power in | power | Through the 40A main fuse already in the parts list. |
| ESC 3-phase out | Motor | 3 wires, any order | Swap any two to reverse spin direction. |

**Verify before soldering:** the pad names above are the standard F405-WING
architecture, but Matek has revised the silkscreen between V1/V2/V3.
Confirm the UART assigned to RX and the servo-rail voltage jumper against
the actual board — a wrong UART choice is the most common first-build
mistake on this board family.

## Setup sequence

1. **Flash ArduPlane** — target `MatekF405-Wing`, via Mission Planner or
   QGroundControl's firmware tool over USB.
2. **Bind the ELRS receiver** to the transmitter (standard ELRS bind
   procedure, both ends into bind mode until the RX LED goes solid).
3. **Confirm the RC protocol parameter** — `SERIALx_PROTOCOL = 23` (RCIN) on
   the UART wired to the receiver. Confirm channels move in the ground
   station when the sticks move.
4. **Run radio calibration** — standard stick-endpoint wizard.
5. **Assign servo functions, prop still off.** For each S-pad actually
   wired, set `SERVOx_FUNCTION` (Aileron, Elevator, Rudder, Throttle) to
   match. Record which physical pad is used for what — it's the only
   record of the wiring once it's covered up.
6. **Check surface directions and set the throttle cap, prop still off.**
   Move each stick, confirm correct surface deflection direction, flip
   `SERVOx_REVERSED` where needed.
   - *Max-throttle-limit idea:* lower `SERVO_MAX` on the throttle output to
     cap the highest PWM ever sent to the ESC. Throttle-vs-current isn't
     linear, so the real number needs a bench wattmeter test at full stick
     first (already flagged in `outputs/design_report.md`), then set the
     cap from measured data. This connects to the Phase 2 sensor decision —
     configuring the ACS712 as ArduPilot's actual battery current monitor
     (`BATT_MONITOR`, `BATT_AMP_PERVOLT`) lets a current threshold trigger a
     real failsafe (`BATT_FS_CRT_ACT`), not just a readout.
7. **Configure RC-loss failsafe** — RTL or a safe circle/glide on loss of
   the ELRS link, not "continue on last command." Matters even for
   manual-only flights.
8. **First power-up with the propeller still removed.** Arm on the bench,
   run the throttle stick through its range, confirm the ESC responds and
   stops correctly at low throttle. Attach the propeller only after this
   checks out.

## Open decisions before Phase 2/3

- **Sensor path:** rely on the Matek F405-WING's built-in voltage/current
  sensing, or wire in the ACS712 (20A range) and voltage-divider modules
  already bought? Affects both the wiring above and whether `BATT_MONITOR`
  is configured from the FC's internal shunt or the external ACS712.
- **Cellular relay architecture:** the A7670 LTE modem needs something on
  the internet side to relay MAVLink to — typically a small always-on relay
  (e.g. a cheap VPS) that `mavlink-router` on the Pi pushes to, with
  QGroundControl connecting to that relay from the ground. Needs a decision
  on what's available before Phase 3 wiring/software is detailed.
