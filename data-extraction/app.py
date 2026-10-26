import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import csv, re
import pandas as pd
import customtkinter as ctk
from i18n import TEXT
from i18n_runtime import tr, show_about, language_action, apply_language, refresh_localized_state
from chart_dialog import open_chart_dialog
from batch_ui import BatchImportMixin
from batch_io import enrich_fields
from workbench_ui import WorkbenchMixin

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")
PREVIEW_ROWS = 500
OPS = ["包含", "不包含", "等于", "不等于", "开头是", "结尾是", "大于", "小于", "非空", "为空"]
APP_NAME = "数据提取工具"
APP_VERSION = "0.15.1"
BUILD_DATE = "2026-10-26"
LEFT_ALIGNED_COLUMNS = {"日志内容", "文本内容", "原始行"}

class App(WorkbenchMixin, BatchImportMixin, ctk.CTk):
    tr = tr
    show_about = show_about
    language_action = language_action
    apply_language = apply_language
    refresh_localized_state = refresh_localized_state
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1360x820"); self.minsize(1080, 680)
        self.audit = None; self.source_record_column = None; self.paths = []; self.source_file_column = None; self.source = self.result = None; self.path = None; self.conditions = []; self.visible = {}; self.lang = "zh"; self.language_option_buttons = []; self.chart_settings = None; self.app_version = APP_VERSION; self.build_date = BUILD_DATE
        self._style(); self._ui(); self.apply_language()
        self.bind("<Button-1>", self.close_language_menu_on_outside_click, add="+")
        self.bind("<Escape>", lambda _e:self.close_language_menu(), add="+")

    def show_language_menu(self):
        if self.language_popup is not None and self.language_popup.winfo_exists():
            self.close_language_menu()
            return
        self.update_idletasks()
        width = self.language_btn.winfo_width()
        height = 92
        x = self.language_btn.winfo_rootx()
        y = self.language_btn.winfo_rooty() - height - 6
        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg="#F5F7FA")
        popup.geometry(f"{width}x{height}+{x}+{y}")
        self.language_popup = popup
        self.language_option_buttons = []
        panel = ctk.CTkFrame(popup, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E3E8F0")
        panel.pack(fill="both", expand=True)
        for code, label, choice in (("zh", "中文", "中文"), ("en", "English", "English")):
            selected = self.lang == code
            button = ctk.CTkButton(panel, text=("✓  " if selected else "    ") + label, height=38, corner_radius=7, anchor="w", fg_color="#DBEAFE" if selected else "transparent", hover_color="#EDF1F7", text_color="#172B4D", font=(self.ui_font, 12, "bold" if selected else "normal"), command=lambda c=choice:self.select_language(c))
            self.language_option_buttons.append(button)
            button.pack(fill="x", padx=6, pady=(6,0) if code == "zh" else (2,6))
        popup.bind("<Escape>", lambda _e:self.close_language_menu())


    def close_language_menu_on_outside_click(self, event):
        popup = self.language_popup
        if popup is None or not popup.winfo_exists(): return
        x, y = event.x_root, event.y_root
        inside_popup = popup.winfo_rootx() <= x < popup.winfo_rootx()+popup.winfo_width() and popup.winfo_rooty() <= y < popup.winfo_rooty()+popup.winfo_height()
        inside_button = self.language_btn.winfo_rootx() <= x < self.language_btn.winfo_rootx()+self.language_btn.winfo_width() and self.language_btn.winfo_rooty() <= y < self.language_btn.winfo_rooty()+self.language_btn.winfo_height()
        if not inside_popup and not inside_button: self.close_language_menu()

    def select_language(self, choice):
        self.language_action(choice)
        self.close_language_menu()

    def close_language_menu(self):
        popup = self.language_popup
        if popup is not None:
            try:
                if popup.winfo_exists(): popup.destroy()
            except tk.TclError:
                pass
        self.language_popup = None
        self.language_option_buttons = []


    def load_text(self,p):
        lines=None
        for enc in ("utf-8-sig","utf-8","gb18030","gbk","latin1"):
            try:
                with open(p,"r",encoding=enc) as f:lines=f.read().splitlines()
                break
            except UnicodeDecodeError:continue
        if lines is None:raise ValueError("无法识别文件编码")
        sample="\n".join(lines[:30])
        if Path(p).suffix.lower() == ".csv":
            try:
                separator=csv.Sniffer().sniff(sample,delimiters=",\t;|").delimiter
            except csv.Error:
                separator=","  # A one-column CSV is still a table, not raw text.
            try:
                self.source=pd.read_csv(p,encoding=enc,sep=separator,engine="python")
            except pd.errors.EmptyDataError:
                self.source=pd.DataFrame()
            self.loaded()
            return
        try:
            dialect=csv.Sniffer().sniff(sample,delimiters=",\t;|")
            self.source=pd.read_csv(p,encoding=enc,sep=dialect.delimiter,engine="python")
            if len(self.source.columns)==1:raise ValueError()
        except Exception:
            self.source=pd.DataFrame({"行号":range(1,len(lines)+1),"文本内容":lines})
        self.loaded()
    def load_trc(self,p):
        lines=None
        for enc in ("utf-8-sig","utf-8","gb18030","gbk","latin1"):
            try:
                with open(p,"r",encoding=enc) as f:lines=f.read().splitlines()
                break
            except UnicodeDecodeError:continue
        if lines is None:raise ValueError("无法识别 TRC 文件编码")
        rows=[]
        pat=re.compile(r"^\[(?P<time>\d{2}:\d{2}:\d{2}\.\d{3})\]\s+\[\s*(?P<counter>\d+)\]\s+\[\s*(?P<seq>\d+)\]\s+\[(?P<context>[^]]*)\]\s+\[(?P<task>[^]]*)\]\s+\[(?P<flag>[^]]*)\]\s*(?P<module>[^/ :]*?)\s*/(?P<level>[A-Za-z])\s*:\s*(?P<message>.*)$")
        for no,line in enumerate(lines,1):
            m=pat.match(line)
            if m:
                d=m.groupdict();msg=d["message"]
                row={"行号":no,"时间":d["time"],"计数器":d["counter"],"序号":d["seq"],"上下文":d["context"].strip(),"任务":d["task"].strip(),"标志":d["flag"].strip(),"模块":d["module"].strip(),"级别":d["level"].upper(),"日志内容":msg,"原始行":line}
            else:
                msg=line;row={"行号":no,"时间":"","计数器":"","序号":"","上下文":"","任务":"","标志":"","模块":"","级别":"RAW","日志内容":msg,"原始行":line}
            for key in ("status","values","percent","vol","user","width","height"):
                km=re.search(r"(?i)(?<![A-Za-z0-9_])"+key+r"\s*[:=]\s*([^\s,;]+)",msg)
                if km:row[key]=km.group(1)
            rows.append(row)
        self.source=pd.DataFrame(rows).fillna("")
        self.loaded()

    def load_log(self,p):
        text=None
        for enc in ("utf-8-sig","utf-8","gb18030","gbk","latin1"):
            try:
                with open(p,"r",encoding=enc) as f:text=f.read().splitlines()
                break
            except UnicodeDecodeError:continue
        rows=[]
        pat=re.compile(r"^\[(?P<datetime>\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})\](?:\[\s*(?P<runtime>\d+\.\d+)\])?\s*(?P<message>.*)$")
        for no,line in enumerate(text or [],1):
            m=pat.match(line);dt=m.group("datetime") if m else "";runtime=m.group("runtime") if m else "";msg=m.group("message") if m else line
            low=msg.lower()
            if re.search(r"panic|fatal|exception|\berr(?:or)?\b|fail(?:ed)?|not exist|timeout",low):level="ERROR"
            elif re.search(r"\bwarn(?:ing)?\b",low):level="WARN"
            elif re.search(r"\[\s*ok\s*\]",low):level="OK"
            else:level="INFO"
            module="";mm=re.match(r"([^ ]+\.(?:c|cpp|h):\d+):?",msg)
            if mm:module=mm.group(1)
            rows.append({"行号":no,"日期时间":dt.strip(),"运行时间(秒)":runtime,"级别":level,"模块/来源":module,"日志内容":msg,"原始行":line})
        self.source=pd.DataFrame(rows, columns=["行号","日期时间","运行时间(秒)","级别","模块/来源","日志内容","原始行"])
        for key in ("status","values","percent"):
            self.source[key]=self.source["日志内容"].str.extract(r"(?i)(?<![A-Za-z0-9_])"+key+r"\s*:\s*([^\s,;]+)",expand=False).fillna("")
        self.loaded()

    def change_sheet(self,name):
        if len(self.paths) <= 1 and self.path and self.path.suffix.lower() in (".xlsx",".xls"):self.load_sheet(name)
    def load_sheet(self,name):
        from batch_io import load_selection
        parsers={'text':type(self).load_text,'.log':type(self).load_log,'.trc':type(self).load_trc}
        self.commit_import(load_selection([self.path],parsers,sheet=name))
        self.sheet.set(name)
    def loaded(self):
        self.source.columns=[str(x) for x in self.source.columns]; self.result=self.source.copy(); self.visible={x:True for x in self.source.columns}; self.clear_conditions(); extracted=self.extract_primary(silent=True); self.meta.configure(text=self.tr("summary",name=self.path.name,source=len(self.source),result=len(self.result))); (not extracted) and (self.refresh() or self.status.configure(text=self.tr("auto_none")))
    def add_condition(self):
        if self.source is None or len(self.source.columns)==0: messagebox.showinfo(self.tr("info"),self.tr("no_file")); return
        self.show_filter_panel(True)
        r=ctk.CTkFrame(self.condbox,fg_color="#f4f7fb",corner_radius=8);r.pack(fill="x",pady=4)
        col=ctk.CTkComboBox(r,values=list(self.source.columns),width=190,command=self.refresh_pending);col.set(str(self.source.columns[0]));col.pack(side="left",padx=(8,5),pady=7)
        op=ctk.CTkComboBox(r,values=TEXT[self.lang]["ops"],width=150,command=self.refresh_pending);op.set(TEXT[self.lang]["ops"][0]);op.pack(side="left",padx=5,pady=7)
        val=ctk.CTkEntry(r,placeholder_text=self.tr("condition_value"),height=31);val.pack(side="left",fill="x",expand=True,padx=5,pady=7)
        ctk.CTkButton(r,text="×",width=32,height=31,fg_color="#EDF1F7",text_color="#B42332",hover_color="#DFE6F0",command=lambda:self.remove_condition(r)).pack(side="right",padx=(5,8),pady=7);self.conditions.append((r,col,op,val))
    def remove_condition(self,r):self.conditions=[x for x in self.conditions if x[0]!=r];r.destroy()
    def clear_conditions(self):
        for r,*_ in self.conditions:r.destroy()
        self.conditions=[];self.quick.set("")
    def test(self,s,op,v):
        t=s.fillna("").astype(str);v=v.strip();op=dict(zip(TEXT["en"]["ops"],TEXT["zh"]["ops"])).get(op,op)
        if op=="非空":return t.str.strip().ne("")
        if op=="为空":return t.str.strip().eq("")
        if op=="包含":return t.str.contains(re.escape(v),case=False,na=False)
        if op=="不包含":return ~t.str.contains(re.escape(v),case=False,na=False)
        if op=="等于":return t.str.lower().eq(v.lower())
        if op=="不等于":return ~t.str.lower().eq(v.lower())
        if op=="开头是":return t.str.startswith(v,na=False)
        if op=="结尾是":return t.str.endswith(v,na=False)
        n=pd.to_numeric(s,errors="coerce");q=pd.to_numeric(pd.Series([v]),errors="coerce").iloc[0]
        if pd.isna(q):raise ValueError(self.tr("numeric_error"))
        return n.gt(q) if op=="大于" else n.lt(q)
    def apply(self):
        if self.source is None:return
        try:
            ms=[];q=self.quick.get().strip()
            if q:ms.append(self.source.astype(str).apply(lambda z:z.str.contains(re.escape(q),case=False,na=False)).any(axis=1))
            for _,c,o,v in self.conditions:ms.append(self.test(self.source[c.get()],o.get(),v.get()))
            if ms:
                m=ms[0]
                for z in ms[1:]:m=(m&z) if self.logic.get() in (TEXT["zh"]["all"],TEXT["en"]["all"]) else (m|z)
                self.result=self.source[m].copy()
            else:self.result=self.source.copy()
            self.refresh()
        except Exception:raise
    def extract_primary(self,silent=False):
        if self.source is None:return False
        work=enrich_fields(self.source)
        if not {"values","percent"}.issubset(work.columns):
            if not silent:messagebox.showinfo(self.tr("info"),self.tr("no_fields"))
            return False
        mask=work["values"].fillna("").astype(str).str.strip().ne("") & work["percent"].fillna("").astype(str).str.strip().ne("")
        columns=([self.source_file_column] if self.source_file_column in work.columns else []) + ([self.source_record_column] if self.source_record_column in work.columns else []) + ["values","percent"]
        self.result=work.loc[mask,columns].copy()
        self.visible={c:True for c in columns};self.refresh()
        self.status.configure(text=self.tr("auto_ok",n=len(self.result)))
        if not silent and self.result.empty:messagebox.showinfo(self.tr("info"),self.tr("no_records"))
        return not self.result.empty

    def only_errors(self):
        if self.source is None:return
        if "级别" not in self.source.columns:messagebox.showinfo(self.tr("info"),self.tr("log_only"));return
        self.result=self.source[self.source["级别"].astype(str).str.upper().isin(["ERROR","WARN","E","W","F","FATAL"])].copy();self.refresh()
    def reset(self):
        if self.source is not None:self.result=self.source.copy();self.visible={c:True for c in self.source.columns};self.refresh()
    def clear_all_data(self, confirm=True):
        if self.path is None and self.source is None:
            return
        if confirm and not messagebox.askyesno(self.tr("confirm"), self.tr("confirm_clear")):
            return
        self.audit=None
        self.source_record_column=None
        self.paths=[]
        self.source_file_column=None
        self.chart_settings=None
        self.path=None
        self.source=None
        self.result=None
        self.visible={}
        self.clear_conditions()
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"]=()
        self.rows.configure(text=self.tr("rows",n=0))
        self.fmt.set("Excel")
        self.refresh_localized_state()
        self.show_filter_panel(False)

    def dedupe(self):
        if self.result is None:return
        n=len(self.result);self.result=self.result.drop_duplicates(subset=[c for c in self.result.columns if c!=self.source_record_column]).copy();self.refresh();messagebox.showinfo(self.tr("done"),self.tr("deduped",n=n-len(self.result)))
    def data(self):return self.result[[c for c in self.result.columns if self.visible.get(c,True)]] if self.result is not None else pd.DataFrame()
    def refresh(self):
        if self.result is None:
            self.refresh_workbench(); return
        if len(self.paths) > 1:
            self.meta.configure(text=self.tr("batch_summary", n=len(self.paths), source=len(self.source), result=len(self.result)))
        d=self.data();cols=list(d.columns);self.tree.delete(*self.tree.get_children());ids=[f"data_col_{i}" for i in range(len(cols))];self.tree["columns"]=ids
        for c,column_id in zip(cols,ids):
            anchor = "w" if c in LEFT_ALIGNED_COLUMNS else "center"
            self.tree.heading(column_id,text=c,anchor="center")
            self.tree.column(column_id,width=max(120,min(260,len(c)*16+80)),anchor=anchor)
        for _,r in d.head(PREVIEW_ROWS).iterrows():self.tree.insert("","end",values=["" if pd.isna(x) else str(x)[:500] for x in r])
        self.rows.configure(text=self.tr("rows",n=len(d))+(self.tr("preview_limit") if len(d)>PREVIEW_ROWS else ""))
        self.style_preview_rows()
        self.refresh_workbench()
    def column_action(self,choice):
        if choice in (TEXT["zh"]["choose_columns"],TEXT["en"]["choose_columns"]):self.columns()
        elif choice in (TEXT["zh"]["show_all"],TEXT["en"]["show_all"]) and self.result is not None:self.visible={c:True for c in self.result.columns};self.refresh()
        self.after(100,lambda:self.colmenu.set(self.tr("columns")))
    def selected_text(self):
        items=self.tree.selection()
        if not items and self.tree.focus():items=(self.tree.focus(),)
        return "\n".join("\t".join(map(str,self.tree.item(i,"values"))) for i in items)
    def copy_selection(self,event=None):
        text=self.selected_text()
        if text:self.clipboard_clear();self.clipboard_append(text);self.update()
        return "break"
    def copy_cell(self):
        item=getattr(self,"copy_item",None);col=getattr(self,"copy_col","")
        if not item or not col:return
        vals=self.tree.item(item,"values");idx=int(col[1:])-1
        if 0<=idx<len(vals):self.clipboard_clear();self.clipboard_append(str(vals[idx]));self.update()
    def popup_copy_menu(self,event):
        item=self.tree.identify_row(event.y);self.copy_col=self.tree.identify_column(event.x);self.copy_item=item
        if item:
            if item not in self.tree.selection():self.tree.selection_set(item)
            self.tree.focus(item)
        menu=tk.Menu(self,tearoff=0);menu.add_command(label=self.tr("copy_cell"),command=self.copy_cell);menu.add_command(label=self.tr("copy_rows"),command=self.copy_selection);menu.tk_popup(event.x_root,event.y_root)
    def columns(self):
        if self.result is None:return
        w=ctk.CTkToplevel(self);w.title(self.tr("select_columns_title"));w.geometry("430x560");w.transient(self);w.grab_set();ctk.CTkLabel(w,text=self.tr("select_columns"),font=("Microsoft YaHei UI",18,"bold")).pack(pady=(20,10));f=ctk.CTkScrollableFrame(w);f.pack(fill="both",expand=True,padx=20,pady=8);vs={}
        for c in self.result.columns:
            v=tk.BooleanVar(value=self.visible.get(c,True));vs[c]=v;ctk.CTkCheckBox(f,text=c,variable=v).pack(anchor="w",padx=10,pady=5)
        def save():
            if not any(v.get() for v in vs.values()):messagebox.showwarning(self.tr("info"),self.tr("at_least_one"));return
            self.visible={c:v.get() for c,v in vs.items()};self.refresh();w.destroy()
        ctk.CTkButton(w,text=self.tr("save_selection"),command=save,height=38).pack(pady=(5,20))
    def open_chart(self):
        open_chart_dialog(self, self.result.copy() if self.result is not None else None, self.lang, self.batch_label() if len(self.paths) > 1 else (self.path.name if self.path else ""), self.chart_settings)

    def export(self):
        from audit_ui import export
        return export(self)
from audit_ui import install
install(App)
from workbench_ui import refresh_after_action
for _action in ("apply","extract_primary","dedupe","reset","only_errors","export","clear_conditions","remove_condition","add_condition","commit_import"):
    setattr(App,_action,refresh_after_action(getattr(App,_action)))

if __name__=="__main__":App().mainloop()
