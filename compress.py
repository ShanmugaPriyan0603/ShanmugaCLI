"""Compression backend for the ShanmugaCLI compress command."""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
PDF_EXTENSIONS = {".pdf"}


def result(ok: bool, **values: object) -> None:
    print(json.dumps({"ok": ok, **values}))


def output_path(source: Path, suffix: str) -> Path:
    candidate = source.with_name(f"{source.stem}_{suffix}{source.suffix}")
    number = 2
    while candidate.exists():
        candidate = source.with_name(f"{source.stem}_{suffix}_{number}{source.suffix}")
        number += 1
    return candidate


def zip_path(source: Path) -> Path:
    candidate = source.with_suffix(".zip")
    number = 2
    while candidate.exists():
        candidate = source.with_name(f"{source.stem}_{number}.zip")
        number += 1
    return candidate


def compress_image(source: Path, level: str) -> Path:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "Image compression requires Pillow. Install it with: python -m pip install Pillow"
        ) from exc

    destination = output_path(source, f"compressed_{level}")
    with Image.open(source) as image:
        if source.suffix.lower() in {".jpg", ".jpeg"}:
            quality = {"high": 90, "balanced": 75, "small": 50}[level]
            if image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
            image.save(
                destination,
                quality=quality,
                optimize=True,
                progressive=True,
            )
        else:
            colors = {"high": 256, "balanced": 128, "small": 64}[level]
            if image.mode not in {"P", "L"}:
                image = image.convert("RGBA")
            image = image.quantize(colors=colors)
            image.save(destination, optimize=True, compress_level=9)
    return destination


def compress_pdf(source: Path, level: str) -> Path:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(
            "PDF compression requires PyMuPDF. Install it with: python -m pip install PyMuPDF"
        ) from exc

    destination = output_path(source, f"compressed_{level}")
    document = fitz.open(source)
    try:
        document.save(
            destination,
            garbage=4,
            clean=True,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True,
        )
    finally:
        document.close()
    return destination


def compress_to_zip(source: Path) -> Path:
    destination = zip_path(source)
    with zipfile.ZipFile(
        destination,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        archive.write(source, arcname=source.name)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Compress a supported file.")
    parser.add_argument("action", choices=("compress", "zip"))
    parser.add_argument("--path", required=True)
    parser.add_argument("--level", choices=("high", "balanced", "small"))
    args = parser.parse_args()

    source = Path(args.path).expanduser().resolve()
    if not source.is_file():
        result(False, error="The selected path is not a file.")
        return 1

    extension = source.suffix.lower()
    if extension not in IMAGE_EXTENSIONS | PDF_EXTENSIONS:
        result(False, error="Only JPG, PNG, and PDF files are supported.")
        return 1

    if args.action == "compress" and not args.level:
        result(False, error="A compression level is required.")
        return 1

    try:
        destination = (
            compress_to_zip(source)
            if args.action == "zip"
            else (
                compress_image(source, args.level)
                if extension in IMAGE_EXTENSIONS
                else compress_pdf(source, args.level)
            )
        )
        result(
            True,
            source=str(source),
            destination=str(destination),
            original_size=source.stat().st_size,
            compressed_size=destination.stat().st_size,
        )
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        result(False, error=str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
