#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import struct
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class PreviewEntry:
    variant: str
    resource_id: int
    name: str
    png_relpath: str


@dataclass(frozen=True)
class RawAsset:
    resource_id: int
    name: str
    source_variant: str
    raw_relpath: str
    png_relpath: str
    width: int
    height: int
    byte_size: int


def parse_id_name_map(header_path: Path) -> dict[int, str]:
    pattern = re.compile(r"^#define\s+([A-Za-z_]\w*)\s+(\d+)\s*$")
    by_id: dict[int, str] = {}
    for line in header_path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        name, raw_id = match.group(1), match.group(2)
        resource_id = int(raw_id)
        by_id.setdefault(resource_id, name)
    return by_id


def parse_resource_fork(resource_path: Path) -> dict[str, list[tuple[int, bytes]]]:
    blob = resource_path.read_bytes()
    data_offset, map_offset, data_length, map_length = struct.unpack(">IIII", blob[:16])
    data_section = blob[data_offset : data_offset + data_length]
    map_section = blob[map_offset : map_offset + map_length]

    type_list_offset = struct.unpack(">H", map_section[24:26])[0]
    type_list = map_section[type_list_offset:]
    type_count = struct.unpack(">H", type_list[:2])[0] + 1

    result: dict[str, list[tuple[int, bytes]]] = {}
    for type_index in range(type_count):
        entry_offset = 2 + type_index * 8
        type_code = type_list[entry_offset : entry_offset + 4].decode("mac_roman", errors="replace")
        resource_count = struct.unpack(">H", type_list[entry_offset + 4 : entry_offset + 6])[0] + 1
        ref_list_offset = struct.unpack(">H", type_list[entry_offset + 6 : entry_offset + 8])[0]

        resources: list[tuple[int, bytes]] = []
        for ref_index in range(resource_count):
            ref_offset = ref_list_offset + ref_index * 12
            reference = type_list[ref_offset : ref_offset + 12]
            resource_id = struct.unpack(">h", reference[0:2])[0]
            data_offset_24 = int.from_bytes(reference[5:8], byteorder="big", signed=False)

            length = int.from_bytes(data_section[data_offset_24 : data_offset_24 + 4], byteorder="big", signed=False)
            payload_start = data_offset_24 + 4
            payload_end = payload_start + length
            payload = data_section[payload_start:payload_end]
            resources.append((resource_id, payload))

        result[type_code] = resources
    return result


def snake_case(name: str) -> str:
    with_underscores = re.sub(r"(?<!^)([A-Z])", r"_\1", name).lower()
    return re.sub(r"[^a-z0-9_]+", "_", with_underscores).strip("_")


