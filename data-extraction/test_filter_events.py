"""Native menu selection must mark pending without applying data changes."""
import unittest,tempfile,json
from pathlib import Path
from copy import deepcopy
import pandas as pd
from app import App
from batch_io import load_selection
from i18n import TEXT
class FilterEventTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.a=App();self.a.update()
        p=Path(self.tmp.name)/'data.csv'
        pd.DataFrame({'x':['1','2'],'other':['2','1']}).to_csv(p,index=False)
        self.a.commit_import(load_selection([p],{'text':App.load_text,'.log':App.load_log,'.trc':App.load_trc}))
    def tearDown(self):
        self.a.destroy();self.tmp.cleanup()
    def prepare(self,lang):
        a=self.a;a.reset();a.language_action('English' if lang=='en' else '中文')
        a.logic.set(TEXT[lang]['all'])
        a.add_condition();_,c,o,v=a.conditions[0];c.set('x');o.set(TEXT[lang]['ops'][0]);v.insert(0,'1');a.apply();a.update()
        self.assertEqual(a.pending_label.cget('text'),a.tr('wb_applied'))
        return c,o,v
    def choose(self,combo,index):
        # Invoke native Tk menu, which dispatches the real CTk selection callback.
        combo._dropdown_menu.invoke(index)
    def assert_pending_no_commit(self,old,ledger):
        a=self.a
        self.assertEqual(a.pending_label.cget('text'),a.tr('wb_pending'))
        pd.testing.assert_frame_equal(a.result,old)
        self.assertEqual(a.audit.__dict__,ledger)
    def test_operator_native_menu_marks_pending(self):
        a=self.a
        for lang in ('zh','en'):
            c,o,v=self.prepare(lang);old=a.result.copy();ledger=deepcopy(a.audit.__dict__)
            self.choose(o,1);self.assert_pending_no_commit(old,ledger)
            a.apply();self.assertEqual(a.result['x'].astype(str).tolist(),['2'])
            self.assertEqual(a.pending_label.cget('text'),a.tr('wb_applied'))
    def test_column_native_menu_marks_pending(self):
        a=self.a
        for lang in ('zh','en'):
            c,o,v=self.prepare(lang);old=a.result.copy();ledger=deepcopy(a.audit.__dict__)
            self.choose(c,c.cget('values').index('other'));self.assert_pending_no_commit(old,ledger)
            a.apply();self.assertEqual(a.result['other'].astype(str).tolist(),['1'])
            self.assertEqual(a.pending_label.cget('text'),a.tr('wb_applied'))
    def test_logic_button_marks_pending_without_apply(self):
        a=self.a
        for lang in ('zh','en'):
            self.prepare(lang);old=a.result.copy();ledger=deepcopy(a.audit.__dict__)
            a.logic._buttons_dict[TEXT[lang]['any']].invoke()
            self.assert_pending_no_commit(old,ledger)
            a.apply();self.assertEqual(a.pending_label.cget('text'),a.tr('wb_applied'))
if __name__=='__main__':unittest.main(verbosity=2)
