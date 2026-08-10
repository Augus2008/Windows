from unittest.mock import patch
import pandas as pd
from pathlib import Path
from app import App, APP_VERSION, BUILD_DATE
from i18n import TEXT
app=App();app.update_idletasks();app.update()
assert not hasattr(app,"language_menu") and not hasattr(app,"language_label")
assert app.language_btn.cget("text")==TEXT["zh"]["language_menu"]
assert app.status.cget("text")==TEXT["zh"]["header_empty"]
assert app.language_btn.winfo_manager()=="pack"
assert app.language_btn.cget("fg_color")==app.about_btn.cget("fg_color")
assert app.language_btn.cget("hover_color")==app.about_btn.cget("hover_color")
assert int(app.language_btn.cget("height"))==int(app.about_btn.cget("height"))
assert app.export_btn.cget("text_color")=="#ffffff"
assert app.export_btn.cget("font").cget("weight")=="bold"
assert app.language_popup.index("end")==1
assert app.language_popup.entrycget(0,"label")=="中文"
assert app.language_popup.entrycget(1,"label")=="English"
app.language_action("English");app.update_idletasks();app.update()
assert app.language_btn.cget("text")==TEXT["en"]["language_menu"]
assert app.status.cget("text")==TEXT["en"]["header_empty"]
colors=[app.search_btn.cget("fg_color"),app.dedupe_btn.cget("fg_color"),app.reextract_btn.cget("fg_color"),app.restore_btn.cget("fg_color"),app.clear_all_btn.cget("fg_color"),app.colmenu.cget("fg_color")]
assert len(colors)==len(set(colors)),colors
app.source=pd.DataFrame({"values":["4184mV"],"percent":["100%"]});app.result=app.source.copy();app.path=Path("sample.trc");app.visible={"values":True,"percent":True};app.refresh()
assert str(app.tree.heading("values","anchor"))=="center"
assert str(app.tree.column("values","anchor"))=="center"
app.clear_all_data(confirm=False)
assert app.path is None and app.source is None and app.result is None and not app.tree.get_children()
assert app.status.cget("text")==TEXT["en"]["header_empty"]
app.language_action("中文");assert app.language_btn.cget("text")==TEXT["zh"]["language_menu"]
with patch("i18n_runtime.messagebox.showinfo") as info:app.show_about();assert APP_VERSION in info.call_args.args[1] and BUILD_DATE in info.call_args.args[1]
app.destroy();print("GUI_COMPACT_LANGUAGE_UNIQUE_COLORS_OK")
