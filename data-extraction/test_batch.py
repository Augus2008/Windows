"""Batch I/O + real Tk GUI regression (use xvfb-run on Linux)."""
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import pandas as pd
from app import App
from batch_io import load_selection, ImportCancelled
from i18n import TEXT

PARSERS = {'text': App.load_text, '.log': App.load_log, '.trc': App.load_trc}


class BatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = App()
        cls.app.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        # Windows TEMP may use an 8.3 short name; match loader canonicalization.
        self.root = Path(self.temp.name).resolve()
        self.app.clear_all_data(confirm=False)
        self.app.lang = 'zh'
        self.app.apply_language()

    def tearDown(self):
        self.temp.cleanup()

    def csv(self, name, data):
        path = self.root / name
        pd.DataFrame(data).to_csv(path, index=False, encoding='utf-8-sig')
        return path

    def selection(self, *paths):
        return load_selection(paths, PARSERS)

    def commit(self, *paths):
        self.app.commit_import(self.selection(*paths))

    def wait(self):
        deadline = time.monotonic() + 15
        while self.app._import_busy and time.monotonic() < deadline:
            self.app.update()
            time.sleep(.01)
        self.assertFalse(self.app._import_busy, 'Background import timed out')

    def test_align_columns_missing_blank_and_order(self):
        a = self.csv('a.csv', {'name': ['a'], 'value': [1]})
        b = self.csv('b.csv', {'value': [2], 'extra': ['x']})
        result = self.selection(a, b)
        self.assertEqual(list(result['frame'].columns), ['来源文件', 'name', 'value', 'extra'])
        self.assertEqual(result['frame']['name'].tolist(), ['a', ''])
        self.assertEqual(result['frame']['value'].tolist(), [1, 2])

    def test_excel_first_sheet_only(self):
        a = self.root / 'a.xlsx'
        with pd.ExcelWriter(a) as writer:
            pd.DataFrame({'value': [10]}).to_excel(writer, sheet_name='First', index=False)
            pd.DataFrame({'value': [999]}).to_excel(writer, sheet_name='Second', index=False)
        b = self.csv('b.csv', {'value': [20]})
        result = self.selection(a, b)
        self.assertEqual(result['frame']['value'].tolist(), [10, 20])
        self.assertEqual(result['sheet_names'], ['First', 'Second'])

    def test_source_column_collision_and_duplicate_basenames(self):
        a = self.csv('a.csv', {'来源文件': ['user value'], '来源文件_2': ['also user'], 'x': [1]})
        sub = self.root / 'sub'
        sub.mkdir()
        b = sub / 'a.csv'
        pd.DataFrame({'x': [2]}).to_csv(b, index=False)
        result = self.selection(a, b)
        self.assertEqual(result['source_column'], '来源文件_3')
        self.assertEqual(result['frame']['来源文件_3'].tolist(), [str(a), str(b)])
        self.assertEqual(result['frame'].iloc[0]['来源文件'], 'user value')

    def test_duplicate_path_loaded_once(self):
        a = self.csv('a.csv', {'x': [1]})
        result = self.selection(a, a)
        self.assertEqual(len(result['paths']), 1)
        self.assertIsNone(result['source_column'])

    def test_log_trc_txt_and_csv_enrichment_without_lost_rows(self):
        log = self.root / 'a.log'
        log.write_text('values:4184mV percent:100%\nordinary message\n')
        trc = self.root / 'b.trc'
        trc.write_text('values=4183mV percent=99%\n')
        txt = self.root / 'c.txt'
        txt.write_text('values:4182mV percent:98%\n')
        csv = self.csv('d.csv', {'value': [7]})
        self.commit(log, trc, txt, csv)
        self.assertEqual(len(self.app.source), 5)
        self.assertEqual(len(self.app.result), 5)
        self.assertEqual(self.app.source['values'].tolist()[:4], ['4184mV', '', '4183mV', '4182mV'])
        self.app.extract_primary(silent=True)
        self.assertEqual(self.app.result['percent'].tolist(), ['100%', '99%', '98%'])
        self.assertIn('来源文件', self.app.result)
        self.app.reset()
        self.assertEqual(len(self.app.result), 5)

    def test_empty_files_and_headers(self):
        log = self.root / 'empty.log'
        log.write_text('')
        trc = self.root / 'empty.trc'
        trc.write_text('')
        csv = self.csv('a.csv', {'x': [1]})
        result = self.selection(log, trc, csv)
        self.assertEqual(len(result['frame']), 1)
        self.assertEqual(len(result['paths']), 3)

    def test_failure_names_file_and_does_not_change_existing_data(self):
        a = self.csv('old.csv', {'x': [1]})
        self.commit(a)
        previous = self.app.source.copy()
        broken = self.root / 'broken.xlsx'
        broken.write_text('this is not Excel')
        with patch('batch_ui.messagebox.showerror') as error:
            self.app.begin_import([a, broken])
            self.wait()
        pd.testing.assert_frame_equal(self.app.source, previous)
        self.assertEqual(self.app.path, a)
        self.assertIn('broken.xlsx', error.call_args.args[1])

    def test_cancel_no_partial_result(self):
        a = self.csv('a.csv', {'x': [1]})
        b = self.csv('b.csv', {'x': [2]})
        cancelled = threading.Event()
        with self.assertRaises(ImportCancelled):
            load_selection([a, b], PARSERS, lambda *args: cancelled.set(), cancelled)

    def test_cancel_dialog_does_not_clear_existing(self):
        a = self.csv('a.csv', {'x': [1]})
        self.commit(a)
        with patch('batch_ui.load_selection', side_effect=ImportCancelled):
            self.app.begin_import([a])
            self.wait()
        self.assertEqual(self.app.source['x'].tolist(), [1])

    def test_file_dialog_supports_multiple_and_async_commit(self):
        a = self.csv('a.csv', {'x': [1]})
        b = self.csv('b.csv', {'x': [2]})
        with patch('batch_ui.filedialog.askopenfilenames', return_value=(str(a), str(b))) as dialog:
            self.app.import_file()
            self.wait()
        dialog.assert_called_once()
        self.assertEqual(len(self.app.paths), 2)
        self.assertEqual(str(self.app.sheet.cget('state')), 'disabled')

    def test_numeric_and_or_and_source_filter(self):
        a = self.csv('a.csv', {'value': [10, 30]})
        b = self.csv('b.csv', {'value': [40], 'other': ['y']})
        self.commit(a, b)
        self.app.add_condition()
        _, column, operator, entry = self.app.conditions[0]
        column.set('value'); operator.set('大于'); entry.insert(0, '20')
        self.app.apply()
        self.assertEqual(self.app.result['value'].tolist(), [30, 40])
        self.app.add_condition()
        _, column, operator, entry = self.app.conditions[1]
        column.set('来源文件'); operator.set('等于'); entry.insert(0, 'b.csv')
        self.app.apply()
        self.assertEqual(self.app.result['value'].tolist(), [40])
        self.app.logic.set(TEXT['zh']['any'])
        self.app.apply()
        self.assertEqual(self.app.result['value'].tolist(), [30, 40])

    def test_language_clear_and_single_excel_sheet_switch(self):
        a = self.root / 'a.xlsx'
        with pd.ExcelWriter(a) as writer:
            pd.DataFrame({'x': [1]}).to_excel(writer, sheet_name='First', index=False)
            pd.DataFrame({'x': [2]}).to_excel(writer, sheet_name='Second', index=False)
        b = self.csv('b.csv', {'x': [3]})
        self.commit(a, b)
        self.app.language_action('English')
        self.assertIn('Merged 2 files', self.app.file.cget('text'))
        self.assertIn('来源文件', self.app.result)
        self.app.clear_all_data(confirm=False)
        self.assertEqual(self.app.paths, [])
        self.assertIsNone(self.app.source_file_column)
        self.assertEqual(str(self.app.sheet.cget('state')), 'readonly')
        self.commit(a)
        self.app.change_sheet('Second')
        self.assertEqual(self.app.source['x'].tolist(), [2])

    def test_all_rows_exported_to_one_file_all_formats(self):
        a = self.csv('a.csv', {'value': list(range(601))})
        b = self.csv('b.csv', {'value': [900]})
        self.commit(a, b)
        self.assertEqual(len(self.app.tree.get_children()), 500)
        for fmt, suffix in [('CSV', '.csv'), ('TXT', '.txt'), ('Excel', '.xlsx')]:
            out = self.root / ('combined' + suffix)
            self.app.fmt.set(fmt)
            with patch('app.filedialog.asksaveasfilename', return_value=str(out)), patch('app.messagebox.showinfo'):
                self.app.export()
            data = pd.read_excel(out) if suffix == '.xlsx' else pd.read_csv(out, sep='\t' if suffix == '.txt' else ',')
            self.assertEqual(len(data), 602)
            self.assertEqual(data['来源文件'].iloc[-1], 'b.csv')
        self.app.quick.set('900')
        self.app.apply()
        out = self.root / 'filtered.csv'
        self.app.fmt.set('CSV')
        with patch('app.filedialog.asksaveasfilename', return_value=str(out)), patch('app.messagebox.showinfo'):
            self.app.export()
        self.assertEqual(pd.read_csv(out)['value'].tolist(), [900])


    def test_missing_columns_preserve_integer_precision_and_equality(self):
        number = 1234567890123456789
        a = self.csv('a.csv', {'id': [number], 'small': [1]})
        b = self.csv('b.csv', {'other': ['x']})
        self.commit(a, b)
        self.assertEqual(self.app.source['id'].iloc[0], number)
        self.assertEqual(str(self.app.source['small'].iloc[0]), '1')
        self.app.add_condition()
        _, col, op, entry = self.app.conditions[0]
        col.set('small'); op.set('等于'); entry.insert(0, '1')
        self.app.apply()
        self.assertEqual(len(self.app.result), 1)
        out = self.root / 'exact.csv'
        self.app.fmt.set('CSV')
        with patch('app.filedialog.asksaveasfilename', return_value=str(out)), patch('app.messagebox.showinfo'):
            self.app.export()
        data = pd.read_csv(out, dtype=str, keep_default_na=False)
        self.assertEqual(data['id'].iloc[0], str(number))
        self.assertEqual(data['small'].iloc[0], '1')

    def test_special_column_names_are_headers_not_tk_column_ids(self):
        a = self.csv('a.csv', {'#999': [1], '1': [2], 'col_0': [3]})
        b = self.csv('b.csv', {'#999': [4]})
        self.commit(a, b)
        headings = [self.app.tree.heading(c, 'text') for c in self.app.tree['columns']]
        self.assertEqual(headings, ['来源文件', '#999', '1', 'col_0'])
        self.assertEqual(len(self.app.tree.get_children()), 2)

    def test_ui_commit_failure_restores_models_filters_and_preview(self):
        a = self.csv('old.csv', {'x': [1, 2]})
        b = self.csv('new.csv', {'x': [99]})
        self.commit(a)
        self.app.add_condition()
        _, col, op, entry = self.app.conditions[0]
        col.set('x'); op.set('等于'); entry.insert(0, '2')
        self.app.quick.set('2')
        self.app.logic.set(TEXT['zh']['any'])
        self.app.apply()
        previous = self.app.source.copy()
        result = self.app.result.copy()
        condition = self.app.conditions[0]
        refresh = self.app.refresh
        calls = []
        def fail_once():
            calls.append(1)
            if len(calls) == 1:
                refresh()  # Fail after the new preview has already replaced the old view.
                raise RuntimeError('Injected view commit failure')
            return refresh()
        with patch.object(self.app, 'refresh', side_effect=fail_once), patch('batch_ui.messagebox.showerror') as error:
            self.app.begin_import([b])
            self.wait()
        error.assert_called_once()
        pd.testing.assert_frame_equal(self.app.source, previous)
        pd.testing.assert_frame_equal(self.app.result, result)
        self.assertEqual(self.app.path, a)
        self.assertIs(self.app.conditions[0], condition)
        self.assertTrue(condition[0].winfo_exists())
        self.assertEqual(entry.get(), '2')
        self.assertEqual(self.app.quick.get(), '2')
        self.assertEqual(self.app.logic.get(), TEXT['zh']['any'])
        self.assertEqual(len(self.app.tree.get_children()), 1)


    def test_real_xls_first_sheet(self):
        import importlib.util
        if not importlib.util.find_spec('xlrd'):
            self.skipTest('xlrd is required for XLS')
        xls = Path(__file__).parent / 'testdata' / 'two-sheets.xls'
        csv = self.csv('b.csv', {'value': [20]})
        self.commit(xls, csv)
        self.assertEqual(self.app.source['value'].tolist(), [10, 20])
        self.assertEqual(self.app.source['来源文件'].tolist(), ['two-sheets.xls', 'b.csv'])


    def test_mixed_integer_float_column_preserves_exact_id(self):
        number = 1234567890123456789
        a = self.csv('a.csv', {'id': [number]})
        b = self.csv('b.csv', {'id': [1.5]})
        self.commit(a, b)
        self.assertEqual(str(self.app.source['id'].iloc[0]), str(number))
        self.assertEqual(self.app.source['id'].iloc[1], 1.5)
        out = self.root / 'mixed.csv'
        self.app.data().to_csv(out, index=False)
        self.assertEqual(pd.read_csv(out, dtype=str)['id'].iloc[0], str(number))


if __name__ == '__main__':
    unittest.main(verbosity=2)
