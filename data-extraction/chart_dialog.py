import re
from collections import Counter
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import pandas as pd
from matplotlib.figure import Figure
from matplotlib import rcParams
rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
rcParams["axes.unicode_minus"] = False
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

NUMBER_UNIT_RE = re.compile(r'^\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*(.*?)\s*$')

def parse_numeric_unit(value):
    if value is None or pd.isna(value): return None, ''
    m = NUMBER_UNIT_RE.match(str(value).replace(',', ''))
    return (float(m.group(1)), m.group(2).strip()) if m else (None, '')

def analyze_series(series):
    parsed = [parse_numeric_unit(v) for v in series]
    units = Counter(u for n,u in parsed if n is not None and u)
    return parsed, (units.most_common(1)[0][0] if units else '')

UNIT_SCALE = {'uV':('voltage',1e-6),'µV':('voltage',1e-6),'mV':('voltage',1e-3),'V':('voltage',1.0),'kV':('voltage',1e3),'uA':('current',1e-6),'µA':('current',1e-6),'mA':('current',1e-3),'A':('current',1.0),'%':('percent',1.0),'°C':('temperature',1.0),'℃':('temperature',1.0)}

def convert_series(parsed, detected_unit, target_unit):
    target=target_unit.strip();converted=[]
    for number,source in parsed:
        if number is None: converted.append(None);continue
        source=source or detected_unit
        if not target or not source or source==target: converted.append(number);continue
        src,dst=UNIT_SCALE.get(source),UNIT_SCALE.get(target)
        if src and dst and src[0]==dst[0]: converted.append(number*src[1]/dst[1])
        elif target not in UNIT_SCALE: converted.append(number)
        else: converted.append(None)
    return converted

