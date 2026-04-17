from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from cv_engine.ingest.normalize import (
    NormalizationError,
    file_sha256,
    normalize_to_pdf,
)


def test_file_sha256_matches_manual(tmp_path: Path) -> None:
    p = tmp_path / "x.bin"
    p.write_bytes(b"hello cv")
    expected = hashlib.sha256(b"hello cv").hexdigest()
    assert file_sha256(p) == expected


def test_normalize_pdf_is_passthrough(tmp_path: Path) -> None:
    src = tmp_path / "in.pdf"
    src.write_bytes(b"%PDF-1.4 fake")
    dst_dir = tmp_path / "out"
    dst_dir.mkdir()

    result = normalize_to_pdf(src, dst_dir)

    assert result.pdf_path == src
    assert result.original_format == "pdf"
    assert result.sha256 == file_sha256(src)


def test_normalize_docx_invokes_soffice(tmp_path: Path, mocker) -> None:
    src = tmp_path / "in.docx"
    src.write_bytes(b"PKfake-docx")
    dst_dir = tmp_path / "out"
    dst_dir.mkdir()

    # Simulate soffice producing the output PDF
    def fake_run(cmd, *args, **kwargs):
        out_pdf = dst_dir / "in.pdf"
        out_pdf.write_bytes(b"%PDF-1.4 converted")
        class R:
            returncode = 0
            stdout = b""
            stderr = b""
        return R()

    mock_run = mocker.patch("cv_engine.ingest.normalize.subprocess.run", side_effect=fake_run)

    result = normalize_to_pdf(src, dst_dir)

    mock_run.assert_called_once()
    called_cmd = mock_run.call_args[0][0]
    assert called_cmd[0] == "soffice"
    assert "--headless" in called_cmd
    assert "--convert-to" in called_cmd
    assert "pdf" in called_cmd
    assert str(src) in called_cmd

    assert result.pdf_path == dst_dir / "in.pdf"
    assert result.original_format == "docx"
    assert result.sha256 == file_sha256(src)


def test_normalize_docx_raises_when_soffice_fails(tmp_path: Path, mocker) -> None:
    src = tmp_path / "in.docx"
    src.write_bytes(b"PKcorrupt")
    dst_dir = tmp_path / "out"
    dst_dir.mkdir()

    class R:
        returncode = 1
        stdout = b""
        stderr = b"Error: source file could not be loaded"

    mocker.patch("cv_engine.ingest.normalize.subprocess.run", return_value=R())

    with pytest.raises(NormalizationError, match="soffice exit 1"):
        normalize_to_pdf(src, dst_dir)


def test_normalize_rejects_unknown_format(tmp_path: Path) -> None:
    src = tmp_path / "resume.txt"
    src.write_bytes(b"plain text")
    dst_dir = tmp_path / "out"
    dst_dir.mkdir()

    with pytest.raises(NormalizationError, match="unsupported"):
        normalize_to_pdf(src, dst_dir)
