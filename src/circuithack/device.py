from __future__ import annotations

import glob
import platform
import subprocess
from dataclasses import asdict, dataclass

from serial.tools import list_ports


KNOWN_ESPRESSIF_VIDS = {0x303A}
LIKELY_USB_PATTERNS = ("usb", "acm", "modem", "wch", "cp210", "ch340", "serial")


@dataclass
class SerialDevice:
    path: str
    description: str
    manufacturer: str | None
    product: str | None
    serial_number: str | None
    vid: int | None
    pid: int | None

    def to_dict(self) -> dict:
        return asdict(self)


def list_serial_devices(only_likely_usb: bool = True) -> list[SerialDevice]:
    out: list[SerialDevice] = []
    for p in list_ports.comports():
        desc = (p.description or "").lower()
        dev = (p.device or "").lower()
        manu = (p.manufacturer or "").lower()
        if only_likely_usb:
            is_likely = any(x in desc or x in dev or x in manu for x in LIKELY_USB_PATTERNS)
            if not is_likely and p.vid not in KNOWN_ESPRESSIF_VIDS:
                continue
        out.append(
            SerialDevice(
                path=p.device,
                description=p.description or "",
                manufacturer=p.manufacturer,
                product=p.product,
                serial_number=p.serial_number,
                vid=p.vid,
                pid=p.pid,
            )
        )
    out.sort(key=lambda x: x.path)
    return out


def detect_codee_candidates() -> list[SerialDevice]:
    candidates: list[SerialDevice] = []
    for d in list_serial_devices(only_likely_usb=True):
        text = " ".join(
            x or "" for x in [d.path, d.description, d.manufacturer, d.product]
        ).lower()
        if d.vid in KNOWN_ESPRESSIF_VIDS or "espressif" in text or "usbmodem" in text:
            candidates.append(d)
    return candidates


def resolve_codee_port(port: str | None) -> str:
    if port:
        return port
    candidates = detect_codee_candidates()
    if not candidates:
        raise RuntimeError("No Codee-like USB serial device found.")
    return candidates[0].path


def macos_usb_summary() -> str:
    if platform.system() != "Darwin":
        return ""
    proc = subprocess.run(
        ["system_profiler", "SPUSBDataType"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc.stdout.strip()


def serial_node_snapshot() -> list[str]:
    nodes = glob.glob("/dev/cu.*") + glob.glob("/dev/tty.*")
    return sorted(nodes)
