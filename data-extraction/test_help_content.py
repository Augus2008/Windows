import unittest
from help_content import HELP_SECTIONS as S, help_text

class HelpTests(unittest.TestCase):
 def test_structure(self):
  ids=[[x[0] for x in S[l]] for l in ('zh','en')]
  self.assertEqual(ids[0],ids[1]); self.assertEqual(len(set(ids[0])),11)
  for sections in S.values():
   for row in sections:
    self.assertEqual(len(row),3)
    for s in row:self.assertIsInstance(s,str);self.assertTrue(s.strip())
 def test_render(self):
  old=repr(S)
  for l in S:self.assertEqual(help_text(l),'\n\n'.join(t+'\n'+b for _,t,b in S[l]))
  self.assertEqual(repr(S),old)
  for l in ('fr','',None):
   with self.assertRaises(ValueError):help_text(l)
 def test_limits(self):
  for l in S:
   for token in ('500','AND','OR','JSON','CSV','values','percent'):
    self.assertIn(token,help_text(l))
 def test_contracts(self):
  required={'zh':['首表','物理行号','区分大小写','点击应用','来源文件参与','手动保存','不覆盖','当时','线性','字面','路径','关于”菜单','软件信息'], 'en':['first sheet','physical line','case-sensitive','click Apply','Source file','manually','failure','at export time','linear','literal','paths','About includes','Software information']}
  for lang,tokens in required.items():
   for token in tokens:self.assertIn(token,help_text(lang))

 def test_full_chart_contract(self):
  zh=dict((i,b) for i,t,b in S['zh'])['chart']
  en=dict((i,b) for i,t,b in S['en'])['chart']
  self.assertIn('全部记录',zh);self.assertIn('不抽样、不截断',zh)
  self.assertIn('every current-result record',en)
  self.assertIn('without sampling or truncation',en)
  for text in (zh,en):self.assertNotIn('5000',text)

if __name__=='__main__':unittest.main()
