"""Real Tk audit integration tests; run with xvfb-run -a."""
import json, tempfile, unittest, threading
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from app import App
from audit_ui import report
from audit_ledger import save_report
from batch_io import load_selection, ImportCancelled
PARSERS={'text':App.load_text,'.log':App.load_log,'.trc':App.load_trc}

class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=App(); cls.app.withdraw()
    @classmethod
    def tearDownClass(cls):cls.app.destroy()
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name).resolve()
        self.app.clear_all_data(False); self.app.lang='zh'; self.app.apply_language()
    def tearDown(self):self.tmp.cleanup()
    def csv(self,name,**data):
        p=self.root/name; pd.DataFrame(data).to_csv(p,index=False); return p
    def commit(self,*paths):self.app.commit_import(load_selection(paths,PARSERS))
    def test_manifest_empty_and_duplicates(self):
        a=self.csv('a.csv',x=[1]); b=self.csv('header.csv',y=[])
        c=self.root/'empty.log'; c.write_text('')
        self.commit(a,b,c,a)
        r=report(self.app)
        self.assertEqual(r['selection'],dict(input_count=4,unique_files=3,duplicate_selections=1))
        self.assertEqual([f['read_rows'] for f in r['files']],[1,0,0])
        self.assertTrue(r['totals']['consistent'])
        self.assertEqual(len(r['files'][0]['sha256']),64)
        self.assertEqual(self.app.source['y'].tolist(),[''])
        self.assertEqual(r['result_records'],[dict(file_id='file_1',record_number=1)])
    def test_collision_dedupe_reset(self):
        a=self.csv('a.csv',x=[7,7],来源记录=['user','user'])
        b=self.csv('b.csv',x=[7],来源记录=['user'])
        self.commit(a,b)
        self.assertEqual(self.app.source_record_column,'来源记录_2')
        with patch('app.messagebox.showinfo'):self.app.dedupe()
        self.assertEqual(len(self.app.result),2)
        stage=self.app.audit.history[-1]
        self.assertEqual((stage['input_basis'],stage['base'],stage['after']),('result',3,2))
        self.assertEqual(stage['per_file_removed'],{'file_1':1})
        self.app.quick.set('1');self.app.reset()
        self.assertEqual(self.app.audit.history[-1]['filters'],{})
        self.assertEqual(self.app.audit.history[-1]['controls_snapshot_not_applied']['quick'],'1')
        self.assertEqual(len(self.app.result),3)
        self.assertEqual(self.app.audit.history[-1]['input_basis'],'source')
    def test_apply_recomputes_and_pending(self):
        self.commit(self.csv('a.csv',x=[1,2,3]))
        self.app.quick.set('1');self.app.apply()
        self.app.quick.set('3');self.app.apply()
        s=self.app.audit.history[-1]
        self.assertEqual((s['before'],s['base'],s['after']),(1,3,1))
        self.assertEqual((s['removed_from_previous'],s['added_to_previous']),(1,1))
        self.app.quick.set('not applied')
        r=report(self.app)
        self.assertEqual(r['history'][-1]['filters']['quick'],'3')
        self.assertEqual(r['pending_controls_not_applied']['quick'],'not applied')
        self.assertEqual(r['result_records'][0]['record_number'],3)
    def test_extract_and_raw(self):
        a=self.root/'raw.log'; a.write_text('unmatched\nvalues=10 percent=20\nvalues=30\n')
        b=self.csv('b.csv',other=['x'])
        self.commit(a,b)
        self.assertEqual(len(self.app.source),4)
        self.assertEqual(self.app.source['原始行'].iloc[0],'unmatched')
        self.app.extract_primary(True)
        self.assertEqual(len(self.app.result),1)
        self.assertIn(self.app.source_record_column,self.app.result)
        self.assertEqual(report(self.app)['totals']['excluded'],3)
        self.app.reset(); self.assertEqual(len(self.app.result),4)
        self.commit(b)
        self.assertFalse(self.app.extract_primary(True))
        self.assertEqual(len(self.app.audit.history),1)
    def test_failed_apply_and_reset_rollback(self):
        self.commit(self.csv('a.csv',x=[1,2]))
        self.app.add_condition(); self.app.quick.set('1')
        old=self.app.result.copy(); history=list(self.app.audit.history)
        widget=self.app.conditions[0][0]; refresh=self.app.refresh
        for operation in (self.app.apply,self.app.reset):
            calls=[]
            def fail():
                calls.append(1)
                if len(calls)==1:raise RuntimeError('injected refresh')
                return refresh()
            with patch.object(self.app,'refresh',side_effect=fail), patch('app.messagebox.showerror'):
                operation()
            pd.testing.assert_frame_equal(self.app.result,old)
            self.assertEqual(self.app.audit.history,history)
            self.assertTrue(widget.winfo_exists())
    def test_cancel_and_commit_failure_preserve_audit(self):
        a=self.csv('a.csv',x=[1]); b=self.csv('b.csv',x=[2]); self.commit(a)
        original=self.app.audit; cancel=threading.Event();cancel.set()
        with self.assertRaises(ImportCancelled):load_selection([b],PARSERS,cancelled=cancel)
        self.assertIs(self.app.audit,original)
        refresh=self.app.refresh; calls=[]
        def fail():
            calls.append(1)
            if len(calls)==1:raise RuntimeError('commit')
            refresh()
        with patch.object(self.app,'refresh',side_effect=fail):
            with self.assertRaises(RuntimeError):self.commit(b)
        self.assertIs(self.app.audit,original)
        with self.assertRaises(ValueError):self.commit(self.root/'missing.csv')
        self.assertIs(self.app.audit,original)
    def test_sheet_and_bilingual_report(self):
        a=self.root/'s.xlsx'
        with pd.ExcelWriter(a) as w:
            pd.DataFrame({'x':[1,2]}).to_excel(w,sheet_name='First',index=False)
            pd.DataFrame({'x':[]}).to_excel(w,sheet_name='Empty',index=False)
        self.commit(a)
        self.assertEqual(self.app.audit.manifest[0]['worksheets_skipped'],['Empty'])
        self.app.change_sheet('Empty')
        self.assertEqual(self.app.audit.manifest[0]['worksheets_read'],['Empty'])
        self.assertEqual(report(self.app)['totals']['read_rows'],0)
        for language in ('English','中文'):
            self.app.language_action(language);window=self.app.open_audit()
            self.assertTrue(window.winfo_exists()); window.destroy()
        self.app.clear_all_data(False);self.assertIsNone(self.app.audit)
    def test_verified_export_metadata_and_empty(self):
        self.commit(self.csv('a.csv',x=list(range(601))))
        out=self.root/'out.csv'; self.app.fmt.set('CSV')
        with patch('app.filedialog.asksaveasfilename',return_value=str(out)), patch('app.messagebox.showinfo') as info:
            self.app.export()
        self.assertEqual(len(pd.read_csv(out)),601);info.assert_called_once()
        meta=self.app.audit.exports[-1]
        self.assertEqual((meta['status'],meta['rows'],meta['stage']),('verified',601,1))
        self.assertEqual(len(meta['content_sha256']),64)
        self.assertEqual(meta['column_names'],['x'])
        self.assertEqual(len(meta['result_identity']),64)
        self.assertEqual(meta['source_snapshots'][0]['sha256'],self.app.audit.manifest[0]['sha256'])
        self.app.quick.set('absent');self.app.apply()
        self.assertEqual(self.app.audit.exports[0]['rows'],601)
        self.assertEqual(self.app.audit.exports[0]['stage'],1)
        with patch('app.filedialog.asksaveasfilename',return_value=str(out)), patch('app.messagebox.showinfo'):
            self.app.export()
        self.assertEqual(self.app.audit.exports[-1]['rows'],0)
        self.assertEqual(self.app.audit.exports[-1]['stage'],2)
        self.assertEqual(len(meta['result_records']),601)
        self.assertEqual(meta['superseded_by'],2)
        self.assertIn('verified_at_utc',meta)
        self.assertEqual(len(pd.read_csv(out)),0)
        self.assertNotEqual(meta['result_identity'],self.app.audit.exports[-1]['result_identity'])
        self.app.visible={'x':False}
        self.assertEqual(report(self.app)['visible_columns'],[])
    def test_report_save_and_collisions(self):
        src=self.csv('a.csv',x=[1234567890123456789]);self.commit(src)
        dest=self.root/'audit.json'; data=report(self.app)
        save_report(data,dest,[src])
        self.assertEqual(json.loads(dest.read_text(encoding='utf-8'))['totals']['current_kept'],1)
        with self.assertRaises(FileExistsError):save_report(data,dest,[src])
        with self.assertRaises(ValueError):save_report(data,src,[src])
        with patch('app.filedialog.asksaveasfilename',return_value=str(src)),patch('app.messagebox.showerror') as err:
            self.app.export()
        err.assert_called_once();self.assertEqual(len(self.app.audit.exports),0)
        self.assertEqual(self.app.source['x'].iloc[0],1234567890123456789)

    def test_large_hidden_lineage_report(self):
        self.commit(self.csv('a.csv',x=list(range(601))),self.csv('b.csv',x=[900]))
        self.app.visible={self.app.source_file_column:False,self.app.source_record_column:False}
        r=report(self.app)
        self.assertEqual(r['totals']['current_kept'],602)
        self.assertEqual(len(r['result_records']),602)
        self.assertEqual(r['result_records'][-1],dict(file_id='file_2',record_number=1))
        out=self.root/'hidden.csv';self.app.fmt.set('CSV')
        with patch('app.filedialog.asksaveasfilename',return_value=str(out)),patch('app.messagebox.showinfo'):
            self.app.export()
        self.assertEqual(self.app.audit.exports[-1]['rows'],602)
        self.assertEqual(self.app.audit.exports[-1]['column_names'],['x'])
    def test_snapshot_save_and_changed_source(self):
        from audit_ui import save
        a=self.csv('a.csv',x=[1]);self.commit(a);snapshot=report(self.app)
        with patch('batch_io.snapshot',side_effect=[{'sha256':'before'},{'sha256':'after'}]):
            with self.assertRaisesRegex(ValueError,'changed'):load_selection([a],PARSERS)
        self.app.clear_all_data(False);out=self.root/'captured.json'
        with patch('app.filedialog.asksaveasfilename',return_value=str(out)),patch('app.messagebox.showinfo'):
            save(self.app,snapshot)
        self.assertEqual(json.loads(out.read_text(encoding='utf-8'))['totals']['current_kept'],1)
        invalid=self.root/'invalid.json'
        with self.assertRaises(ValueError):save_report({'bad':float('nan')},invalid)
        self.assertFalse(invalid.exists())

if __name__=='__main__':unittest.main(verbosity=2)
