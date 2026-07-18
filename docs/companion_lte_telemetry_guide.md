# Companion Computer + LTE Telemetry — Phase 3 (secondary link)

Companion to `docs/gps_sensors_wiring_guide.md`. ELRS stays the primary
control link — this phase is a test feature layered on top of manual
flight, not a replacement for it. ArduPilot gives RC stick input priority
over GCS commands by design, which matches that intent.

## Architecture

```
FC (MAVLink) --UART, crossed TX/RX--> Pi Zero 2 W (mavlink-router)
                                            |
                                            v
                                    A7670E modem (USB/ECM preferred)
                                            |
                                        cellular
                                            |
                                            v
                              Hetzner VPS (public IP, root)
                                mavlink-router relay, UDP :14550
                                            ^
                                            | outbound only, no port-forward
                                            |
                                  Home server: QGroundControl
```

Both the Pi (mobile, cellular, no fixed address) and the home server
connect outbound to the VPS's fixed public IP. Neither needs inbound
port-forwarding on the home network or a static cellular IP.

## Power wiring

| Rail | Feed | Note |
|---|---|---|
| Pi Zero 2 W - 5V | Dedicated buck (MP1584EN or MINI360), own ~2A branch fuse | Not shared with the modem rail. |
| A7670E modem - 3.8-4.0V | Separate dedicated buck, own ~3A branch fuse | Modem has high current TX pulses during transmit bursts - sharing the Pi's 5V rail can brown it out. This is what the 10x 1000uF caps from the original order are for: place one at the modem's VBAT pin. |
| Common ground | Pi, FC, modem, battery negative all tied together | Required for the UART link to read correctly. |

## Bring-up sequence

1. **Wire FC <-> Pi UART.** FC TX -> Pi RX, FC RX -> Pi TX (crossed), shared
   ground. Use a spare FC UART not already used by the ELRS receiver or GPS
   port. Set that UART's `SERIALx_PROTOCOL = 1` or `2` (MAVLink1/2) and
   match baud rate on both ends.
2. **Wire the modem - USB preferred over UART.** If the A7670E breakout
   exposes USB, use it: most SIMCom-compatible modules can present as a
   standard USB network interface (ECM/RNDIS mode), so Linux just sees a
   new network device and DHCPs an address - far simpler than driving PPP
   over UART. Check the board's documentation for how to enable this mode
   (usually an AT command).
3. **Bring up cellular data on the Pi.** Insert the SIM, power the modem on
   its dedicated rail. If it enumerated as USB ECM/RNDIS:
   ```
   ip link show                 # find the new interface, e.g. usb0
   sudo dhclient usb0
   ping -I usb0 -c 3 8.8.8.8    # confirm real internet reachability
   ```
   UART-only boards need PPP instead (AT+CGDATA/pppd) - more fragile, only
   use if USB genuinely isn't available.
4. **Set up the VPS relay (Hetzner).**
   ```
   sudo apt update && sudo apt install -y git meson ninja-build pkg-config gcc g++ systemd
   git clone https://github.com/mavlink-router/mavlink-router --recursive
   cd mavlink-router && meson setup build . && ninja -C build && sudo ninja -C build install
   sudo ufw allow 14550/udp
   ```
   Configure `/etc/mavlink-router/main.conf` with a UDP server endpoint on
   `0.0.0.0:14550` (learns the Pi's and QGC's addresses automatically once
   each sends traffic to it), run as a systemd service.
5. **Point the Pi's mavlink-router at the VPS** - a UART endpoint reading
   the FC's MAVLink stream, and a UDP normal/client endpoint targeting
   `<VPS public IP>:14550`.
6. **Connect QGroundControl from the home server** - add a UDP comm link
   targeting `<VPS public IP>:14550`. QGC sending anything to the VPS is
   enough for mavlink-router to learn its address - no inbound firewall
   rule needed on the home network.
7. **Bench-test the whole chain before the first flight.** With the plane
   on the bench, confirm telemetry (attitude, GPS, battery) shows up live
   through the full FC -> Pi -> cellular -> VPS -> home server path,
   including a deliberate signal-loss test (power off the modem, confirm
   QGC shows the link as lost rather than hanging).

## Known risks

- **Latency:** cellular round-trip adds real delay vs ELRS. Treat this as
  telemetry/monitoring, not fast manual control.
- **Coverage:** LTE can drop mid-flight with no warning. This relay chain
  has no failsafe of its own - ArduPilot's RC-loss failsafe (Phase 1) is
  what actually protects the plane, not this link.
- **VPS cost:** mavlink-router's idle load on a small instance is
  negligible - shouldn't need an upgrade from the current tier.

Exact AT commands and USB mode switching depend on the specific A7670E
breakout's firmware - check its documentation for the ECM/RNDIS enable
command before step 3.
