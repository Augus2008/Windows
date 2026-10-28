"""Real chooser/button/export regressions, driven under xvfb."""
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from PIL import ImageTk
from app import App
from batch_io import load_selection
from window_theme import BrandedToplevel

class ExportChoiceTests(unittest.TestCase):
    def setUp(self):
        self.a=App(); self.a.update()
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.path=self.root/'input.csv'
        self.path.write_text('name,value\nalpha,1\nbeta,2\n')
        self.a.commit_import(load_selection([self.path], {'text':App.load_text,'.log':App.load_log,'.trc':App.load_trc}))
        self.a.update()
    def tearDown(self):
        if self.a is not None: self.a.destroy()
        self.tmp.cleanup()
    def open(self):
        self.a.export_btn.invoke(); self.a.update()
        return self.a.export_format_window
    def test_bilingual_open_and_repeated_single_window(self):
        a=self.a
        for lang in ('zh','en'):
            a.lang=lang; a.apply_language(); w=self.open()
            self.assertIs(w,a.open_export_format())
            self.assertIs(a.grab_current(),w)
            self.assertEqual(w.title(),a.tr('export_choose'))
            self.assertEqual(len(a.export_format_buttons),3)
            for fmt,ext in (('Excel','.xlsx'),('CSV','.csv'),('TXT','.txt')):
                button=a.export_format_buttons[fmt]
                self.assertIn(f'{fmt} ({ext})',button.cget('text'))
                self.assertEqual(button.cget('anchor'),'center')
                self.assertIn(a.tr('export_hint_'+fmt.lower()),button.cget('text'))
                self.assertEqual(a.export_format_descriptions[fmt],a.tr('export_hint_'+fmt.lower()))
            self.assertEqual(sum(isinstance(c,BrandedToplevel) for c in a.winfo_children()),1)
            self.assertEqual((w.winfo_width(),w.winfo_height()),(440,270))
            self.assertEqual(w.resizable(),(0,0))
            self.assertEqual(a.export_format_heading.grid_info()['sticky'],'w')
            self.assertEqual(a.export_format_hint.grid_info()['sticky'],'w')
            self.assertEqual(a.export_format_cancel.grid_info()['sticky'],'e')
            a.close_export_format(); self.assertIsNone(a.grab_current())
    def test_all_formats_real_write_and_metadata(self):
        a=self.a
        for lang in ('zh','en'):
            a.lang=lang; a.apply_language()
            for fmt,ext in (('Excel','.xlsx'),('CSV','.csv'),('TXT','.txt')):
                dest=self.root/(lang+fmt+ext); w=self.open()
                def save(**kwargs):
                    self.assertFalse(w.winfo_exists())
                    self.assertIsNone(a.grab_current())
                    self.assertEqual(kwargs['defaultextension'],ext)
                    return str(dest)
                before=a.result.copy()
                with patch('audit_ui.filedialog.asksaveasfilename',side_effect=save) as dialog, patch('audit_ui.messagebox.showinfo') as info:
                    a.export_format_buttons[fmt].invoke()
                dialog.assert_called_once(); info.assert_called_once()
                self.assertTrue(dest.exists()); self.assertEqual(a.fmt.get(),fmt)
                pd.testing.assert_frame_equal(before,a.result)
                meta=a.audit.exports[-1]
                self.assertEqual(meta['status'],'verified')
                self.assertEqual(meta['path'],str(dest.resolve()))
                self.assertEqual(len(meta['content_sha256']),64)
                self.assertEqual(len(meta['result_records']),len(a.result))
                if fmt=='Excel': out=pd.read_excel(dest,dtype=str,keep_default_na=False)
                else: out=pd.read_csv(dest,sep=',' if fmt=='CSV' else '\t',dtype=str,keep_default_na=False)
                self.assertEqual(list(out.columns),list(a.data().columns))
                self.assertEqual(out.astype(str).values.tolist(),a.data().astype(str).values.tolist())
                self.assertEqual(a.verification_label.cget('text'),a.tr('wb_verified'))
    def test_cancel_button_escape_and_window_close_are_read_only(self):
        a=self.a; a.fmt.set('TXT')
        before=deepcopy(a.audit.__dict__); result=a.result.copy()
        with patch('audit_ui.filedialog.asksaveasfilename') as save:
            for action in ('button','escape','x'):
                w=self.open()
                if action=='button': a.export_format_cancel.invoke()
                elif action=='escape':
                    w.focus_force(); a.update(); w.event_generate('<Escape>'); a.update()
                else: a.tk.call(w.protocol('WM_DELETE_WINDOW'))
                self.assertIsNone(a.export_format_window)
                self.assertIsNone(a.grab_current())
                self.assertEqual(a.fmt.get(),'TXT')
                self.assertEqual(a.audit.__dict__,before)
                pd.testing.assert_frame_equal(a.result,result)
            save.assert_not_called()
        self.assertEqual(list(self.root.iterdir()),[self.path])
    def test_no_data_has_disabled_button_and_safe_direct_api(self):
        a=self.a; a.clear_all_data(False); a.update()
        self.assertEqual(a.export_btn.cget('state'),'disabled')
        with patch('export_ui.messagebox.showinfo') as info, patch('audit_ui.filedialog.asksaveasfilename') as save:
            self.assertIsNone(a.open_export_format()); info.assert_called_once(); save.assert_not_called()
        self.assertIsNone(a.export_format_window)
    def test_cancel_save_preserves_result_audit_and_new_format(self):
        a=self.a; before=deepcopy(a.audit.__dict__); result=a.result.copy()
        self.open()
        with patch('audit_ui.filedialog.asksaveasfilename',return_value='') as save, patch('audit_ui.messagebox.showinfo') as info:
            a.export_format_buttons['CSV'].invoke()
        save.assert_called_once(); info.assert_not_called()
        self.assertEqual(a.fmt.get(),'CSV')
        self.assertIsNone(a.export_format_window); self.assertIsNone(a.grab_current())
        self.assertEqual(a.audit.__dict__,before); pd.testing.assert_frame_equal(a.result,result)
        self.assertEqual(list(self.root.iterdir()),[self.path])
    def test_branded_icon_and_external_destroy_cleanup(self):
        a=self.a; w=self.open()
        self.assertIsInstance(w,BrandedToplevel)
        self.assertTrue(w._iconbitmap_method_called)
        self.assertEqual([i.width() for i in w._application_icon_images],[16,32,48,64,128])
        self.assertEqual(ImageTk.getimage(w._application_icon_images[2]).tobytes(),ImageTk.getimage(a._application_icon_images[2]).tobytes())
        w.destroy(); a.update()
        self.assertIsNone(a.export_format_window); self.assertIsNone(a.grab_current())
    def test_busy_or_existing_modal_is_not_stolen(self):
        a=self.a; a._import_busy=True
        self.assertIsNone(a.open_export_format())
        a._import_busy=False
        w=BrandedToplevel(a); w.wait_visibility(); w.grab_set()
        self.assertIsNone(a.open_export_format()); self.assertIs(a.grab_current(),w)
        w.destroy()

    def test_parent_destroy_releases_and_destroys_open_chooser(self):
        a=self.a; w=self.open()
        with patch.object(w,'grab_release',wraps=w.grab_release) as release, patch.object(w,'destroy',wraps=w.destroy) as destroy:
            a.destroy(); self.a=None
        release.assert_called_once(); destroy.assert_called_once()
        self.assertIsNone(a.export_format_window)

    def test_chooser_button_refuses_input_path(self):
        a=self.a; before=deepcopy(a.audit.__dict__); data=self.path.read_bytes()
        result=a.result.copy(); self.open()
        with patch('audit_ui.filedialog.asksaveasfilename',return_value=str(self.path)) as save, patch('audit_ui.messagebox.showerror') as error:
            a.export_format_buttons['CSV'].invoke()
        save.assert_called_once(); error.assert_called_once()
        self.assertIn(a.tr('audit_source_refused'),error.call_args.args[1])
        self.assertEqual(self.path.read_bytes(),data)
        self.assertEqual(a.audit.__dict__,before)
        pd.testing.assert_frame_equal(a.result,result)
        self.assertIsNone(a.export_format_window); self.assertIsNone(a.grab_current())
        self.assertEqual(a.verification_label.cget('text'),a.tr('wb_not_exported'))

    def test_internal_canvas_hover_has_no_callback_error(self):
        a=self.a; errors=[]
        a.report_callback_exception=lambda t,e,b: errors.append(str(e))
        self.open()
        for button in a.export_format_buttons.values():
            for event in ('<Enter>','<Leave>'):
                button._canvas.event_generate(event); a.update()
                self.assertEqual(button.cget('anchor'),'center')
        self.assertEqual(errors,[])
        self.assertEqual(len(a.result),2)
        self.assertEqual(len(a.audit.exports),0)

if __name__=='__main__': unittest.main()
