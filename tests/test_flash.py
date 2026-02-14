from circuithack.flash import build_esptool_base


def test_build_esptool_base_contains_expected_flags() -> None:
    cmd = build_esptool_base(
        port="/dev/cu.usbmodem123",
        baud=921600,
        chip="esp32s3",
        before="default_reset",
        after="hard_reset",
    )
    s = " ".join(cmd)
    assert "--chip esp32s3" in s
    assert "--port /dev/cu.usbmodem123" in s
    assert "--baud 921600" in s
    assert "--before default_reset" in s
    assert "--after hard_reset" in s