class ChartDialog(ctk.CTkToplevel):
    def __init__(self, parent, data, lang='zh', source_name=''):
        super().__init__(parent)
        self.data = data.copy(); self.lang = lang; self.source_name = source_name
        self.title('图表设置与预览' if lang=='zh' else 'Chart Settings & Preview')
        self.geometry('1180x760'); self.minsize(980,650); self.transient(parent)
        self.protocol('WM_DELETE_WINDOW', self.destroy)
        self.series = {}
        self._build(); self.after(120, self.refresh_preview)

    def _build(self):
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        left=ctk.CTkScrollableFrame(self,width=315,fg_color='#f1f5f9');left.grid(row=0,column=0,sticky='nsew',padx=(12,6),pady=12)
        right=ctk.CTkFrame(self,fg_color='white');right.grid(row=0,column=1,sticky='nsew',padx=(6,12),pady=12);right.grid_columnconfigure(0,weight=1);right.grid_rowconfigure(1,weight=1)
        zh=self.lang=='zh'; ctk.CTkLabel(left,text='图表设置' if zh else 'Chart Settings',font=('Microsoft YaHei UI',20,'bold')).pack(anchor='w',padx=10,pady=(8,16))
        title_default=(Path(self.source_name).stem+' - 趋势图') if self.source_name else ('数据趋势图' if zh else 'Data Trend')
        self.title_var=tk.StringVar(value=title_default);self._entry(left,'图表标题' if zh else 'Chart title',self.title_var)
        self.chart_type=tk.StringVar(value='折线图' if zh else 'Line');self._option(left,'图表类型' if zh else 'Chart type',self.chart_type,['折线图','散点图','折线＋数据点'] if zh else ['Line','Scatter','Line + markers'])
        xvalues=['记录序号' if zh else 'Record index']+[str(c) for c in self.data.columns if c not in ('values','percent')]
        self.x_axis=tk.StringVar(value=xvalues[0]);self._option(left,'横轴' if zh else 'X axis',self.x_axis,xvalues)
        for col,default_name in [('values','数值' if zh else 'Values'),('percent','百分比' if zh else 'Percent')]:
            if col not in self.data.columns: continue
            parsed,unit=analyze_series(self.data[col]);enabled=tk.BooleanVar(value=True);name=tk.StringVar(value=default_name);unit_var=tk.StringVar(value=unit)
            self.series[col]={'enabled':enabled,'name':name,'unit':unit_var,'parsed':parsed,'detected_unit':unit,'color':'#2563eb' if col=='values' else '#f97316'}
            box=ctk.CTkFrame(left,fg_color='white',corner_radius=10);box.pack(fill='x',padx=7,pady=7)
            ctk.CTkCheckBox(box,text=col,variable=enabled,command=self.refresh_preview,font=('Microsoft YaHei UI',13,'bold')).pack(anchor='w',padx=12,pady=(12,6))
            self._entry(box,'名称' if zh else 'Name',name);self._entry(box,'单位' if zh else 'Unit',unit_var)
        self.grid_var=tk.BooleanVar(value=True);self.legend_var=tk.BooleanVar(value=True)
        ctk.CTkCheckBox(left,text='显示网格' if zh else 'Show grid',variable=self.grid_var,command=self.refresh_preview).pack(anchor='w',padx=12,pady=(12,5))
        ctk.CTkCheckBox(left,text='显示图例' if zh else 'Show legend',variable=self.legend_var,command=self.refresh_preview).pack(anchor='w',padx=12,pady=5)
        self.stats=ctk.CTkLabel(right,text='',text_color='#475569');self.stats.grid(row=0,column=0,sticky='w',padx=18,pady=(12,2))
        self.figure=Figure(figsize=(8,5),dpi=100);self.canvas=FigureCanvasTkAgg(self.figure,master=right);self.canvas.get_tk_widget().grid(row=1,column=0,sticky='nsew',padx=10,pady=8)
        actions=ctk.CTkFrame(right,fg_color='transparent');actions.grid(row=2,column=0,sticky='e',padx=14,pady=(0,12))
        ctk.CTkButton(actions,text='刷新预览' if zh else 'Refresh',command=self.refresh_preview,fg_color='#0f766e').pack(side='left',padx=5)
        ctk.CTkButton(actions,text='导出图表' if zh else 'Export Chart',command=self.export_chart,fg_color='#7c3aed').pack(side='left',padx=5)
        ctk.CTkButton(actions,text='关闭' if zh else 'Close',command=self.destroy,fg_color='#64748b').pack(side='left',padx=5)

    def _entry(self,parent,label,var):
        ctk.CTkLabel(parent,text=label,text_color='#475569').pack(anchor='w',padx=10,pady=(5,2));e=ctk.CTkEntry(parent,textvariable=var);e.pack(fill='x',padx=10,pady=(0,7));e.bind('<KeyRelease>',lambda _e:self.after(120,self.refresh_preview));return e
    def _option(self,parent,label,var,values):
        ctk.CTkLabel(parent,text=label,text_color='#475569').pack(anchor='w',padx=10,pady=(5,2));ctk.CTkOptionMenu(parent,variable=var,values=values,command=lambda _v:self.refresh_preview()).pack(fill='x',padx=10,pady=(0,7))
    def axis_label(self,item):
        n=item['name'].get().strip();u=item['unit'].get().strip();return f'{n}（{u}）' if u else n
    def selected(self): return [(k,v) for k,v in self.series.items() if v['enabled'].get()]
    def draw(self):
        chosen=self.selected()
        if not chosen: raise ValueError('请至少选择一个数据系列。' if self.lang=='zh' else 'Select at least one series.')
        self.figure.clear();ax=self.figure.add_subplot(111);axes=[ax];record_label='记录序号' if self.lang=='zh' else 'Record index';xchoice=self.x_axis.get();xdata=list(range(1,len(self.data)+1)) if xchoice==record_label or xchoice not in self.data.columns else list(self.data[xchoice])
        if len(chosen)>1: axes.append(ax.twinx())
        lines=[];valid=set();ctype=self.chart_type.get().lower()
        for i,(key,item) in enumerate(chosen):
            target=axes[min(i,len(axes)-1)];numbers=convert_series(item['parsed'],item['detected_unit'],item['unit'].get());points=[(xdata[x],n,x) for x,n in enumerate(numbers) if n is not None];valid.update(idx for _,_,idx in points)
            if points:
                xs,ys,_idx=zip(*points)
                if '散点' in ctype or 'scatter' in ctype: line=target.scatter(xs,ys,color=item['color'],s=20,label=item['name'].get())
                else:
                    marker='o' if ('数据点' in ctype or 'marker' in ctype) else None
                    line,=target.plot(xs,ys,color=item['color'],linewidth=1.8,marker=marker,markersize=4,label=item['name'].get())
                lines.append(line)
            target.set_ylabel(self.axis_label(item),color=item['color'],fontproperties=None);target.tick_params(axis='y',labelcolor=item['color'])
        ax.set_xlabel(xchoice);ax.set_title(self.title_var.get().strip());ax.grid(self.grid_var.get(),alpha=.25)
        if self.legend_var.get() and lines: ax.legend(lines,[x.get_label() for x in lines],loc='best')
        self.figure.tight_layout();return len(valid),len(self.data)-len(valid)
    def refresh_preview(self):
        try:
            valid,skipped=self.draw();self.canvas.draw_idle();self.stats.configure(text=(f'当前结果：{len(self.data):,} 条  ·  有效绘图：{valid:,} 条  ·  跳过：{skipped:,} 条' if self.lang=='zh' else f'Rows: {len(self.data):,}  ·  Valid: {valid:,}  ·  Skipped: {skipped:,}'))
        except (tk.TclError,ValueError) as e:
            if self.winfo_exists(): self.stats.configure(text=str(e))
    def export_chart(self):
        if not self.selected(): messagebox.showwarning('提示' if self.lang=='zh' else 'Notice','请至少选择一个数据系列。' if self.lang=='zh' else 'Select at least one series.',parent=self);return
        p=filedialog.asksaveasfilename(parent=self,title='导出图表' if self.lang=='zh' else 'Export Chart',defaultextension='.png',initialfile=(Path(self.source_name).stem if self.source_name else 'chart')+'_chart.png',filetypes=[('PNG','*.png'),('PDF','*.pdf'),('SVG','*.svg')])
        if not p:return
        try:self.draw();self.figure.savefig(p,dpi=200,bbox_inches='tight');messagebox.showinfo('导出成功' if self.lang=='zh' else 'Export Complete',f'图表已保存：\n{p}' if self.lang=='zh' else f'Chart saved:\n{p}',parent=self)
        except Exception as e:messagebox.showerror('导出失败' if self.lang=='zh' else 'Export Failed',str(e),parent=self)

def open_chart_dialog(parent,data,lang='zh',source_name=''):
    if data is None or data.empty or not any(c in data.columns for c in ('values','percent')):
        messagebox.showinfo('提示' if lang=='zh' else 'Information','请先导入并自动提取 values 和 percent 数据。' if lang=='zh' else 'Import and auto-extract values and percent data first.',parent=parent);return None
    return ChartDialog(parent,data,lang,source_name)
