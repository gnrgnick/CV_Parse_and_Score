"""DOCX → PDF normalization via LibreOffice headless.

The foundational slice accepts PDF and DOCX attachments. PDFs pass through
untouched. DOCX files are converted to PDF via `soffice --headless --convert-to pdf`.
Anything else raises NormalizationError immediately — the caller is expected
to mark the run as failed.
"""
from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path


class NormalizationError(Exception):
    """Raised when a CV attachment cannot be normalized to PDF."""


@dataclass(frozen=True)
class NormalizedCV:
    pdf_path: Path
    original_format: str
    sha256: str


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_to_pdf(src: Path, output_dir: Path) -> NormalizedCV:
    """Return a PDF path for `src`. PDFs are returned unchanged; DOCX is converted."""
    suffix = src.suffix.lower()
    src_sha = file_sha256(src)

    if suffix == ".pdf":
        return NormalizedCV(pdf_path=src, original_format="pdf", sha256=src_sha)

    if suffix == ".docx":
        return NormalizedCV(
            pdf_path=_convert_docx_to_pdf(src, output_dir),
            original_format="docx",
            sha256=src_sha,
        )

    raise NormalizationError(f"unsupported attachment format: {suffix!r}")


def _convert_docx_to_pdf(src: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "soffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", str(output_dir),
        str(src),
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=120)
    if result.returncode != 0:
        raise NormalizationError(
            f"soffice exit {result.returncode}: {result.stderr.decode(errors='replace')[:500]}"
        )
    expected_pdf = output_dir / (src.stem + ".pdf")
    if not expected_pdf.exists():
        raise NormalizationError(f"soffice exited 0 but produced no file at {expected_pdf}")
    return expected_pdf
