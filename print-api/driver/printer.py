"""Printer driver: manages the ESC/POS connection lifecycle.

Supports three backends:
  - 'file'     : escpos.printer.File (Linux — /dev/thermalprinter)
  - 'win32raw' : escpos.printer.Win32Raw (Windows — printer name)
  - 'dummy'    : escpos.printer.Dummy (development/testing)
"""
import os
import logging

import config
from .escpos_builder import build_escpos_commands

logger = logging.getLogger(__name__)

# ESC/POS init command for resetting printer state after reconnect
ESC_INIT = b"\x1B\x40"


class PrinterDriver:
    def __init__(self, device: str, backend: str = None):
        self._device = device
        self._backend = backend or config.PRINTER_BACKEND
        self._printer = None

    def _open(self):
        """Open or reopen the printer handle."""
        if self._printer is not None:
            try:
                self._printer.close()
            except Exception:
                pass
            self._printer = None

        if self._backend == 'file':
            from escpos.printer import File
            self._printer = File(self._device)
        elif self._backend == 'win32raw':
            from escpos.printer import Win32Raw
            self._printer = Win32Raw(self._device)
        elif self._backend == 'dummy':
            from escpos.printer import Dummy
            self._printer = Dummy()
        else:
            raise ValueError(f"Unknown printer backend: {self._backend}")

        logger.info("Printer opened: %s (backend=%s)", self._device, self._backend)

    def _ensure_connected(self):
        """Verify connection, reopen if needed."""
        if self._printer is None:
            self._open()
            return

        # On Linux, check if device file still exists
        if self._backend == 'file' and not os.path.exists(self._device):
            self._printer = None
            raise IOError(f"Printer device {self._device} not found")

    def is_available(self) -> bool:
        """Check if the printer device is accessible."""
        if self._backend == 'file':
            return os.path.exists(self._device)
        if self._backend == 'dummy':
            return True
        # Win32: try to verify printer exists
        if self._backend == 'win32raw':
            try:
                import win32print
                printers = [p[2] for p in win32print.EnumPrinters(2)]
                return self._device in printers
            except Exception:
                return False
        return False

    def print_job(self, job):
        """Execute a print job. Called from the queue consumer thread only.

        Args:
            job: PrintJob instance with payload dict and is_raw flag.
        """
        self._ensure_connected()

        if job.is_raw:
            raw_data = job.payload.get('raw_data', b'')
            self._send_raw(raw_data)
        else:
            commands = build_escpos_commands(job.payload)
            self._send_raw(commands)

    def _send_raw(self, data: bytes):
        """Send raw bytes to the printer with retry-once on I/O error."""
        try:
            self._write(data)
        except (IOError, OSError) as e:
            logger.warning("Print I/O error, reopening: %s", e)
            self._open()
            self._write(ESC_INIT + data)  # re-init printer state then retry

    def _write(self, data: bytes):
        """Write bytes to the printer handle."""
        if self._backend == 'dummy':
            # Dummy printer: just accumulate output silently
            self._printer._raw(data)
            logger.debug("Dummy printer received %d bytes", len(data))
            return

        self._printer._raw(data)

    def close(self):
        if self._printer:
            try:
                self._printer.close()
            except Exception:
                pass
            self._printer = None
