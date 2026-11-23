import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import pty
import signal
import subprocess
import sys
import termios
import threading
import unittest
from unittest.mock import patch


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


backup = load('verify_backups')
uart = load('pico_uart')


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / 'image.img'
        self.path.write_bytes(b'original image')
        self.record = {'path': 'image.img', 'bytes': self.path.stat().st_size, 'sha256': hashlib.sha256(self.path.read_bytes()).hexdigest()}

    def test_matching_image_and_nested_image(self):
        self.assertEqual(backup.verify(self.root, {'files': [self.record]}), ['image.img'])
        (self.root / 'nested').mkdir()
        self.path.rename(self.root / 'nested/image.img')
        self.assertEqual(backup.verify(self.root, {'files': [{**self.record, 'path': 'nested/image.img'}]}), ['nested/image.img'])

    def test_modified_content_and_truncation(self):
        self.path.write_bytes(b'changed! image')  # Same byte count, different hash.
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            backup.verify(self.root, {'files': [self.record]})
        self.path.write_bytes(b'short')
        with self.assertRaisesRegex(ValueError, 'expected .* bytes, found'):
            backup.verify(self.root, {'files': [self.record]})

    def test_traversal_absolute_paths_and_duplicates(self):
        for path in ['../image.img', str(self.path)]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                backup.verify(self.root, {'files': [{**self.record, 'path': path}]})
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            backup.verify(self.root, {'files': [self.record, self.record]})

    def test_symlink_and_symlink_parent_rejected(self):
        (self.root / 'link.img').symlink_to(self.path)
        with self.assertRaises(OSError):
            backup.verify(self.root, {'files': [{**self.record, 'path': 'link.img'}]})
        (self.root / 'linked-dir').symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(OSError):
            backup.verify(self.root, {'files': [{**self.record, 'path': 'linked-dir/image.img'}]})

    def test_fifo_does_not_block(self):
        os.mkfifo(self.root / 'pipe')
        with self.assertRaisesRegex(ValueError, 'not a regular'):
            backup.verify(self.root, {'files': [{**self.record, 'path': 'pipe', 'bytes': 0}]})

    def test_malformed_records(self):
        for manifest in [[], {}, {'files': []}, {'files': ['bad']}, {'files': [{**self.record, 'sha256': 'placeholder'}]}, {'files': [{**self.record, 'bytes': True}]}]:
            with self.subTest(manifest=manifest), self.assertRaises(ValueError):
                backup.verify(self.root, manifest)


class BridgeTests(unittest.TestCase):
    def test_partial_serial_writes_preserve_all_bytes(self):
        data = b'command\x03\r'
        sent = bytearray()
        def partial(fd, view):
            sent.extend(view[:1])
            return 1
        with patch.object(uart.os, 'write', partial):
            uart.write_all(1, data)
        self.assertEqual(bytes(sent), data)

    def test_disconnected_write_fails_instead_of_spinning(self):
        with patch.object(uart.os, 'write', return_value=0), self.assertRaises(OSError):
            uart.write_all(1, b'x')

    def test_split_raw_repl_marker(self):
        blocks = [b'raw RE', b'PL; CTRL-B to exit\r\n>']
        with patch.object(uart.select, 'select', return_value=([1], [], [])), patch.object(uart.os, 'read', side_effect=blocks):
            self.assertEqual(uart.read_until(1, b'raw REPL; CTRL-B to exit\r\n>'), b''.join(blocks))

    def test_disconnect_during_setup(self):
        with patch.object(uart.select, 'select', return_value=([1], [], [])), patch.object(uart.os, 'read', return_value=b''), self.assertRaises(OSError):
            uart.read_until(1, b'never')


class TerminalCleanupTests(unittest.TestCase):
    def test_hangup_and_termination_restore_interactive_terminal(self):
        # Two synthetic PTYs model the Pico CDC port and the user's keyboard.
        # Signal only after the child's ready message proves raw mode is active.
        for stop_signal in (signal.SIGHUP, signal.SIGTERM):
            with self.subTest(signal=stop_signal), tempfile.TemporaryDirectory() as directory:
                serial_master, serial_slave = pty.openpty()
                input_master, input_slave = pty.openpty()
                original = termios.tcgetattr(input_slave)
                process = None
                def pico():
                    data = b''
                    while b'\x01' not in data:
                        data += os.read(serial_master, 1)
                    os.write(serial_master, b'raw REPL; CTRL-B to exit\r\n>')
                    data = b''
                    while b'\x04' not in data:
                        data += os.read(serial_master, 1)
                    os.write(serial_master, b'OKBRIDGE_READY\r\n')
                thread = threading.Thread(target=pico, daemon=True)
                thread.start()
                try:
                    process = subprocess.Popen(
                        [sys.executable, str(Path(__file__).parents[1] / 'tools/pico_uart.py'),
                         '--port', os.ttyname(serial_slave), '--log', str(Path(directory) / 'capture.bin'), '--interactive'],
                        stdin=input_slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.assertIn(b'Loading RAM bridge', process.stdout.readline())
                    self.assertIn(b'Bridge ready.', process.stdout.readline())
                    mask = termios.ICANON | termios.ECHO | termios.ISIG
                    self.assertEqual(termios.tcgetattr(input_slave)[3] & mask, 0)
                    process.send_signal(stop_signal)
                    process.communicate()
                    self.assertEqual(process.returncode, 0)
                    restored = termios.tcgetattr(input_slave)
                    # macOS sets the kernel's PENDIN pending-retype flag when
                    # canonical mode returns; it is not a persistent tty setting.
                    restored[3] &= ~getattr(termios, 'PENDIN', 0)
                    expected = original.copy()
                    expected[3] &= ~getattr(termios, 'PENDIN', 0)
                    self.assertEqual(restored, expected)
                    self.assertEqual((Path(directory) / 'capture.bin').stat().st_mode & 0o777, 0o600)
                finally:
                    if process and process.poll() is None:
                        process.kill()
                        process.communicate()
                    for fd in (serial_master, serial_slave, input_master, input_slave):
                        os.close(fd)


if __name__ == '__main__':
    unittest.main()