def convert_pict_payload_to_png(payload: bytes, png_path: Path) -> None:
    pict_path = png_path.with_suffix(".pict")
    pict_path.write_bytes((b"\x00" * 512) + payload)
    subprocess.run(
        ["sips", "-s", "format", "png", str(pict_path), "--out", str(png_path)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    pict_path.unlink(missing_ok=True)


def png_to_rgb565_raw(png_path: Path) -> tuple[int, int, bytes]:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_bmp = Path(temp_dir) / "frame.bmp"
        subprocess.run(
            ["sips", "-s", "format", "bmp", str(png_path), "--out", str(temp_bmp)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        bmp = temp_bmp.read_bytes()

    if len(bmp) < 54 or bmp[:2] != b"BM":
        raise ValueError(f"Unsupported BMP generated from {png_path}")

    pixel_offset = struct.unpack_from("<I", bmp, 10)[0]
    dib_size = struct.unpack_from("<I", bmp, 14)[0]
    if dib_size < 40:
        raise ValueError(f"Unsupported BMP DIB header for {png_path}")

    width = struct.unpack_from("<i", bmp, 18)[0]
    height_raw = struct.unpack_from("<i", bmp, 22)[0]
    planes = struct.unpack_from("<H", bmp, 26)[0]
    bpp = struct.unpack_from("<H", bmp, 28)[0]
    compression = struct.unpack_from("<I", bmp, 30)[0]

    if planes != 1 or compression != 0:
        raise ValueError(f"Unsupported BMP layout for {png_path}")
    if bpp not in (24, 32):
        raise ValueError(f"Unsupported BMP bit depth {bpp} for {png_path}")

    is_top_down = height_raw < 0
    height = abs(height_raw)
    row_stride = ((bpp * width + 31) // 32) * 4

    raw = bytearray(width * height * 2)
    out_index = 0

    for row in range(height):
        src_row = row if is_top_down else (height - 1 - row)
        row_start = pixel_offset + (src_row * row_stride)

        for col in range(width):
            px_start = row_start + (col * (bpp // 8))
            blue = bmp[px_start]
            green = bmp[px_start + 1]
            red = bmp[px_start + 2]

            value = ((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3)
            struct.pack_into("<H", raw, out_index, value)
            out_index += 2

    return width, height, bytes(raw)


def build_preview_html(output_path: Path, entries: list[PreviewEntry]) -> None:
    entries_by_variant: dict[str, list[PreviewEntry]] = {}
    for entry in entries:
        entries_by_variant.setdefault(entry.variant, []).append(entry)

    for variant_entries in entries_by_variant.values():
        variant_entries.sort(key=lambda item: item.resource_id)

    parts: list[str] = []
    parts.append("<!doctype html>")
    parts.append("<html><head><meta charset='utf-8'><title>SpaceTrader PNG Preview</title>")
    parts.append(
        "<style>"
        "body{font-family:system-ui,Arial,sans-serif;background:#0f1115;color:#e8ecf1;margin:0;padding:20px;}"
        "h1{margin:0 0 8px;}h2{margin:24px 0 10px;color:#9ecbff;}"
        ".meta{color:#9aa5b1;margin-bottom:16px;}"
        ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;}"
        ".card{background:#171b22;border:1px solid #2b313d;border-radius:8px;padding:10px;}"
        ".card img{width:100%;height:120px;object-fit:contain;background:#0b0e13;border-radius:6px;}"
        ".cap{margin-top:8px;font-size:12px;line-height:1.4;color:#d7dee8;}"
        ".id{color:#8fb5ff;}"
        "</style>"
    )
    parts.append("</head><body>")
    parts.append("<h1>SpaceTrader extracted PNG preview</h1>")
    parts.append("<div class='meta'>Generated from Palm resource forks (PICT → PNG via sips).</div>")

    order = ["color", "gray", "bw", "ui"]
    for variant in order:
        variant_entries = entries_by_variant.get(variant)
        if not variant_entries:
            continue
        parts.append(f"<h2>{variant.upper()} ({len(variant_entries)})</h2>")
        parts.append("<div class='grid'>")
        for entry in variant_entries:
            name = html.escape(entry.name)
            img_src = html.escape(entry.png_relpath)
            parts.append(
                "<div class='card'>"
                f"<img loading='lazy' src='{img_src}' alt='{name}'>"
                f"<div class='cap'><span class='id'>PICT {entry.resource_id}</span><br>{name}</div>"
                "</div>"
            )
        parts.append("</div>")

    parts.append("</body></html>")
    output_path.write_text("".join(parts), encoding="utf-8")


def resolve_resource_path(source_dir: Path, filename: str) -> Path:
    forked = source_dir / "Resource.frk" / filename
    direct = source_dir / filename
    if forked.exists():
        return forked
    if direct.exists():
        return direct
    raise FileNotFoundError(f"Could not find {filename} in {source_dir} or Resource.frk")


def parse_variant_order(raw: str) -> list[str]:
    order = [part.strip().lower() for part in raw.split(",") if part.strip()]
    allowed = {"color", "gray", "bw", "ui"}
    invalid = [name for name in order if name not in allowed]
    if invalid:
        raise ValueError(f"Unknown variant(s): {', '.join(invalid)}")
    if not order:
        raise ValueError("Variant order cannot be empty")
    return order


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract SpaceTrader Palm PICT assets, convert to RGB565 raw, and optionally sync to Bit-Firmware SPIFFS."
    )
    parser.add_argument(
        "--source-dir",
        default="downloads/SpaceTraderSource/Rsc",
        help="Directory containing Merchant*.rsrc files (or a nested Resource.frk/).",
    )
    parser.add_argument(
        "--header",
        default="downloads/SpaceTraderSource/Rsc/MerchantGraphics.h",
        help="Header file containing PICT id/name mappings.",
    )
    parser.add_argument(
        "--out-dir",
        default="downloads/SpaceTraderSource/converted_bit_assets",
        help="Output directory for generated PNG/RAW assets and manifest.",
    )
    parser.add_argument(
        "--bit-spiffs-dir",
        default="third_party/Bit-Firmware/spiffs_image/Games/SpaceTrader",
        help="Destination directory for syncing generated .raw files into Bit-Firmware SPIFFS image.",
    )
    parser.add_argument(
        "--skip-spiffs-sync",
        action="store_true",
        help="Skip syncing .raw files into Bit-Firmware SPIFFS directory.",
    )
    parser.add_argument(
        "--prefer-variants",
        default="color,gray,bw,ui",
        help="Comma-separated lookup order when selecting a PICT resource by id.",
    )
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()
    header_path = Path(args.header).resolve()
    out_dir = Path(args.out_dir).resolve()
    spiffs_dir = Path(args.bit_spiffs_dir).resolve()
    variant_order = parse_variant_order(args.prefer_variants)

    resources = {
        "color": resolve_resource_path(source_dir, "MerchantColor.rsrc"),
        "gray": resolve_resource_path(source_dir, "MerchantGray.rsrc"),
        "bw": resolve_resource_path(source_dir, "MerchantBW.rsrc"),
        "ui": resolve_resource_path(source_dir, "Merchant.rsrc"),
    }

    id_name_map = parse_id_name_map(header_path)

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    png_root = out_dir / "png"
    raw_root = out_dir / "raw"
    png_root.mkdir(parents=True, exist_ok=True)
    raw_root.mkdir(parents=True, exist_ok=True)

    entries: list[PreviewEntry] = []
    pict_by_variant: dict[str, dict[int, bytes]] = {}

    for variant, resource_path in resources.items():
        variant_dir = png_root / variant
        variant_dir.mkdir(parents=True, exist_ok=True)
        parsed = parse_resource_fork(resource_path)
        pict_items = parsed.get("PICT", [])
        pict_by_variant[variant] = {resource_id: payload for resource_id, payload in pict_items}

        for resource_id, payload in pict_items:
            base_name = id_name_map.get(resource_id, f"PICT_{resource_id}")
            file_stem = f"{resource_id}_{snake_case(base_name)}"
            png_path = variant_dir / f"{file_stem}.png"
            convert_pict_payload_to_png(payload, png_path)
            entries.append(
                PreviewEntry(
                    variant=variant,
                    resource_id=resource_id,
                    name=base_name,
                    png_relpath=png_path.relative_to(out_dir).as_posix(),
                )
            )

    all_resource_ids = sorted({resource_id for resources_map in pict_by_variant.values() for resource_id in resources_map})
    raw_assets: list[RawAsset] = []

    for resource_id in all_resource_ids:
        chosen_variant = ""
        chosen_payload = b""
        for variant in variant_order:
            payload = pict_by_variant.get(variant, {}).get(resource_id)
            if payload is None:
                continue
            chosen_variant = variant
            chosen_payload = payload
            break

        if not chosen_variant:
            continue

        name = id_name_map.get(resource_id, f"PICT_{resource_id}")
        file_stem = f"{resource_id}_{snake_case(name)}"

        chosen_png_path = png_root / "selected" / f"{file_stem}.png"
        chosen_png_path.parent.mkdir(parents=True, exist_ok=True)
        convert_pict_payload_to_png(chosen_payload, chosen_png_path)

        width, height, rgb565 = png_to_rgb565_raw(chosen_png_path)
        expected_size = width * height * 2
        if len(rgb565) != expected_size:
            raise ValueError(
                f"RGB565 size mismatch for {file_stem}: expected {expected_size}, got {len(rgb565)}"
            )

        raw_path = raw_root / f"{file_stem}.raw"
        raw_path.write_bytes(rgb565)

        raw_assets.append(
            RawAsset(
                resource_id=resource_id,
                name=name,
                source_variant=chosen_variant,
                raw_relpath=raw_path.relative_to(out_dir).as_posix(),
                png_relpath=chosen_png_path.relative_to(out_dir).as_posix(),
                width=width,
                height=height,
                byte_size=len(rgb565),
            )
        )

    if not args.skip_spiffs_sync:
        if spiffs_dir.exists():
            shutil.rmtree(spiffs_dir)
        spiffs_dir.mkdir(parents=True, exist_ok=True)
        for asset in raw_assets:
            shutil.copy2(out_dir / asset.raw_relpath, spiffs_dir / Path(asset.raw_relpath).name)

    manifest = {
        "tool": "scripts/spacetrader_preview.py",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_dir": str(source_dir),
        "header": str(header_path),
        "variant_order": variant_order,
        "assets": [
            {
                "resource_id": asset.resource_id,
                "name": asset.name,
                "source_variant": asset.source_variant,
                "raw_path": asset.raw_relpath,
                "png_path": asset.png_relpath,
                "width": asset.width,
                "height": asset.height,
                "byte_size": asset.byte_size,
            }
            for asset in raw_assets
        ],
    }
    (out_dir / "assets_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if not args.skip_spiffs_sync:
        spiffs_manifest = dict(manifest)
        spiffs_manifest["spiffs_dir"] = str(spiffs_dir)
        (spiffs_dir / "assets_manifest.json").write_text(json.dumps(spiffs_manifest, indent=2), encoding="utf-8")

    build_preview_html(out_dir / "index.html", entries)
    print(f"Generated {len(entries)} variant PNG images.")
    print(f"Generated {len(raw_assets)} RGB565 raw assets.")
    print(f"Manifest: {out_dir / 'assets_manifest.json'}")
    print(f"Preview: {out_dir / 'index.html'}")
    if args.skip_spiffs_sync:
        print("SPIFFS sync skipped.")
    else:
        print(f"Synced RAW assets to: {spiffs_dir}")


if __name__ == "__main__":
    main()
