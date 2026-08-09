import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import csv, re
import pandas as pd
import customtkinter as ctk

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")
PREVIEW_ROWS = 500
OPS = ["包含", "不包含", "等于", "不等于", "开头是", "结尾是", "大于", "小于", "非空", "为空"]

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("数据提取")
        self.geometry("1360x820"); self.minsize(1080, 680)
        self.source = self.result = None; self.path = None; self.conditions = []; self.visible = {}
        self._style(); self._ui()

    def _style(self):
        s = ttk.Style(); s.theme_use("clam")
        s.configure("Treeview", background="#fff", fieldbackground="#fff", foreground="#263238", rowheight=28, font=("Microsoft YaHei UI", 10))
        s.configure("Treeview.Heading", background="#e8f1ff", foreground="#1e3a5f", font=("Microsoft YaHei UI", 10, "bold"))
        s.map("Treeview", background=[("selected", "#2f80ed")], foreground=[("selected", "white")])

    def _ui(self):
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(1, weight=1)
        side = ctk.CTkFrame(self, width=285, corner_radius=0, fg_color="#102a43"); side.grid(row=0,column=0,rowspan=2,sticky="nsew"); side.grid_propagate(False)
        ctk.CTkLabel(side,text="数据提取",font=("Microsoft YaHei UI",27,"bold"),text_color="white").pack(anchor="w",padx=26,pady=(32,2))
        ctk.CTkLabel(side,text="Excel · CSV · TXT 数据处理工具",font=("Microsoft YaHei UI",12),text_color="#b9d6eb").pack(anchor="w",padx=27,pady=(0,26))
        ctk.CTkButton(side,text="＋  导入数据文件",height=44,command=self.import_file,font=("Microsoft YaHei UI",14,"bold")).pack(fill="x",padx=22)
        self.file = ctk.CTkLabel(side,text="尚未导入文件",justify="left",wraplength=235,text_color="#d9eaf7"); self.file.pack(anchor="w",padx=24,pady=(13,22))
        ctk.CTkLabel(side,text="工作表",text_color="#b9d6eb",font=("Microsoft YaHei UI",12,"bold")).pack(anchor="w",padx=24)
        self.sheet = ctk.CTkComboBox(side,values=["请先导入文件"],state="disabled",command=self.change_sheet,height=36); self.sheet.pack(fill="x",padx=22,pady=(7,22))
        ctk.CTkLabel(side,text="导出格式",text_color="#b9d6eb",font=("Microsoft YaHei UI",12,"bold")).pack(anchor="w",padx=24)
        self.fmt=ctk.CTkSegmentedButton(side,values=["Excel","CSV","TXT"]); self.fmt.set("Excel"); self.fmt.pack(fill="x",padx=22,pady=(8,10))
        ctk.CTkButton(side,text="⇩  导出当前结果",height=42,fg_color="#38a169",hover_color="#258052",command=self.export).pack(fill="x",padx=22)
        ctk.CTkLabel(side,text="支持多条件筛选、去重与选择列导出。",justify="left",wraplength=235,text_color="#8fb3ca",font=("Microsoft YaHei UI",11)).pack(anchor="w",padx=24,pady=14)
        head=ctk.CTkFrame(self,height=84,corner_radius=0,fg_color="white"); head.grid(row=0,column=1,sticky="ew"); head.grid_columnconfigure(0,weight=1)
        self.status=ctk.CTkLabel(head,text="导入文件后即可开始提取",font=("Microsoft YaHei UI",16,"bold"),text_color="#1f3b57"); self.status.grid(row=0,column=0,padx=28,pady=(18,2),sticky="w")
        self.meta=ctk.CTkLabel(head,text="支持 Excel、CSV 与 TXT 文件",text_color="#78909c"); self.meta.grid(row=1,column=0,padx=29,pady=(0,16),sticky="w")
        main=ctk.CTkFrame(self,corner_radius=0,fg_color="#f4f7fb"); main.grid(row=1,column=1,sticky="nsew"); main.grid_columnconfigure(0,weight=1); main.grid_rowconfigure(2,weight=1)
        box=ctk.CTkFrame(main,fg_color="white",corner_radius=12); box.grid(row=0,column=0,padx=22,pady=(20,10),sticky="ew"); box.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(box,text="筛选条件",font=("Microsoft YaHei UI",15,"bold"),text_color="#243b53").grid(row=0,column=0,padx=18,pady=(14,6),sticky="w")
        self.logic=ctk.CTkSegmentedButton(box,values=["满足全部条件 (AND)","满足任一条件 (OR)"],width=320); self.logic.set("满足全部条件 (AND)"); self.logic.grid(row=0,column=1,padx=18,pady=(14,6),sticky="e")
        self.condbox=ctk.CTkFrame(box,fg_color="transparent"); self.condbox.grid(row=1,column=0,columnspan=2,padx=14,sticky="ew")
        ctk.CTkButton(box,text="＋ 添加条件",width=110,height=32,command=self.add_condition).grid(row=2,column=0,padx=18,pady=(8,14),sticky="w")
        ctk.CTkButton(box,text="清空筛选",width=100,height=32,fg_color="#90a4ae",command=self.clear_conditions).grid(row=2,column=1,padx=18,pady=(8,14),sticky="e")
        tools=ctk.CTkFrame(main,fg_color="transparent"); tools.grid(row=1,column=0,padx=24,pady=5,sticky="ew"); tools.grid_columnconfigure(0,weight=1)
        self.quick=tk.StringVar(); e=ctk.CTkEntry(tools,textvariable=self.quick,placeholder_text="快速搜索全部列…",height=35,width=280); e.grid(row=0,column=0,sticky="w"); e.bind("<Return>",lambda _:self.apply())
        ctk.CTkButton(tools,text="搜索 / 应用筛选",width=120,height=35,command=self.apply).grid(row=0,column=1,padx=8)
        ctk.CTkButton(tools,text="去除重复行",width=105,height=35,fg_color="#64748b",command=self.dedupe).grid(row=0,column=2,padx=4)
        ctk.CTkButton(tools,text="恢复原始数据",width=110,height=35,fg_color="#90a4ae",command=self.reset).grid(row=0,column=3)
        table=ctk.CTkFrame(main,fg_color="white",corner_radius=12); table.grid(row=2,column=0,padx=22,pady=(8,20),sticky="nsew"); table.grid_columnconfigure(0,weight=1); table.grid_rowconfigure(1,weight=1)
        top=ctk.CTkFrame(table,fg_color="transparent"); top.grid(row=0,column=0,padx=16,pady=(13,7),sticky="ew"); top.grid_columnconfigure(1,weight=1)
        ctk.CTkLabel(top,text="结果预览",font=("Microsoft YaHei UI",15,"bold"),text_color="#243b53").grid(row=0,column=0,sticky="w")
        self.rows=ctk.CTkLabel(top,text="0 行",text_color="#607d8b"); self.rows.grid(row=0,column=1,padx=12,sticky="w")
        ctk.CTkButton(top,text="选择显示列",width=104,height=30,command=self.columns).grid(row=0,column=2,sticky="e")
        wrap=ctk.CTkFrame(table,fg_color="transparent"); wrap.grid(row=1,column=0,padx=15,pady=(0,15),sticky="nsew"); wrap.grid_columnconfigure(0,weight=1); wrap.grid_rowconfigure(0,weight=1)
        self.tree=ttk.Treeview(wrap,show="headings"); y=ttk.Scrollbar(wrap,orient="vertical",command=self.tree.yview); x=ttk.Scrollbar(wrap,orient="horizontal",command=self.tree.xview); self.tree.configure(yscrollcommand=y.set,xscrollcommand=x.set); self.tree.grid(row=0,column=0,sticky="nsew"); y.grid(row=0,column=1,sticky="ns"); x.grid(row=1,column=0,sticky="ew")

    def import_file(self):
        p=filedialog.askopenfilename(title="选择数据文件",filetypes=[("数据文件","*.xlsx *.xls *.csv *.txt"),("所有文件","*.*")])
        if not p:return
        self.path=Path(p)
        try:
            if self.path.suffix.lower() in (".xlsx",".xls"):
                names=pd.ExcelFile(p).sheet_names; self.sheet.configure(values=names,state="normal"); self.sheet.set(names[0]); self.load_sheet(names[0])
            else:
                self.sheet.configure(values=["CSV / TXT 文件"],state="disabled"); self.load_text(p)
            self.file.configure(text=f"已导入\n{self.path.name}")
        except Exception as e: messagebox.showerror("导入失败",f"无法读取该文件：\n{e}")
    def load_text(self,p):
        err=None
        for enc in ("utf-8-sig","utf-8","gb18030","gbk","latin1"):
            try: self.source=pd.read_csv(p,encoding=enc,sep=None,engine="python"); self.loaded(); return
            except Exception as e:err=e
        raise err
    def change_sheet(self,name):
        if self.path and self.path.suffix.lower() in (".xlsx",".xls"):self.load_sheet(name)
    def load_sheet(self,name): self.source=pd.read_excel(self.path,sheet_name=name); self.loaded()
    def loaded(self):
        self.source.columns=[str(x) for x in self.source.columns]; self.result=self.source.copy(); self.visible={x:True for x in self.source.columns}; self.clear_conditions(); self.refresh(); self.status.configure(text="数据已就绪，可以开始筛选与提取"); self.meta.configure(text=f"{self.path.name}  ·  {len(self.source):,} 行  ·  {len(self.source.columns)} 列")
    def add_condition(self):
        if self.source is None: messagebox.showinfo("提示","请先导入数据文件。"); return
        r=ctk.CTkFrame(self.condbox,fg_color="#f4f7fb",corner_radius=8);r.pack(fill="x",pady=4)
        col=ctk.CTkComboBox(r,values=list(self.source.columns),width=190);col.set(str(self.source.columns[0]));col.pack(side="left",padx=(8,5),pady=7)
        op=ctk.CTkComboBox(r,values=OPS,width=115);op.set("包含");op.pack(side="left",padx=5,pady=7)
        val=ctk.CTkEntry(r,placeholder_text="输入筛选值",height=31);val.pack(side="left",fill="x",expand=True,padx=5,pady=7)
        ctk.CTkButton(r,text="×",width=32,height=31,fg_color="#e57373",command=lambda:self.remove_condition(r)).pack(side="right",padx=(5,8),pady=7);self.conditions.append((r,col,op,val))
    def remove_condition(self,r):self.conditions=[x for x in self.conditions if x[0]!=r];r.destroy()
    def clear_conditions(self):
        for r,*_ in self.conditions:r.destroy()
        self.conditions=[];self.quick.set("")
    def test(self,s,op,v):
        t=s.fillna("").astype(str);v=v.strip()
        if op=="非空":return t.str.strip().ne("")
        if op=="为空":return t.str.strip().eq("")
        if op=="包含":return t.str.contains(re.escape(v),case=False,na=False)
        if op=="不包含":return ~t.str.contains(re.escape(v),case=False,na=False)
        if op=="等于":return t.str.lower().eq(v.lower())
        if op=="不等于":return ~t.str.lower().eq(v.lower())
        if op=="开头是":return t.str.startswith(v,na=False)
        if op=="结尾是":return t.str.endswith(v,na=False)
        n=pd.to_numeric(s,errors="coerce");q=pd.to_numeric(pd.Series([v]),errors="coerce").iloc[0]
        if pd.isna(q):raise ValueError("大于/小于需要输入数字")
        return n.gt(q) if op=="大于" else n.lt(q)
    def apply(self):
        if self.source is None:return
        try:
            ms=[];q=self.quick.get().strip()
            if q:ms.append(self.source.astype(str).apply(lambda z:z.str.contains(re.escape(q),case=False,na=False)).any(axis=1))
            for _,c,o,v in self.conditions:ms.append(self.test(self.source[c.get()],o.get(),v.get()))
            if ms:
                m=ms[0]
                for z in ms[1:]:m=(m&z) if self.logic.get().startswith("满足全部") else (m|z)
                self.result=self.source[m].copy()
            else:self.result=self.source.copy()
            self.refresh()
        except Exception as e:messagebox.showerror("筛选失败",str(e))
    def reset(self):
        if self.source is not None:self.result=self.source.copy();self.clear_conditions();self.refresh()
    def dedupe(self):
        if self.result is None:return
        n=len(self.result);self.result=self.result.drop_duplicates().copy();self.refresh();messagebox.showinfo("完成",f"已移除 {n-len(self.result)} 行重复数据。")
    def data(self):return self.result[[c for c in self.result.columns if self.visible.get(c,True)]] if self.result is not None else pd.DataFrame()
    def refresh(self):
        if self.result is None:return
        d=self.data();cols=list(d.columns);self.tree.delete(*self.tree.get_children());self.tree["columns"]=cols
        for c in cols:self.tree.heading(c,text=c);self.tree.column(c,width=max(120,min(260,len(c)*16+80)),anchor="w")
        for _,r in d.head(PREVIEW_ROWS).iterrows():self.tree.insert("","end",values=["" if pd.isna(x) else str(x)[:500] for x in r])
        self.rows.configure(text=f"筛选结果：{len(d):,} 行"+("（仅预览前 500 行）" if len(d)>PREVIEW_ROWS else ""))
    def columns(self):
        if self.result is None:return
        w=ctk.CTkToplevel(self);w.title("选择显示与导出列");w.geometry("430x560");w.transient(self);w.grab_set();ctk.CTkLabel(w,text="选择需要保留的列",font=("Microsoft YaHei UI",18,"bold")).pack(pady=(20,10));f=ctk.CTkScrollableFrame(w);f.pack(fill="both",expand=True,padx=20,pady=8);vs={}
        for c in self.result.columns:
            v=tk.BooleanVar(value=self.visible.get(c,True));vs[c]=v;ctk.CTkCheckBox(f,text=c,variable=v).pack(anchor="w",padx=10,pady=5)
        def save():
            if not any(v.get() for v in vs.values()):messagebox.showwarning("提示","至少保留一列。");return
            self.visible={c:v.get() for c,v in vs.items()};self.refresh();w.destroy()
        ctk.CTkButton(w,text="保存选择",command=save,height=38).pack(pady=(5,20))
    def export(self):
        if self.result is None:messagebox.showinfo("提示","请先导入数据并筛选。");return
        f=self.fmt.get();ext={"Excel":".xlsx","CSV":".csv","TXT":".txt"}[f];p=filedialog.asksaveasfilename(title="保存提取结果",defaultextension=ext,initialfile="提取结果"+ext,filetypes=[(f+" 文件","*"+ext)])
        if not p:return
        try:
            d=self.data()
            if f=="Excel":d.to_excel(p,index=False)
            elif f=="CSV":d.to_csv(p,index=False,encoding="utf-8-sig")
            else:d.to_csv(p,index=False,sep="\t",encoding="utf-8-sig",quoting=csv.QUOTE_MINIMAL)
            messagebox.showinfo("导出成功",f"已保存 {len(d):,} 行数据：\n{p}")
        except Exception as e:messagebox.showerror("导出失败",str(e))
if __name__=="__main__":App().mainloop()
