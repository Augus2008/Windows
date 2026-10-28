import unittest,tempfile,time,threading
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import pandas as pd
from PIL import Image,ImageTk
from app import App
from batch_io import load_selection
from window_theme import BrandedToplevel
from help_content import help_text

class HelpUITests(unittest.TestCase):
    def setUp(self):
        self.a=App();self.a.update()
        self.tmp=tempfile.TemporaryDirectory();p=Path(self.tmp.name)/'a.csv'
        p.write_text('x\n1\n2\n');self.path=p
        self.a.commit_import(load_selection([p],{'text':App.load_text,'.log':App.load_log,'.trc':App.load_trc}))
    def tearDown(self):self.a.destroy();self.tmp.cleanup()
    def pump(self):
        a=self.a;done=threading.Event();a.after(260,done.set)
        while not done.is_set():a.update();time.sleep(.005)
    def icon(self,w):
        self.assertIsInstance(w,BrandedToplevel)
        self.assertTrue(w._iconbitmap_method_called)
        self.assertEqual([i.width() for i in w._application_icon_images],[16,32,48,64,128])
        with patch.object(w,'iconbitmap') as default:
            w._windows_set_titlebar_icon();default.assert_not_called()
        self.assertEqual(ImageTk.getimage(w._application_icon_images[2]).tobytes(),ImageTk.getimage(self.a._application_icon_images[2]).tobytes())
    def test_menu_language_about_and_guide_are_read_only(self):
        a=self.a;source=a.source.copy();result=a.result.copy();audit=deepcopy(a.audit.__dict__)
        a.help_menu.invoke(0);self.pump();w=a.help_window;self.icon(w)
        self.assertEqual(a.help_textbox.get('1.0','end').strip(),help_text('zh'))
        a.help_language_menu.invoke(1);self.pump()
        self.assertEqual(a.lang,'en');self.assertEqual(a.help_btn.cget('text'),'About')
        self.assertEqual(a.help_textbox.get('1.0','end').strip(),help_text('en'))
        self.assertEqual(a.help_menu.entrycget(3,'label'),a.tr('software_info'))
        a.help_menu.invoke(3);self.pump();self.icon(a.about_window)
        self.assertIn(a.app_version,a.about_body.cget('text'))
        a.help_language_menu.invoke(0);self.pump()
        self.assertEqual(a.about_window.title(),a.tr('about_title'))
        pd.testing.assert_frame_equal(a.source,source);pd.testing.assert_frame_equal(a.result,result)
        self.assertEqual(a.audit.__dict__,audit)
        a.help_close.invoke();a.open_usage();self.pump();self.icon(a.help_window)

    def test_source_at_top_stats_centered_and_bottom_help(self):
        a=self.a
        for size in ('1360x820','1080x680'):
            a.geometry(size);self.pump()
            self.assertLess(a.source_label.winfo_y(),40)
            self.assertEqual(str(a.cget('menu')),'')
            self.assertTrue(a.help_btn.winfo_ismapped())
            self.assertGreater(a.help_btn.winfo_rooty(),a.clear_all_btn.winfo_rooty())
            for w in a.stat_labels+a.stat_values:
                self.assertEqual(w.cget('anchor'),'center')
                self.assertEqual(w.cget('justify'),'center')
                self.assertLessEqual(abs(w.winfo_x()+w.winfo_width()/2-w.master.winfo_width()/2),2)
    def test_bottom_help_button_posts_upward_within_window(self):
        a=self.a
        for lang in ('zh','en'):
            a.lang=lang;a.apply_language();self.pump()
            import sys
            if sys.platform=='win32':
                # A native Windows popup can enter an OS modal loop. Check the
                # callback and coordinates here; X11 below exercises real post.
                with patch.object(a.help_menu,'tk_popup') as popup:
                    a.help_btn.invoke()
                popup.assert_called_once()
                x,y=popup.call_args.args
                self.assertEqual(x,a.help_btn.winfo_rootx())
                self.assertLessEqual(y,a.help_btn.winfo_rooty())
                continue
            a.help_btn.invoke();a.update()
            self.assertTrue(a.help_menu.winfo_ismapped())
            self.assertLess(a.help_menu.winfo_rooty(),a.help_btn.winfo_rooty())
            self.assertLessEqual(a.help_menu.winfo_rooty()+a.help_menu.winfo_height(),a.help_btn.winfo_rooty()+2)
            self.assertEqual(a.help_menu.entrycget(0,'label'),a.tr('help_guide'))
            a.help_menu.unpost()

    def test_columns_audit_and_chart_icons(self):
        a=self.a;a.columns();self.pump()
        column=next(w for w in a.winfo_children() if isinstance(w,BrandedToplevel))
        self.icon(column);column.destroy()
        audit=a.open_audit();self.pump();self.icon(audit);audit.destroy()
        from chart_dialog import ChartDialog
        chart=ChartDialog(a,pd.DataFrame({'values':['4184mV'],'percent':['100%']}))
        self.pump();self.icon(chart);chart.destroy()

    def test_progress_icon_during_real_async_import(self):
        a=self.a;gate=threading.Event()
        import batch_ui
        original=batch_ui.load_selection
        def blocked(*args,**kwargs):
            gate.wait(timeout=5);return original(*args,**kwargs)
        with patch('batch_ui.load_selection',side_effect=blocked):
            a.begin_import([self.path]);self.pump()
            w=next(w for w in a.winfo_children() if isinstance(w,BrandedToplevel))
            try:self.icon(w)
            finally:gate.set()
            end=time.monotonic()+10
            while getattr(a,'_import_busy',False) and time.monotonic()<end:
                a.update();time.sleep(.01)
            self.assertFalse(a._import_busy)

    def test_executable_icon_asset_matches_window_artwork(self):
        from window_theme import make_brand_image
        p=Path(__file__).parent/'assets'/'app.ico'
        with Image.open(p) as image:
            self.assertEqual(image.format,'ICO');self.assertIn((16,16),image.ico.sizes())
            self.assertEqual(image.convert('RGBA').tobytes(),make_brand_image().resize(image.size,Image.Resampling.LANCZOS).tobytes())
if __name__=='__main__':unittest.main()
