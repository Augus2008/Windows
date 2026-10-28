"""Real CTk/ttk layout and state regressions; requires a display (xvfb)."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from app import App
from batch_io import load_selection
from i18n import TEXT
PARSERS={'text':App.load_text,'.log':App.load_log,'.trc':App.load_trc}

class WorkbenchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=App()
    @classmethod
    def tearDownClass(cls):cls.app.destroy()
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.app.clear_all_data(False); self.app.lang='zh'; self.app.apply_language()
        self.app.show_filter_panel(False); self.app.geometry('1360x820'); self.pump()
    def tearDown(self):self.tmp.cleanup()
    def pump(self):
        # Windows window-manager geometry and CTk DPI callbacks are asynchronous.
        import tkinter as tk
        settled=tk.BooleanVar(self.app,value=False)
        self.app.after(150,lambda:settled.set(True))
        self.app.wait_variable(settled)
        self.app.update_idletasks();self.app.update()
    def csv(self,filename,**data):
        p=self.root/filename; pd.DataFrame(data).to_csv(p,index=False); return p
    def commit(self,*paths):
        self.app.commit_import(load_selection(paths,PARSERS)); self.pump()
    def text(self,widget):return widget.cget('text')
    def test_empty_clear_and_locales(self):
        a=self.app
        from tkinter import font
        self.assertIn(a.ui_font,font.families(a))
        if '文泉驿正黑' in font.families(a):self.assertEqual(a.ui_font,'文泉驿正黑')
        for lang in ('zh','en'):
            a.lang=lang; a.apply_language(); self.pump()
            self.assertEqual(self.text(a.import_btn),TEXT[lang]['wb_import'])
            self.assertEqual(self.text(a.search_caption),TEXT[lang]['wb_search_hint'])
            self.assertIn(TEXT[lang]['wb_preview'],a.title())
            self.assertEqual(self.text(a.empty_label),TEXT[lang]['wb_empty'])
            self.assertTrue(a.empty_state.winfo_ismapped())
            self.assertEqual(self.text(a.verification_label),TEXT[lang]['wb_unverified'])
            self.assertEqual(self.text(a.pending_label),TEXT[lang]['wb_ready'])
            self.assertEqual(a.export_btn.cget('state'),'disabled')
        self.commit(self.csv('sample.csv',channel=['CH-01','CH-02']))
        a.add_condition(); a.clear_all_data(False); self.pump()
        self.assertIsNone(a.audit); self.assertEqual(a.source_file_items,[])
        self.assertEqual([self.text(v) for v in a.stat_values],['0','0','0'])
        self.assertFalse(a.filter_panel_open); self.assertTrue(a.empty_state.winfo_ismapped())
        self.assertFalse(a.tree.get_children())
        self.assertEqual(set(TEXT['zh']),set(TEXT['en']))
        self.assertFalse(a.status.winfo_ismapped())
        self.assertFalse(a.meta.winfo_ismapped())
        self.assertFalse(hasattr(a,'export_label'))

    def test_manifest_includes_zero_rows_and_replaces(self):
        a=self.app
        self.commit(self.csv('read.csv',x=[1,2]),self.csv('zero.csv',x=[]))
        self.assertEqual(len(a.source_file_items),2)
        self.assertIn('zero.csv',self.text(a.source_file_items[1]))
        self.assertIn('0',self.text(a.source_file_items[1]))
        self.assertEqual([self.text(v) for v in a.stat_values],['2','2','2'])
        from copy import deepcopy
        before=deepcopy(a.audit.__dict__); source=a.source.copy(); result=a.result.copy()
        a.refresh_workbench()
        self.assertEqual(a.audit.__dict__,before)
        pd.testing.assert_frame_equal(a.source,source); pd.testing.assert_frame_equal(a.result,result)
        a.language_action('English')
        self.assertIn('Read',self.text(a.source_file_items[1]))
        self.commit(self.csv('replacement.csv',x=[9]))
        self.assertEqual(len(a.source_file_items),1)
        self.assertNotIn('zero.csv',self.text(a.source_file_items[0]))
        self.assertEqual(self.text(a.stat_values[0]),'1')

    def test_sheet_switch_and_manifest_hint(self):
        p=self.root/'sheets.xlsx'
        with pd.ExcelWriter(p) as w:
            pd.DataFrame({'x':[1]}).to_excel(w,sheet_name='First',index=False)
            pd.DataFrame({'x':[]}).to_excel(w,sheet_name='Empty',index=False)
        self.commit(p); a=self.app
        self.assertIn('First',self.text(a.source_file_items[0]))
        self.assertIn(a.tr('wb_skipped',n=1),self.text(a.source_file_items[0]))
        a.change_sheet('Empty'); self.pump()
        self.assertIn('Empty',self.text(a.source_file_items[0]))
        self.assertEqual(self.text(a.stat_values[1]),'0')
    def assert_inside(self,widget):
        self.assertTrue(widget.winfo_ismapped(),str(widget))
        a=self.app
        x=widget.winfo_rootx()-a.winfo_rootx(); y=widget.winfo_rooty()-a.winfo_rooty()
        self.assertGreaterEqual(x,0); self.assertGreaterEqual(y,0)
        self.assertLessEqual(x+widget.winfo_width(),a.winfo_width())
        self.assertLessEqual(y+widget.winfo_height(),a.winfo_height())

    def test_layout_minimum_and_table_area_both_locales(self):
        a=self.app
        self.assertEqual(tuple(map(int,a.tk.call('wm','minsize',a._w))),(1080,680))
        for geometry in ('1360x820','1080x680'):
            for lang in ('zh','en'):
                a.geometry(geometry); a.lang=lang; a.apply_language(); self.pump()
                self.assertGreater(a.table_panel.winfo_height()/a.winfo_height(),.40)
                self.assertGreater(a.tree.winfo_width(),600)
                for b in (a.export_btn,a.filter_toggle,a.search_btn,a.dedupe_btn,a.reextract_btn,a.restore_btn,a.colmenu,a.chart_btn,a.audit_btn,a.clear_all_btn):self.assert_inside(b)

    def test_many_filters_bounded_and_expand_collapse(self):
        self.commit(self.csv('many.csv',x=[1,2,3])); a=self.app
        a.geometry('1080x680')
        for _ in range(20):a.add_condition()
        self.pump(); self.assertTrue(a.filter_panel_open)
        self.assertLessEqual(a.filter_panel.winfo_height(),160)
        self.assertGreater(a.tree.winfo_height(),100)
        self.assert_inside(a.add_btn); self.assert_inside(a.clear_btn)
        a.toggle_filter_panel(); self.pump(); self.assertFalse(a.filter_panel.winfo_ismapped())
        a.show_filter_panel(); self.pump(); self.assertTrue(a.filter_panel.winfo_ismapped())
        self.assertEqual(len(a.conditions),20)
        a.language_action('English'); self.pump(); self.assert_inside(a.logic)
        for widget in a.conditions[0][1:]:self.assert_inside(widget)
        a.geometry('1360x820'); self.pump()
        print('LAYOUT_DIAGNOSTIC',dict(window=(a.winfo_width(),a.winfo_height()),screen=(a.winfo_screenwidth(),a.winfo_screenheight()),panel=a.filter_panel.winfo_height(),table=a.table_panel.winfo_height(),tree=a.tree.winfo_height()),flush=True)
        # Windows hosted runner is 1024x768 and clamps the requested 820px
        # window to its work area. Preserve the full-size 250px requirement,
        # subtracting only the measured missing client height on small screens.
        self.assertGreaterEqual(a.winfo_height(),680)
        required=max(100,250-max(0,820-a.winfo_height()))
        self.assertGreaterEqual(a.tree.winfo_height(),required)
        self.assertLessEqual(a.filter_panel.winfo_height(),160)
        for widget in (a.export_btn,a.audit_btn,a.add_btn,a.clear_btn):
            self.assert_inside(widget)
    def test_pending_normalized_and_actual_filter(self):
        self.commit(self.csv('channels.csv',channel=['CH-01','CH-02'])); a=self.app
        self.assertEqual(self.text(a.pending_label),a.tr('wb_ready'))
        a.quick.set('CH-01'); self.pump()
        self.assertEqual(len(a.result),2)
        self.assertEqual(self.text(a.pending_label),a.tr('wb_pending'))
        a.apply(); self.pump(); self.assertEqual(len(a.result),1)
        self.assertEqual([self.text(v) for v in a.stat_values],['1','2','1'])
        self.assertEqual(self.text(a.pending_label),a.tr('wb_applied'))
        a.add_condition(); _,c,o,v=a.conditions[0]
        c.set('channel'); o.set(TEXT['zh']['ops'][2]); v.insert(0,'CH-01')
        a.apply(); a.language_action('English'); self.pump()
        self.assertEqual(self.text(a.pending_label),a.tr('wb_applied'))
        v.delete(0,'end'); v.insert(0,'CH-02'); a.refresh_pending()
        self.assertEqual(self.text(a.pending_label),a.tr('wb_pending'))
        a.reset(); self.pump()
        self.assertEqual(self.text(a.pending_label),a.tr('wb_ready'))
        self.assertEqual(len(a.result),2)
        a.quick.set('absent'); a.apply(); self.pump()
        self.assertEqual(len(a.result),0)
        self.assertEqual(self.text(a.empty_label),a.tr('wb_no_results'))
        self.assertTrue(a.empty_state.winfo_ismapped())

    def test_striping_numeric_alignment_and_500_limit(self):
        self.commit(self.csv('types.csv',device_id=['001','002'],temperature=[21.5,22.5]),self.csv('other.csv',device_id=['003'],temperature=[23.5]))
        a=self.app; children=a.tree.get_children()
        self.assertEqual(a.tree.item(children[0],'tags'),('even',))
        self.assertEqual(a.tree.item(children[1],'tags'),('odd',))
        cols=list(a.data().columns)
        for c in (a.source_file_column,a.source_record_column,'device_id'):
            self.assertEqual(str(a.tree.column(f'data_col_{cols.index(c)}','anchor')),'w')
        self.assertEqual(str(a.tree.column(f'data_col_{cols.index("temperature")}','anchor')),'e')
        self.commit(self.csv('long.csv',x=list(range(601))))
        self.assertEqual(len(a.tree.get_children()),500)
        self.assertEqual(self.text(a.stat_values[2]),'601')
        self.assertIn(a.tr('preview_limit'),self.text(a.rows))
        self.assertEqual(str(a.tree.column('data_col_0','anchor')),'e')

    def test_verification_current_content_and_export_refresh(self):
        self.commit(self.csv('data.csv',x=[1,2],name=['a','b'])); a=self.app
        self.assertEqual(self.text(a.verification_label),a.tr('wb_not_exported'))
        out=self.root/'out.csv'; a.fmt.set('CSV')
        with patch('app.filedialog.asksaveasfilename',return_value=str(out)),patch('app.messagebox.showinfo'):
            a.export()
        self.pump()
        self.assertTrue(out.exists())
        self.assertEqual(self.text(a.verification_label),a.tr('wb_verified'))
        a.quick.set('a'); self.pump()
        self.assertEqual(self.text(a.verification_label),a.tr('wb_verified'))
        a.apply(); self.pump()
        self.assertEqual(self.text(a.verification_label),a.tr('wb_not_exported'))
        a.reset(); a.visible['name']=False; a.refresh()
        self.assertEqual(self.text(a.verification_label),a.tr('wb_not_exported'))
        a.visible['name']=True; a.refresh()
        self.assertEqual(self.text(a.verification_label),a.tr('wb_verified'))
        a.result.loc[a.result.index[0],'name']='changed'; a.refresh()
        self.assertEqual(self.text(a.verification_label),a.tr('wb_not_exported'))

    def test_titlebar_icon_without_sidebar_brand(self):
        a=self.app
        for lang in ('中文','English'):
            a.language_action(lang);a.update_idletasks();a.update()
            for n in ('brand_subtitle','brand_icon','brand_label','language_btn','about_btn'):
                self.assertFalse(hasattr(a,n))
            self.assertEqual(len(a._application_icon_images),5)
            self.assertTrue(a._iconbitmap_method_called)
            self.assertIn(a.tr('app_name'),a.title())
            self.assertLess(a.source_label.winfo_y(),40)

    def test_compact_preview_toolbar_order_and_centering(self):
        a=self.app
        for size in ('1360x820','1080x680'):
            for lang in ('zh','en'):
                a.geometry(size);a.lang=lang;a.apply_language();self.pump()
                for w in (a.preview_label,a.audit_btn,a.chart_btn,a.export_btn,a.help_btn):self.assert_inside(w)
                self.assertEqual(str(a.cget('menu')),'')
                self.assertLessEqual(a.stat_labels[0].master.winfo_rooty()-a.winfo_rooty(),16)
                group=a.preview_actions;bar=a.preview_toolbar
                self.assertLessEqual(abs(group.winfo_x()+group.winfo_width()/2-bar.winfo_width()/2),2)
                self.assertLessEqual(a.preview_label.winfo_rootx()+a.preview_label.winfo_width(),a.audit_btn.winfo_rootx())
                self.assertLessEqual(a.audit_btn.winfo_rootx()+a.audit_btn.winfo_width(),a.chart_btn.winfo_rootx())
                self.assertLessEqual(a.chart_btn.winfo_rootx()+a.chart_btn.winfo_width(),a.export_btn.winfo_rootx())
                self.assertGreater(a.help_btn.winfo_rooty(),a.clear_all_btn.winfo_rooty())
                self.assertLessEqual(abs(a.help_btn.winfo_rooty()+a.help_btn.winfo_height()-a.winfo_rooty()-a.winfo_height()),14)

if __name__=='__main__':unittest.main()
