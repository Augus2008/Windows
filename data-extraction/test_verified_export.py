"""Run with python -B -m unittest -v test_verified_export."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd
import verified_export as ve
from openpyxl.utils.exceptions import IllegalCharacterError


class VerifiedExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.dest = self.root / "special.destination"
        self.dest.write_bytes(b"OLD")
        self.frame = pd.DataFrame({"=header": ["00123", "NA", "null", "nan", None, float("nan"), 1234567890123456789, "=1+1", "+SUM(A1)", "-1", "@cmd", "中文😀\n\t\"", ""], "第二列": ["x"] * 13}, dtype=object)

    def unchanged(self):
        self.assertEqual(self.dest.read_bytes(), b"OLD")
        self.assertEqual(list(self.root.iterdir()), [self.dest])

    def test_round_trip_and_metadata(self):
        digests = []
        expected = [str(v) if v is not None and not isinstance(v, float) else "" for v in self.frame.iloc[:, 0]]
        for fmt in ("csv", "txt", "xlsx"):
            with self.subTest(fmt=fmt):
                report = ve.export_verified(self.frame, self.dest, fmt)
                table = ve._read(self.dest, fmt)
                self.assertEqual([r[0] for r in table[1:]], expected)
                self.assertEqual(table[0], ["=header", "第二列"])
                self.assertEqual((report["rows"], report["columns"]), (13, 2))
                self.assertEqual(report["status"], "verified")
                self.assertEqual(report["column_names"], table[0])
                self.assertEqual(report["sha256"], hashlib.sha256(self.dest.read_bytes()).hexdigest())
                payload = json.dumps(table, ensure_ascii=False, separators=(",", ":"))
                self.assertEqual(report["content_sha256"], hashlib.sha256(payload.encode()).hexdigest())
                json.dumps(report, allow_nan=False)
                digests.append(report["content_sha256"])
        self.assertEqual(len(set(digests)), 1)

    def test_zero_rows_and_empty_cells(self):
        for fmt in ("csv", "txt", "xlsx"):
            for frame in (self.frame.iloc[:0], pd.DataFrame([[None, ""]], columns=["a", "b"])):
                report = ve.export_verified(frame, self.dest, fmt)
                self.assertEqual(report["rows"], len(frame))

    def test_corrupt_content_refused(self):
        original = ve._write
        changes = [lambda t: [t[0]] + t[:0:-1], lambda t: t[:-1],
                   lambda t: [t[0][::-1]] + t[1:],
                   lambda t: t[:1] + [["changed"] + t[1][1:]] + t[2:]]
        for fmt in ("csv", "txt", "xlsx"):
            for change in changes:
                def corrupt(path, kind, table):
                    original(path, kind, change(table))
                with self.subTest(fmt=fmt), patch.object(ve, "_write", side_effect=corrupt):
                    with self.assertRaises(ve.VerificationError):
                        ve.export_verified(self.frame, self.dest, fmt)
                self.unchanged()

    def test_failures_preserve_destination(self):
        for target in ("_write", "_read"):
            with patch.object(ve, target, side_effect=OSError("injected")):
                with self.assertRaises(OSError):
                    ve.export_verified(self.frame, self.dest, "csv")
            self.unchanged()
        with patch.object(ve.os, "replace", side_effect=PermissionError("injected")):
            with self.assertRaises(PermissionError):
                ve.export_verified(self.frame, self.dest, "csv")
        self.unchanged()

    def test_excel_refuses_truncation_and_illegal_characters(self):
        for value in ("x" * 32768, "bad\x00text"):
            with self.subTest(length=len(value)):
                with self.assertRaises((ve.VerificationError, IllegalCharacterError)):
                    ve.export_verified(pd.DataFrame({"a": [value]}), self.dest, "xlsx")
                self.unchanged()

    def test_zero_columns_and_bad_format(self):
        for frame, fmt in ((pd.DataFrame(), "csv"), (self.frame, "xls")):
            with self.assertRaises(ValueError):
                ve.export_verified(frame, self.dest, fmt)
            self.unchanged()

    def test_excel_has_no_formulas(self):
        from openpyxl import load_workbook
        ve.export_verified(self.frame, self.dest, "excel")
        with self.dest.open("rb") as src:
            wb = load_workbook(src, data_only=False, read_only=True)
            try:
                for row in wb.active:
                    for cell in row:
                        self.assertNotEqual(cell.data_type, "f")
                self.assertEqual(wb.active["A8"].value, "1234567890123456789")
            finally:
                wb.close()


    def test_missing_duplicate_headers_and_crlf(self):
        frame = pd.DataFrame([[pd.NA, pd.NaT], ["a\r\nb,\"c", "00001"]], columns=["dup", "dup"], dtype=object)
        for fmt in ("csv", "txt", "xlsx"):
            ve.export_verified(frame, self.dest, fmt)
            self.assertEqual(ve._read(self.dest, fmt), [["dup", "dup"], ["", ""], ["a\r\nb,\"c", "00001"]])



    def test_partial_write_and_missing_destination(self):
        def fail(path, fmt, table):
            Path(path).write_bytes(b"PARTIAL")
            raise OSError("injected partial write")
        for existing in (True, False):
            if not existing:
                self.dest.unlink()
            with patch.object(ve, "_write", side_effect=fail):
                with self.assertRaises(OSError):
                    ve.export_verified(self.frame, self.dest, "csv")
            if existing:
                self.unchanged()
            else:
                self.assertEqual(list(self.root.iterdir()), [])


    def test_excel_2000_rows_smoke(self):
        frame = pd.DataFrame({"id": [f"{i:06}" for i in range(2000)], "value": ["=1+1"] * 2000})
        report = ve.export_verified(frame, self.dest, "xlsx")
        self.assertEqual(report["rows"], 2000)
        self.assertEqual(ve._read(self.dest, "xlsx")[-1], ["001999", "=1+1"])
        self.assertEqual(list(self.root.iterdir()), [self.dest])

    def test_fsync_failure_preserves_destination(self):
        with patch.object(ve.os, "fsync", side_effect=OSError("injected fsync")):
            with self.assertRaises(OSError):
                ve.export_verified(self.frame, self.dest, "xlsx")
        self.unchanged()


    def test_excel_cr_and_literal_escape_sequences(self):
        frame = pd.DataFrame({"h\r\n": ["a\rb", "_x000D_", "_x005F_", "\r\n", "&<>\r"]})
        ve.export_verified(frame, self.dest, "xlsx")
        self.assertEqual(ve._read(self.dest, "xlsx"), [["h\r\n"], ["a\rb"], ["_x000D_"], ["_x005F_"], ["\r\n"], ["&<>\r"]])

    def test_simulated_windows_xml_newlines(self):
        from zipfile import ZipFile
        from io import BytesIO
        restore = ve._preserve_cr
        def translate(path, table):
            buf = BytesIO()
            with ZipFile(path) as source, ZipFile(buf, 'w') as target:
                for info in source.infolist():
                    data = source.read(info)
                    if info.filename.startswith('xl/worksheets/'):
                        data = data.replace(b'\n', b'\r\n')
                    target.writestr(info, data)
            Path(path).write_bytes(buf.getvalue())
            restore(path, table)
        with patch.object(ve, '_preserve_cr', side_effect=translate):
            ve.export_verified(self.frame, self.dest, 'xlsx')

if __name__ == "__main__":
    unittest.main()
