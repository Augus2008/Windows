from unittest.mock import patch
import pandas as pd
from app import App, APP_VERSION, BUILD_DATE
from i18n import TEXT
app=App();app.update_idletasks();app.update()
assert not hasattr(app,"language") and not hasattr(app,"language_label")
assert app.language_menu.get()==TEXT["zh"]["language_menu"]
app.language_action("English");app.update_idletasks();app.update()
assert app.title().startswith(TEXT["en"]["app_name"])
assert app.language_menu.get()==TEXT["en"]["language_menu"]
assert app.import_btn.cget("text")==TEXT["en"]["import_auto"]
app.source=pd.DataFrame({"values":["4184mV"],"percent":["100%"]});app.result=app.source.copy();app.path=__import__("pathlib").Path("sample.trc");app.visible={"values":True,"percent":True};app.refresh()
app.clear_all_data(confirm=False);app.update_idletasks();app.update()
assert app.path is None and app.source is None and app.result is None and app.visible=={}
assert not app.tree.get_children() and app.tree["columns"]==()
assert app.sheet.get()==TEXT["en"]["source_empty"]
assert app.status.cget("text")==TEXT["en"]["header"]
assert app.clear_all_btn.cget("fg_color")=="#dc2626"
app.language_action("中文");app.update_idletasks();app.update();assert app.language_menu.get()==TEXT["zh"]["language_menu"]
with patch("i18n_runtime.messagebox.showinfo") as info:
 app.show_about();assert APP_VERSION in info.call_args.args[1] and BUILD_DATE in info.call_args.args[1]
app.destroy();print("GUI_LANGUAGE_MENU_CLEAR_OK")
