"""Atomic, verified text-fidelity exports; never promises original cell types.
CSV is UTF-8 comma-separated; TXT is UTF-8 tab-separated; Excel is XLSX.
Suffixes are not restricted. None/NaN/NaT become empty strings; literal
NA/null/nan stay literal. Numbers, including Excel numbers, become text.
Content digest: UTF-8 compact JSON [headers, rows], in original order.
"""
import csv
import hashlib
import json
import os
from pathlib import Path
import tempfile
import pandas as pd


class VerificationError(ValueError):
    """Read-back content differs; destination was not replaced."""


def _text(value):
    if isinstance(value, str):
        return value
    return "" if value is None or pd.isna(value) else str(value)


def _write(path, fmt, table):
    if fmt != "xlsx":
        with open(path, "w", encoding="utf-8", newline="") as out:
            csv.writer(out, delimiter="," if fmt == "csv" else "\t").writerows(table)
        return
    from openpyxl import Workbook
    wb = Workbook()
    try:
        ws = wb.active
        for ri, row in enumerate(table, 1):
            for ci, value in enumerate(row, 1):
                ws.cell(row=ri, column=ci, value=value).data_type = "s"
        wb.save(path)
        _preserve_cr(path)
    finally:
        wb.close()



def _preserve_cr(path):
    # ElementTree may emit raw CR in text, which XML readers normalize to LF.
    # Numeric entities preserve CR without changing literal _x000D_ strings.
    from io import BytesIO
    from zipfile import ZipFile
    output = BytesIO()
    with ZipFile(path) as source, ZipFile(output, "w") as target:
        for info in source.infolist():
            data = source.read(info)
            if info.filename.startswith("xl/worksheets/") and info.filename.endswith(".xml"):
                data = data.replace(b"\r", b"&#13;")
            target.writestr(info, data)
    with open(path, "wb") as dest:
        dest.write(output.getvalue())

def _read(path, fmt):
    if fmt != "xlsx":
        with open(path, encoding="utf-8", newline="") as src:
            return list(csv.reader(src, delimiter="," if fmt == "csv" else "\t", strict=True))
    from openpyxl import load_workbook
    with open(path, "rb") as src:
        wb = load_workbook(src, data_only=False, read_only=True)
        try:
            return [[_text(v) for v in row] for row in wb.active.iter_rows(values_only=True)]
        finally:
            wb.close()


def _digest(table):
    payload = json.dumps(table, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def export_verified(frame, destination, fmt):
    """Return JSON-safe metadata only after verified atomic replacement.

    Raises on unsupported format, zero columns, invalid Excel content,
    mismatched read-back or I/O failure. Existing destination survives any
    failure before os.replace; temporary files are removed in finally.
    Normalization, full read-back, hashing and XLSX rewriting use additional
    memory proportional to the table/file; this is not a streaming export.
    Text fidelity only: original Python/pandas types are NOT preserved.
    """
    fmt = str(fmt).lower().lstrip(".")
    fmt = {"excel": "xlsx"}.get(fmt, fmt)
    if fmt not in ("csv", "txt", "xlsx"):
        raise ValueError("Supported formats: csv, txt, xlsx (excel)")
    headers = [_text(c) for c in frame.columns]
    if not headers:
        raise ValueError("Cannot export zero columns")
    rows = [[_text(v) for v in row] for row in frame.itertuples(index=False, name=None)]
    table = [headers] + rows
    if fmt == "xlsx" and (len(table) > 1048576 or len(headers) > 16384):
        raise ValueError("XLSX dimensions exceed Excel limits")
    dest = Path(destination)
    fd, tmp = tempfile.mkstemp(prefix="." + dest.name + ".", suffix=".tmp", dir=dest.parent)
    os.close(fd)
    try:
        _write(tmp, fmt, table)
        with open(tmp, "r+b") as src:
            src.flush()
            os.fsync(src.fileno())
        if _read(tmp, fmt) != table:
            raise VerificationError("Full read-back mismatch: replacement refused")
        with open(tmp, "rb") as src:
            checksum = hashlib.sha256(src.read()).hexdigest()
        report = dict(status="verified", rows=len(rows), columns=len(headers),
                      column_names=headers, sha256=checksum, content_sha256=_digest(table),
                      encoding_policy="text-fidelity/v1; UTF-8 CSV/TXT; XLSX literal strings; missing=empty; all numbers=text",
                      format=fmt, content_digest_schema="compact-json-table/v1")
        os.replace(tmp, dest)
        return report
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
