#!/usr/bin/env python3
"""RAM-only Pico/MicroPython UART capture for the measured MerryIoT console."""
import argparse
import fcntl
import io
import os
from pathlib import Path
import select
import signal
import sys
import termios
import tty

# Measured UART configuration from this unit: UART0 GP0/GP1, 1.5 Mbaud, 8N1.
# GS is MicroPython's interrupt byte so Ctrl+C can pass through to the miner.
PAYLOAD = b'''import sys, select, micropython
from machine import UART, Pin
uart = UART(0, baudrate=1500000, bits=8, parity=None, stop=1, tx=Pin(0), rx=Pin(1), timeout=0)
p = select.poll()
p.register(sys.stdin, select.POLLIN)
print("BRIDGE_READY")
micropython.kbd_intr(29)
while True:
    data = uart.read(uart.any()) if uart.any() else None
    if data:
        sys.stdout.buffer.write(data)
    if p.poll(0):
        data = sys.stdin.buffer.read(1)
        if data:
            uart.write(data)
'''


def write_all(fd, data):
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        if written == 0:
            raise OSError('Serial write made no progress; reconnect the Pico.')
        view = view[written:]


def read_until(fd, marker):
    data = bytearray()
    while marker not in data:
        select.select([fd], [], [])
        block = os.read(fd, io.DEFAULT_BUFFER_SIZE)  # Python's standard I/O buffer size.
        if not block:
            raise OSError('Pico disconnected before the bridge became ready.')
        data.extend(block)
    return bytes(data)


def capture(port, log_path, interactive=False):
    if interactive and not sys.stdin.isatty():
        raise ValueError('--interactive requires a terminal; omit it for capture only.')
    fd, output, serial_state, input_state = None, None, None, None
    bridge_started = False
    try:
        fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.set_blocking(fd, True)
        serial_state = termios.tcgetattr(fd)
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        output = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        tty.setraw(fd)
        settings = termios.tcgetattr(fd)
        settings[4] = settings[5] = termios.B115200  # USB CDC setting, not UART baud.
        termios.tcsetattr(fd, termios.TCSANOW, settings)
        print('Loading RAM bridge on Pico. Ctrl+C cancels setup; no miner boot commands are sent.', flush=True)
        write_all(fd, b'\x1d\x03\x03\x01')  # Interrupt an old bridge or REPL; enter raw REPL.
        read_until(fd, b'raw REPL; CTRL-B to exit\r\n>')
        write_all(fd, PAYLOAD + b'\x04')
        response = read_until(fd, b'BRIDGE_READY\r\n')
        if not response.startswith(b'OK'):
            raise ValueError('Unexpected MicroPython reply; inspect Pico firmware and serial connection.')
        bridge_started = True
        write_all(output, response)
        if interactive:
            input_state = termios.tcgetattr(sys.stdin.fileno())
            tty.setraw(sys.stdin.fileno())
        print('Bridge ready. Ctrl+] exits interactive mode; Ctrl+C exits capture-only mode.', flush=True)
        while True:
            watched = [fd, sys.stdin.fileno()] if interactive else [fd]
            ready, _, _ = select.select(watched, [], [])
            if fd in ready:
                data = os.read(fd, io.DEFAULT_BUFFER_SIZE)
                if not data:
                    raise OSError('Pico disconnected; captured bytes remain in the log.')
                write_all(output, data)
                write_all(sys.stdout.fileno(), data)
            if interactive and sys.stdin.fileno() in ready:
                data = os.read(sys.stdin.fileno(), 1)  # One key: preserve the exit shortcut.
                if not data or data == b'\x1d':
                    break
                write_all(fd, data)
    finally:
        if input_state is not None:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, input_state)
        if fd is not None:
            if bridge_started:
                try:
                    write_all(fd, b'\x1d')  # Stop RAM bridge on Pico, not Ctrl+C on miner.
                except OSError:
                    pass
            if serial_state is not None:
                try:
                    termios.tcsetattr(fd, termios.TCSANOW, serial_state)
                except termios.error:
                    pass
            os.close(fd)
        if output is not None:
            os.close(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True, help='Your authorized Pico USB CDC device')
    parser.add_argument('--log', required=True, type=Path, help='New private capture file; refuses overwrites')
    parser.add_argument('--interactive', action='store_true', help='Forward keystrokes to miner; Ctrl+] exits')
    args = parser.parse_args()
    previous_handlers = {sig: signal.signal(sig, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
                         for sig in (signal.SIGTERM, signal.SIGHUP)}
    try:
        capture(args.port, args.log, args.interactive)
    except KeyboardInterrupt:
        print('\nCapture stopped.', file=sys.stderr)
    except (OSError, ValueError, termios.error) as exc:
        parser.exit(1, f'Capture failed: {exc}\n')
    finally:
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)


if __name__ == '__main__':
    main()
