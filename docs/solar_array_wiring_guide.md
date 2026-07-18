# Solar Array Wiring Guide — 21-Cell Array → Boost Converter → 3S Battery

Companion to `outputs/design_report.md`. Covers the physical build the design
report's power-architecture section doesn't: how to wire the 21 monocrystalline
cells that actually fit the 0.60 m² wing, and how to charge the 3S pack from
them using a boost converter instead of the BQ24650 buck modules originally
on hand.

## Why a boost converter, not the BQ24650 buck modules

A 21-cell series string of 125 mm mono cells (~0.50 V Vmp, ~0.60 V Voc each)
only reaches:

- Vmp (loaded): ~10.5 V
- Voc (open circuit): ~12.6 V
- Imp: ~6.0 A
- Nameplate power: 21 × 3.07 W ≈ 64.5 W (consistent with the ~60 W peak
  figure already in `outputs/design_report.md`)

The 3S battery needs to charge up to 12.6 V (4.20 V/cell). The BQ24650
modules are buck-only — they need input voltage clearly above the output,
with margin. This string's loaded voltage is already below that target, and
it only gets worse as the cells heat up in the sun. There isn't wing space
for more series cells, so a buck-only path can't reliably work here.

**Fix:** run the 150 W boost converter as the sole conversion stage
(panel → boost → blocking diode → fuse → battery), trimmed as a simple
fixed CV/CC charger. It won't be true MPPT, but for a plane that only flies
in direct summer sun, a well-tuned fixed operating point captures most of
the available power. Do not put the boost converter *before* the BQ24650 —
that would make the buck stage regulate against the boost's output instead
of the panel's actual IV curve, defeating what MPP-tracking it has. Keep
the BQ24650 modules as spares or for a separate lower-voltage sub-system.

## Circuit

```
Solar array (21 cells in series)
  Vmp ~10.5 V · Voc ~12.6 V · Imp ~6.0 A
        |
        v
150 W boost converter
  IN 9-13 V -> OUT trimmed to 12.5 V (measured at battery side, diode installed)
        |
        v
Blocking diode (Schottky)
  stops battery backfeeding through the panel at night/low light
        |
        v
5 A fuse (inline, boost output side)
        |
        v
3S LiPo battery
  11.1 V nominal · 12.6 V max charge
  watch balance-lead voltage during first charges
```

Test points: TP1 at the array output (check Voc/Vmp before connecting
anything); TP2 after the diode, where the boost converter is trimmed with
the diode already in circuit.

## Build sequence

1. **Test polarity on every cell.** One at a time, in direct sun: multimeter
   on DC volts, probes on front grid and back pad. Positive reading tells
   you which contact is + on that cell. Mark with tape — imported cells
   aren't always labeled consistently.
2. **Dry-fit the layout on the wing** before soldering. Leave 2-3 mm gaps
   between cells for flex and tabbing wire.
3. **Tab the cells in series** — back pad of cell N to front bus bar of cell
   N+1, through cell 21. Low-wattage iron, flux, under ~2 seconds contact
   per joint — cells crack from heat. 19 spares are on hand from the order
   of 40.
4. **Sanity-check the full string at TP1.** Expect roughly 11-13 V Voc in
   sunlight. Well outside that range means a bad joint or reversed polarity
   somewhere in the chain.
5. **Connect the string to the boost converter input.** Mind polarity.
   Do not connect the output to the battery yet.
6. **Bench-test the boost converter alone** — multimeter on the output only,
   no battery, no load. Dial the trim pot to the lowest stable output first,
   then bring it up gradually.
7. **Add the blocking diode and 5 A fuse** inline between the boost output
   and where the battery lead will connect.
8. **Trim to 12.5 V at TP2** — after the diode, not at the boost module's
   own terminals (the diode's forward drop means the module's internal
   output will read a bit higher than 12.5 V; that's expected).
9. **First connection to the real battery** only once step 8 is confirmed
   stable. Watch balance-lead cell voltages during the first charge cycle
   rather than trusting the pot setting blindly.
10. **Secure and strain-relieve.** Re-check TP2 after the plane has been
    transported or handled — vibration can walk a cheap trim pot.

## Safety

- **No BMS on this path.** The boost module has no overcharge cutoff, no
  balancing, no thermal protection — it only does what the pot is set to.
  Never leave it charging unattended, especially on the first few cycles.
- Consider adding a cheap (~€2) 3S low/high-voltage buzzer module on the
  balance lead for an audible warning if the pack drifts outside a safe
  range — not currently in the parts list, worth adding.
- Charge and store in a fire-resistant LiPo bag.

## Reference numbers

| Quantity | Value | Note |
|---|---|---|
| Cells in series | 21 | 19 spare from the 40 bought |
| String Vmp (loaded) | ~10.5 V | 0.50 V/cell typical |
| String Voc (open circuit) | ~12.6 V | 0.60 V/cell typical |
| String Imp | ~6.0 A | same through whole series string |
| Nameplate array power | ~64.5 W | 21 x 3.07 W rated/cell |
| Boost target (battery side) | 12.5 V | below 3S 12.6 V max, safety margin |
| Expected charge current | ~4.5 A | after ~90% boost efficiency |
| Fuse | 5 A | `outputs/parts_list.csv` currently lists 10 A — oversized for this circuit |
| Battery | 3S / 11.1 V nom | 12.6 V max charge = 4.20 V/cell |

Numbers are based on typical 125 mm mono cell specs (~3.07 W/pc), not a
measured sample. Confirm string Voc/Vmp with a multimeter at step 4 before
trusting the 12.5 V target — real cells vary batch to batch.
