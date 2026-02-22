#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
import shutil
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PreviewEntry:
    variant: str
    resource_id: int
    name: str
    png_relpath: str


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract SpaceTrader PICT assets and build HTML preview.")
    parser.add_argument(
        "--source-dir",
        default="downloads/SpaceTraderSource/Rsc/Resource.frk",
        help="Directory containing resource fork .rsrc files.",
    )
    parser.add_argument(
        "--header",
        default="downloads/SpaceTraderSource/Rsc/MerchantGraphics.h",
        help="Header file containing PICT id/name mappings.",
    )
    parser.add_argument(
        "--out-dir",
        default="downloads/SpaceTraderSource/converted_preview",
        help="Output directory for extracted PNG files and HTML.",
    )
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()
    header_path = Path(args.header).resolve()
    out_dir = Path(args.out_dir).resolve()

    resources = {
        "color": source_dir / "MerchantColor.rsrc",
        "gray": source_dir / "MerchantGray.rsrc",
        "bw": source_dir / "MerchantBW.rsrc",
        "ui": source_dir / "Merchant.rsrc",
    }

    for path in resources.values():
        if not path.exists():
            raise FileNotFoundError(path)

    id_name_map = parse_id_name_map(header_path)

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    entries: list[PreviewEntry] = []
    for variant, resource_path in resources.items():
        variant_dir = out_dir / variant
        variant_dir.mkdir(parents=True, exist_ok=True)
        parsed = parse_resource_fork(resource_path)
        pict_items = parsed.get("PICT", [])

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

    build_preview_html(out_dir / "index.html", entries)
    print(f"Generated {len(entries)} images.")
    print(f"Preview: {out_dir / 'index.html'}")


if __name__ == "__main__":
    main()
