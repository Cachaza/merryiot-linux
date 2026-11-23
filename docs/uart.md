# Pico UART bridge

I used a Pico because it was the first thing I found in the drawer. MicroPython was already installed. The payload below runs in RAM; it does not flash the Pico.

| Pico | Miner |
|---|---|
| GP1 / UART0 RX | TX pad |
| GP0 / UART0 TX | RX pad |
| GND | GND |

Power the miner separately. Do not connect power rails or a 5 V/RS-232 adapter to the UART pads. Check your board's signal levels and pad labels before connecting; this wiring was used on my unit. The original console was 1,500,000 baud, 8N1.

Find the Pico's USB CDC device using your OS's device list. No private device path is baked into the tool.

```
python3 tools/pico_uart.py --port YOUR_USB_CDC_DEVICE --log captures/session.bin
```

By default the host records output without forwarding keyboard input to the miner. It still loads the Pico program, which interrupts whatever was running on the Pico. The USB CDC line setting is 115200; the actual hardware UART baud rate is 1500000.

For an interactive console, add `--interactive`. Ctrl+C is then sent to the miner (useful for interrupting U-Boot); Ctrl+] stops the bridge on the Pico and exits the host console. The host restores terminal settings when it exits. It does not automatically interrupt the miner boot, issue shell commands, reset the outlet or install software.

Logs contain whatever the board prints, potentially including private details. The tool creates new capture files with owner-only permissions and refuses to overwrite an existing log. Keep captures out of Git. Exit any other serial bridge first; the packaged tool attempts an advisory exclusive device lock, which other programs may not honor.

The historical script used a private local command socket for scripted investigations. The packaged adaptation uses stdin instead, removing the socket service and private capture paths. Offline tests cover its byte-write and command payload helpers. A fresh physical capture with this version is still needed before calling this packaged bridge hardware-verified.
