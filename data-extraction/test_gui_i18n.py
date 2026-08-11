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
assert "bold" in str(app.export_btn.cget("font")).lower()
assert app.language_popup is None
app.show_language_menu();app.update_idletasks();app.update()
assert app.language_popup is not None and app.language_popup.winfo_exists()
language_options=app.language_option_buttons
assert len(language_options)==2
assert "✓" in language_options[0].cget("text") and "English" in language_options[1].cget("text")
assert app.language_popup.winfo_width()==app.language_btn.winfo_width()
assert app.language_popup.winfo_y()+app.language_popup.winfo_height()<=app.language_btn.winfo_rooty()
language_options[1].invoke();app.update_idletasks();app.update()
assert app.language_popup is None and app.lang=="en"
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
with patch("i18n_runtime.messagebox.showinfo") as info:
    app.show_about();body=info.call_args.args[1]
    assert APP_VERSION in body and BUILD_DATE in body and "木头人" in body
    assert "编译日期" not in body and "Build date" not in body and "ehisuy" not in body
app.destroy();print("GUI_COMPACT_LANGUAGE_UNIQUE_COLORS_OK")
