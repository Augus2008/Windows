from unittest.mock import patch
import pandas as pd
from pathlib import Path
from app import App, APP_VERSION, BUILD_DATE
from i18n import TEXT
app=App();app.update_idletasks();app.update()
assert not hasattr(app,"language_btn") and not hasattr(app,"about_btn")
assert app.help_btn.cget("text")==TEXT["zh"]["about"]
assert app.status.cget("text")==TEXT["zh"]["header_empty"]
assert app.help_menu.entrycget(0,"label")==TEXT["zh"]["help_guide"]
assert app.help_menu.entrycget(1,"label")==TEXT["zh"]["language_menu"]
assert app.export_btn.cget("text_color")=="#ffffff"
assert "bold" in str(app.export_btn.cget("font")).lower()
app.help_language_menu.invoke(1);app.update()
assert app.lang=="en"
assert app.help_btn.cget("text")==TEXT["en"]["about"]
assert app.chart_btn.cget("text")==TEXT["en"]["chart_export"]
assert app.status.cget("text")==TEXT["en"]["header_empty"]
assert not app.status.winfo_ismapped() and not app.meta.winfo_ismapped()
colors=[app.search_btn.cget("fg_color"),app.dedupe_btn.cget("fg_color"),app.reextract_btn.cget("fg_color"),app.restore_btn.cget("fg_color"),app.clear_all_btn.cget("fg_color"),app.colmenu.cget("fg_color")]
assert len(set(colors))==1,colors
assert app.export_btn.cget("fg_color") not in colors
assert app.clear_all_btn.cget("text_color")=="#B42332"
assert all(b.winfo_ismapped() for b in (app.search_btn,app.dedupe_btn,app.reextract_btn,app.restore_btn,app.clear_all_btn,app.colmenu))
app.source=pd.DataFrame({"values":["4184mV"],"percent":["100%"]});app.result=app.source.copy();app.path=Path("sample.trc");app.visible={"values":True,"percent":True};app.refresh()
assert str(app.tree.heading("#1","anchor"))=="w"
assert str(app.tree.column("#1","anchor"))=="w"
app.clear_all_data(confirm=False)
assert app.path is None and app.source is None and app.result is None and not app.tree.get_children()
assert app.status.cget("text")==TEXT["en"]["header_empty"]
app.help_language_menu.invoke(0);assert app.lang=='zh'
app.help_menu.invoke(3);app.update()
assert app.about_window.winfo_exists()
body=app.about_body.cget('text')
assert APP_VERSION in body and BUILD_DATE in body and '木头人' in body
assert '编译日期' not in body and 'Build date' not in body and 'ehisuy' not in body
assert hasattr(app.about_window,'_application_icon_images')
app.about_close.invoke();app.destroy();print('GUI_HELP_LANGUAGE_ABOUT_ACTIONS_OK')
