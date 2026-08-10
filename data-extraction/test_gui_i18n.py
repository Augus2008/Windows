from unittest.mock import patch
import pandas as pd
from app import App, APP_VERSION, BUILD_DATE
from i18n import TEXT
app=App();app.update_idletasks();app.update()
assert app.about_btn.cget("text")==TEXT["zh"]["about"]
assert app.language_label.cget("text")==TEXT["zh"]["language"]
assert app.import_btn.cget("text")==TEXT["zh"]["import_auto"]
with patch("i18n_runtime.messagebox.showinfo") as info:
    app.show_about();title,body=info.call_args.args
    assert APP_VERSION in body and BUILD_DATE in body and "Copyright 2026 ehisuy" in body
app.change_language("English");app.update_idletasks();app.update()
assert app.title().startswith(TEXT["en"]["app_name"])
assert app.about_btn.cget("text")=="About"
assert app.language_label.cget("text")=="Language"
assert app.import_btn.cget("text")==TEXT["en"]["import_auto"]
assert app.advanced_label.cget("text")==TEXT["en"]["advanced"]
assert app.colmenu.get()==TEXT["en"]["columns"]
series=pd.Series(["alpha","beta"])
assert app.test(series,"Contains","alpha").tolist()==[True,False]
app.change_language("中文");app.update_idletasks();app.update()
assert app.title().startswith(TEXT["zh"]["app_name"])
assert app.about_btn.cget("text")=="关于"
app.destroy();print("GUI_I18N_SWITCH_OK")
