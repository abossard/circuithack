import pytest

from circuithack.device import SerialDevice, resolve_codee_port


def test_resolve_codee_port_prefers_explicit_port() -> None:
    assert resolve_codee_port("/dev/cu.usbmodem123") == "/dev/cu.usbmodem123"


def test_resolve_codee_port_uses_detected_candidate(monkeypatch) -> None:
    monkeypatch.setattr(
        "circuithack.device.detect_codee_candidates",
        lambda: [
            SerialDevice(
                path="/dev/cu.usbmodemAAA",
                description="USB Serial",
                manufacturer="Espressif",
                product="Codee",
                serial_number=None,
                vid=0x303A,
                pid=0x1001,
            )
        ],
    )
    assert resolve_codee_port(None) == "/dev/cu.usbmodemAAA"


def test_resolve_codee_port_raises_when_no_candidates(monkeypatch) -> None:
    monkeypatch.setattr("circuithack.device.detect_codee_candidates", lambda: [])
    with pytest.raises(RuntimeError, match="No Codee-like USB serial device found."):
        resolve_codee_port(None)
