from tkinter import messagebox
from i18n import TEXT

def tr(self, key, **kwargs):
    return TEXT[self.lang][key].format(**kwargs)

def show_about(self):
    messagebox.showinfo(self.tr("about_title"), self.tr("about_body", version=self.app_version, date=self.build_date))

def language_action(self, choice):
    if choice not in ("中文","English"):return
    self.lang = "en" if choice == "English" else "zh"
    self.apply_language()
def apply_language(self):
    t = TEXT[self.lang]
    self.title(f"{t['app_name']} v{self.app_version}")
    self.import_btn.configure(text=t["import_auto"])
    self.source_label.configure(text=t["source"])
    self.export_label.configure(text=t["export_format"])
    self.export_btn.configure(text=t["export"])
    self.about_btn.configure(text=t["about"])
    self.language_menu.configure(values=[t["language_menu"],"中文","English"]);self.language_menu.set(t["language_menu"])
    self.advanced_label.configure(text=t["advanced"])
    self.add_btn.configure(text=t["add"])
    self.clear_btn.configure(text=t["clear"])
    self.quick_entry.configure(placeholder_text=t["quick"])
    self.search_btn.configure(text=t["search"])
    self.dedupe_btn.configure(text=t["dedupe"])
    self.reextract_btn.configure(text=t["reextract"])
    self.restore_btn.configure(text=t["restore"])
    self.clear_all_btn.configure(text=t["clear_all"])
    self.preview_label.configure(text=t["preview"])
    current = self.logic.get()
    is_all = current in (TEXT["zh"]["all"], TEXT["en"]["all"])
    self.logic.configure(values=[t["all"], t["any"]])
    self.logic.set(t["all"] if is_all else t["any"])
    self.colmenu.configure(values=[t["columns"], t["choose_columns"], t["show_all"]])
    self.colmenu.set(t["columns"])
    for _,_,op,val in self.conditions:
        current_op=op.get()
        idx=next((TEXT[x]["ops"].index(current_op) for x in TEXT if current_op in TEXT[x]["ops"]),0)
        op.configure(values=t["ops"]);op.set(t["ops"][idx])
        val.configure(placeholder_text=t["condition_value"])
    self.refresh_localized_state()

def refresh_localized_state(self):
    t = TEXT[self.lang]
    if self.path is None:
        self.file.configure(text=t["supported"])
        self.sheet.configure(values=[t["source_empty"]])
        self.sheet.set(t["source_empty"])
        self.status.configure(text=t["header"])
        self.meta.configure(text=t["files"])
    else:
        self.file.configure(text=t["imported"].format(name=self.path.name))
        ext = self.path.suffix.lower()
        keys = {".trc":"source_trc", ".log":"source_log", ".csv":"source_csv", ".txt":"source_txt"}
        if ext in keys:
            value = t[keys[ext]]
            self.sheet.configure(values=[value])
            self.sheet.set(value)
        self.meta.configure(text=t["summary"].format(name=self.path.name, source=len(self.source), result=len(self.result)))
        if list(self.result.columns)==["values","percent"]:
            self.status.configure(text=t["auto_ok"].format(n=len(self.result)))
        else:
            self.status.configure(text=t["auto_none"])
    self.refresh()
