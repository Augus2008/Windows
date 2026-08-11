import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import csv, re
import pandas as pd
import customtkinter as ctk
from i18n import TEXT
from i18n_runtime import tr, show_about, language_action, apply_language, refresh_localized_state
from chart_dialog import open_chart_dialog

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")
PREVIEW_ROWS = 500
OPS = ["包含", "不包含", "等于", "不等于", "开头是", "结尾是", "大于", "小于", "非空", "为空"]
APP_NAME = "数据提取工具"
APP_VERSION = "0.12.2"
BUILD_DATE = "2026-08-11"
LEFT_ALIGNED_COLUMNS = {"日志内容", "文本内容", "原始行"}

class App(ctk.CTk):
    tr = tr
    show_about = show_about
    language_action = language_action
    apply_language = apply_language
    refresh_localized_state = refresh_localized_state
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1360x820"); self.minsize(1080, 680)
        self.source = self.result = None; self.path = None; self.conditions = []; self.visible = {}; self.lang = "zh"; self.language_option_buttons = []; self.chart_settings = None; self.app_version = APP_VERSION; self.build_date = BUILD_DATE
        self._style(); self._ui(); self.apply_language()
        self.bind("<Button-1>", self.close_language_menu_on_outside_click, add="+")
        self.bind("<Escape>", lambda _e:self.close_language_menu(), add="+")

    def _style(self):
        s = ttk.Style(); s.theme_use("clam")
        s.configure("Treeview", background="#fff", fieldbackground="#fff", foreground="#263238", rowheight=28, font=("Microsoft YaHei UI", 10))
        s.configure("Treeview.Heading", background="#e8f1ff", foreground="#1e3a5f", font=("Microsoft YaHei UI", 10, "bold"))
        s.map("Treeview", background=[("selected", "#2f80ed")], foreground=[("selected", "white")])

    def _ui(self):
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(1, weight=1)
        side = ctk.CTkFrame(self, width=285, corner_radius=0, fg_color="#12314a"); side.grid(row=0,column=0,rowspan=2,sticky="nsew"); side.grid_propagate(False)
        self.import_btn=ctk.CTkButton(side,text="＋  导入并自动提取",height=44,command=self.import_file,font=("Microsoft YaHei UI",14,"bold"))
        self.import_btn.pack(fill="x",padx=22,pady=(46,0))
        self.file = ctk.CTkLabel(side,text="支持导入：Excel、CSV、TXT、LOG、TRC",justify="left",wraplength=235,text_color="#d9eaf7"); self.file.pack(anchor="w",padx=24,pady=(13,22))
        self.source_label=ctk.CTkLabel(side,text="数据源 / 工作表",text_color="#b9d6eb",font=("Microsoft YaHei UI",12,"bold"))
        self.source_label.pack(anchor="w",padx=24)
        self.sheet = ctk.CTkComboBox(side,values=["导入后显示数据源"],state="readonly",command=self.change_sheet,height=36); self.sheet.pack(fill="x",padx=22,pady=(7,22)); self.sheet.set("导入后显示数据源")
        self.export_label=ctk.CTkLabel(side,text="导出格式",text_color="#b9d6eb",font=("Microsoft YaHei UI",12,"bold"))
        self.export_label.pack(anchor="w",padx=24)
        self.fmt=ctk.CTkSegmentedButton(side,values=["Excel","CSV","TXT"]); self.fmt.set("Excel"); self.fmt.pack(fill="x",padx=22,pady=(8,10))
        self.export_btn=ctk.CTkButton(side,text="⇩  导出当前结果",height=42,fg_color="#38a169",hover_color="#258052",text_color="#ffffff",font=("Microsoft YaHei UI",13,"bold"),command=self.export)
        self.export_btn.pack(fill="x",padx=22)
        self.chart_btn=ctk.CTkButton(side,text="▥  生成图表并导出",height=42,fg_color="#0891b2",hover_color="#0e7490",text_color="#ffffff",font=("Microsoft YaHei UI",13,"bold"),command=self.open_chart)
        self.chart_btn.pack(fill="x",padx=22,pady=(9,0))
        self.about_btn=ctk.CTkButton(side,text="关于",height=38,fg_color="#193d57",hover_color="#24516f",command=self.show_about)
        self.about_btn.pack(side="bottom",fill="x",padx=20,pady=(0,22))
        self.language_btn=ctk.CTkButton(side,text="语言",height=38,fg_color="#193d57",hover_color="#24516f",command=self.show_language_menu)
        self.language_btn.pack(side="bottom",fill="x",padx=20,pady=(0,8))
        head=ctk.CTkFrame(self,height=84,corner_radius=0,fg_color="white"); head.grid(row=0,column=1,sticky="ew"); head.grid_columnconfigure(0,weight=1)
        self.status=ctk.CTkLabel(head,text="导入文件，自动提取 values 和 percent",font=("Microsoft YaHei UI",16,"bold"),text_color="#1f3b57"); self.status.grid(row=0,column=0,padx=28,pady=(18,2),sticky="w")
        self.meta=ctk.CTkLabel(head,text="支持 Excel、CSV、TXT、LOG 与 TRC 文件",text_color="#78909c"); self.meta.grid(row=1,column=0,padx=29,pady=(0,16),sticky="w")
        self.language_popup = None
        main=ctk.CTkFrame(self,corner_radius=0,fg_color="#f4f7fb"); main.grid(row=1,column=1,sticky="nsew"); main.grid_columnconfigure(0,weight=1); main.grid_rowconfigure(2,weight=1)
        box=ctk.CTkFrame(main,fg_color="#ffffff",corner_radius=14,border_width=1,border_color="#e2e8f0"); box.grid(row=0,column=0,padx=22,pady=(20,10),sticky="ew"); box.grid_columnconfigure(0,weight=1)
        self.advanced_label=ctk.CTkLabel(box,text="高级筛选（可选）",font=("Microsoft YaHei UI",15,"bold"),text_color="#243b53")
        self.advanced_label.grid(row=0,column=0,padx=18,pady=(14,6),sticky="w")
        self.logic=ctk.CTkSegmentedButton(box,values=["全部条件 AND","任一条件 OR"],width=300,selected_color="#0f766e",selected_hover_color="#115e59",unselected_color="#475569",unselected_hover_color="#334155",text_color="#ffffff"); self.logic.set("全部条件 AND"); self.logic.grid(row=0,column=1,padx=18,pady=(14,6),sticky="e")
        self.condbox=ctk.CTkFrame(box,fg_color="transparent"); self.condbox.grid(row=1,column=0,columnspan=2,padx=14,sticky="ew")
        self.add_btn=ctk.CTkButton(box,text="＋ 添加条件",width=116,height=34,corner_radius=8,fg_color="#0ea5e9",hover_color="#0284c7",command=self.add_condition)
        self.add_btn.grid(row=2,column=0,padx=18,pady=(8,14),sticky="w")
        self.clear_btn=ctk.CTkButton(box,text="清空筛选",width=104,height=34,corner_radius=8,fg_color="#64748b",hover_color="#475569",command=self.clear_conditions)
        self.clear_btn.grid(row=2,column=1,padx=18,pady=(8,14),sticky="e")
        tools=ctk.CTkFrame(main,fg_color="transparent"); tools.grid(row=1,column=0,padx=24,pady=5,sticky="ew"); tools.grid_columnconfigure(0,weight=1)
        self.quick=tk.StringVar(); self.quick_entry=ctk.CTkEntry(tools,textvariable=self.quick,placeholder_text="快速搜索全部列…",height=35,width=280); self.quick_entry.grid(row=0,column=0,sticky="w"); self.quick_entry.bind("<Return>",lambda _:self.apply())
        self.search_btn=ctk.CTkButton(tools,text="搜索 / 应用筛选",width=120,height=35,fg_color="#2563eb",hover_color="#1d4ed8",command=self.apply)
        self.search_btn.grid(row=0,column=1,padx=8)
        self.dedupe_btn=ctk.CTkButton(tools,text="去除重复行",width=105,height=35,fg_color="#7c3aed",hover_color="#6d28d9",command=self.dedupe)
        self.dedupe_btn.grid(row=0,column=2,padx=4)
        self.reextract_btn=ctk.CTkButton(tools,text="重新自动提取",width=90,height=35,fg_color="#0f766e",hover_color="#115e59",command=self.extract_primary)
        self.reextract_btn.grid(row=0,column=3,padx=4)
        self.restore_btn=ctk.CTkButton(tools,text="恢复原始数据",width=110,height=35,fg_color="#d97706",hover_color="#b45309",text_color="#ffffff",command=self.reset)
        self.restore_btn.grid(row=0,column=4)
        self.clear_all_btn=ctk.CTkButton(tools,text="清空全部数据",width=112,height=35,fg_color="#dc2626",hover_color="#b91c1c",command=self.clear_all_data)
        self.clear_all_btn.grid(row=0,column=5,padx=(8,0))
        self.colmenu=ctk.CTkOptionMenu(tools,values=["列操作","选择显示列…","显示全部列"],width=115,height=35,fg_color="#475569",button_color="#334155",button_hover_color="#1e293b",command=self.column_action)
        self.colmenu.grid(row=0,column=6,padx=(8,0)); self.colmenu.set("列操作")
        table=ctk.CTkFrame(main,fg_color="#ffffff",corner_radius=14,border_width=1,border_color="#e2e8f0"); table.grid(row=2,column=0,padx=22,pady=(8,20),sticky="nsew"); table.grid_columnconfigure(0,weight=1); table.grid_rowconfigure(1,weight=1)
        top=ctk.CTkFrame(table,fg_color="transparent"); top.grid(row=0,column=0,padx=16,pady=(13,7),sticky="ew"); top.grid_columnconfigure(1,weight=1)
        self.preview_label=ctk.CTkLabel(top,text="结果预览",font=("Microsoft YaHei UI",15,"bold"),text_color="#243b53")
        self.preview_label.grid(row=0,column=0,sticky="w")
        self.rows=ctk.CTkLabel(top,text="0 行",text_color="#607d8b"); self.rows.grid(row=0,column=1,padx=12,sticky="w")
        wrap=ctk.CTkFrame(table,fg_color="transparent"); wrap.grid(row=1,column=0,padx=15,pady=(0,15),sticky="nsew"); wrap.grid_columnconfigure(0,weight=1); wrap.grid_rowconfigure(0,weight=1)
        self.tree=ttk.Treeview(wrap,show="headings",selectmode="extended"); y=ttk.Scrollbar(wrap,orient="vertical",command=self.tree.yview); x=ttk.Scrollbar(wrap,orient="horizontal",command=self.tree.xview); self.tree.configure(yscrollcommand=y.set,xscrollcommand=x.set); self.tree.grid(row=0,column=0,sticky="nsew"); y.grid(row=0,column=1,sticky="ns"); x.grid(row=1,column=0,sticky="ew"); self.tree.bind("<Control-c>",self.copy_selection); self.tree.bind("<Button-3>",self.popup_copy_menu)

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
        popup.configure(bg="#12314a")
        popup.geometry(f"{width}x{height}+{x}+{y}")
        self.language_popup = popup
        self.language_option_buttons = []
        panel = ctk.CTkFrame(popup, fg_color="#163b56", corner_radius=10, border_width=1, border_color="#315f7e")
        panel.pack(fill="both", expand=True)
        for code, label, choice in (("zh", "中文", "中文"), ("en", "English", "English")):
            selected = self.lang == code
            button = ctk.CTkButton(panel, text=("✓  " if selected else "    ") + label, height=38, corner_radius=7, anchor="w", fg_color="#2b6388" if selected else "transparent", hover_color="#285a7a", text_color="#ffffff", font=("Microsoft YaHei UI", 12, "bold" if selected else "normal"), command=lambda c=choice:self.select_language(c))
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


    def import_file(self):
        p=filedialog.askopenfilename(title=self.tr("select_file"),filetypes=[(self.tr("data_files"),"*.xlsx *.xls *.csv *.txt *.log *.trc"),(self.tr("all_files"),"*.*")])
        if not p:return
        self.path=Path(p)
        try:
            if self.path.suffix.lower() in (".xlsx",".xls"):
                names=pd.ExcelFile(p).sheet_names; self.sheet.configure(values=names,state="readonly"); self.sheet.set(names[0]); self.load_sheet(names[0])
            elif self.path.suffix.lower()==".trc":
                value=self.tr("source_trc"); self.sheet.configure(values=[value],state="readonly"); self.sheet.set(value); self.load_trc(p)
            elif self.path.suffix.lower()==".log":
                value=self.tr("source_log"); self.sheet.configure(values=[value],state="readonly"); self.sheet.set(value); self.load_log(p)
            else:
                label=self.tr("source_csv") if self.path.suffix.lower()==".csv" else self.tr("source_txt"); self.sheet.configure(values=[label],state="readonly"); self.sheet.set(label); self.load_text(p)
            self.file.configure(text=self.tr("imported",name=self.path.name))
        except Exception as e: messagebox.showerror(self.tr("import_failed"),str(e))
    def load_text(self,p):
        lines=None
        for enc in ("utf-8-sig","utf-8","gb18030","gbk","latin1"):
            try:
                with open(p,"r",encoding=enc) as f:lines=f.read().splitlines()
                break
            except UnicodeDecodeError:continue
        if lines is None:raise ValueError("无法识别文件编码")
        sample="\n".join(lines[:30])
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
        self.source=pd.DataFrame(rows)
        for key in ("status","values","percent"):
            self.source[key]=self.source["日志内容"].str.extract(r"(?i)(?<![A-Za-z0-9_])"+key+r"\s*:\s*([^\s,;]+)",expand=False).fillna("")
        self.loaded()

    def change_sheet(self,name):
        if self.path and self.path.suffix.lower() in (".xlsx",".xls"):self.load_sheet(name)
    def load_sheet(self,name): self.source=pd.read_excel(self.path,sheet_name=name); self.loaded()
    def loaded(self):
        self.source.columns=[str(x) for x in self.source.columns]; self.result=self.source.copy(); self.visible={x:True for x in self.source.columns}; self.clear_conditions(); extracted=self.extract_primary(silent=True); self.meta.configure(text=self.tr("summary",name=self.path.name,source=len(self.source),result=len(self.result))); (not extracted) and (self.refresh() or self.status.configure(text=self.tr("auto_none")))
    def add_condition(self):
        if self.source is None: messagebox.showinfo(self.tr("info"),self.tr("no_file")); return
        r=ctk.CTkFrame(self.condbox,fg_color="#f4f7fb",corner_radius=8);r.pack(fill="x",pady=4)
        col=ctk.CTkComboBox(r,values=list(self.source.columns),width=190);col.set(str(self.source.columns[0]));col.pack(side="left",padx=(8,5),pady=7)
        op=ctk.CTkComboBox(r,values=TEXT[self.lang]["ops"],width=150);op.set(TEXT[self.lang]["ops"][0]);op.pack(side="left",padx=5,pady=7)
        val=ctk.CTkEntry(r,placeholder_text=self.tr("condition_value"),height=31);val.pack(side="left",fill="x",expand=True,padx=5,pady=7)
        ctk.CTkButton(r,text="×",width=32,height=31,fg_color="#e57373",command=lambda:self.remove_condition(r)).pack(side="right",padx=(5,8),pady=7);self.conditions.append((r,col,op,val))
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
        except Exception as e:messagebox.showerror(self.tr("error"),str(e))
    def extract_primary(self,silent=False):
        if self.source is None:return False
        work=self.source.copy()
        if not {"values","percent"}.issubset(work.columns):
            text_col=next((c for c in ("日志内容","文本内容","原始行") if c in work.columns),None)
            if text_col:
                for key in ("values","percent"):work[key]=work[text_col].astype(str).str.extract(r"(?i)(?<![A-Za-z0-9_])"+key+r"\s*[:=]\s*([^\s,;]+)",expand=False).fillna("")
        if not {"values","percent"}.issubset(work.columns):
            if not silent:messagebox.showinfo(self.tr("info"),self.tr("no_fields"))
            return False
        mask=work["values"].astype(str).str.strip().ne("") & work["percent"].astype(str).str.strip().ne("")
        self.result=work.loc[mask,["values","percent"]].copy()
        self.visible={"values":True,"percent":True};self.refresh()
        self.status.configure(text=self.tr("auto_ok",n=len(self.result)))
        if not silent and self.result.empty:messagebox.showinfo(self.tr("info"),self.tr("no_records"))
        return not self.result.empty

    def only_errors(self):
        if self.source is None:return
        if "级别" not in self.source.columns:messagebox.showinfo(self.tr("info"),self.tr("log_only"));return
        self.result=self.source[self.source["级别"].astype(str).str.upper().isin(["ERROR","WARN","E","W","F","FATAL"])].copy();self.refresh()
    def reset(self):
        if self.source is not None:self.result=self.source.copy();self.visible={c:True for c in self.source.columns};self.clear_conditions();self.refresh()
    def clear_all_data(self, confirm=True):
        if self.path is None and self.source is None:
            return
        if confirm and not messagebox.askyesno(self.tr("confirm"), self.tr("confirm_clear")):
            return
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

    def dedupe(self):
        if self.result is None:return
        n=len(self.result);self.result=self.result.drop_duplicates().copy();self.refresh();messagebox.showinfo(self.tr("done"),self.tr("deduped",n=n-len(self.result)))
    def data(self):return self.result[[c for c in self.result.columns if self.visible.get(c,True)]] if self.result is not None else pd.DataFrame()
    def refresh(self):
        if self.result is None:return
        d=self.data();cols=list(d.columns);self.tree.delete(*self.tree.get_children());self.tree["columns"]=cols
        for c in cols:
            anchor = "w" if c in LEFT_ALIGNED_COLUMNS else "center"
            self.tree.heading(c,text=c,anchor="center")
            self.tree.column(c,width=max(120,min(260,len(c)*16+80)),anchor=anchor)
        for _,r in d.head(PREVIEW_ROWS).iterrows():self.tree.insert("","end",values=["" if pd.isna(x) else str(x)[:500] for x in r])
        self.rows.configure(text=self.tr("rows",n=len(d))+(self.tr("preview_limit") if len(d)>PREVIEW_ROWS else ""))
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
        open_chart_dialog(self, self.result.copy() if self.result is not None else None, self.lang, self.path.name if self.path else "", self.chart_settings)

    def export(self):
        if self.result is None:messagebox.showinfo(self.tr("info"),self.tr("export_first"));return
        f=self.fmt.get();ext={"Excel":".xlsx","CSV":".csv","TXT":".txt"}[f];p=filedialog.asksaveasfilename(title=self.tr("save_title"),defaultextension=ext,initialfile=self.tr("save_name")+ext,filetypes=[(f+" File" if self.lang=="en" else f+" 文件","*"+ext)])
        if not p:return
        try:
            d=self.data()
            if f=="Excel":d.to_excel(p,index=False)
            elif f=="CSV":d.to_csv(p,index=False,encoding="utf-8-sig")
            else:d.to_csv(p,index=False,sep="\t",encoding="utf-8-sig",quoting=csv.QUOTE_MINIMAL)
            messagebox.showinfo(self.tr("export_ok"),self.tr("saved",n=len(d),path=p))
        except Exception as e:messagebox.showerror(self.tr("export_failed"),str(e))
if __name__=="__main__":App().mainloop()
