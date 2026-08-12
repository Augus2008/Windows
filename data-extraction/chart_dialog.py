import re
from collections import Counter
from pathlib import Path
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import pandas as pd
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage
from matplotlib.figure import Figure
from matplotlib import rcParams
rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
rcParams["axes.unicode_minus"] = False
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

MAX_CHART_POINTS = 5000
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

def representative_indices(series_values, max_points=MAX_CHART_POINTS):
    length = max((len(v) for v in series_values), default=0)
    if length <= max_points: return list(range(length))
    valid_series = [[x if x is not None else float('nan') for x in values] for values in series_values]
    edge = max(2, max_points // max(1, len(valid_series)*2))
    bucket_count = max(1, edge-1); selected={0,length-1}
    for bucket in range(bucket_count):
        start=1+(length-2)*bucket//bucket_count;end=1+(length-2)*(bucket+1)//bucket_count
        if end<=start:continue
        for values in valid_series:
            valid=[i for i in range(start,end) if values[i]==values[i]]
            if valid:selected.add(min(valid,key=lambda i:values[i]));selected.add(max(valid,key=lambda i:values[i]))
    if len(selected)>max_points:
        ordered=sorted(selected);selected={ordered[round(i*(len(ordered)-1)/(max_points-1))] for i in range(max_points)}
    return sorted(selected)

class ChartDialog(ctk.CTkToplevel):
    def __init__(self, parent, data, lang='zh', source_name='', settings=None):
        super().__init__(parent)
        self.data = data.copy(); self.lang = lang; self.source_name = source_name; self.parent_app = parent; self.initial_settings = settings or {}
        self.title('图表设置与预览' if lang=='zh' else 'Chart Settings & Preview')
        self.geometry('1180x760'); self.minsize(980,650); self.transient(parent)
        self.protocol('WM_DELETE_WINDOW', self.request_close)
        self.series = {}; self.dirty = False
        self._build(); self.apply_settings(self.initial_settings); self.snapshot = self.collect_settings(); self.after(120, self.refresh_preview)

    def _build(self):
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        left=ctk.CTkScrollableFrame(self,width=315,fg_color='#f1f5f9');left.grid(row=0,column=0,sticky='nsew',padx=(12,6),pady=12)
        right=ctk.CTkFrame(self,fg_color='white');right.grid(row=0,column=1,sticky='nsew',padx=(6,12),pady=12);right.grid_columnconfigure(0,weight=1);right.grid_rowconfigure(1,weight=1)
        zh=self.lang=='zh'; ctk.CTkLabel(left,text='图表设置' if zh else 'Chart Settings',font=('Microsoft YaHei UI',20,'bold')).pack(anchor='w',padx=10,pady=(8,16))
        title_default=(Path(self.source_name).stem+' - 趋势图') if self.source_name else ('数据趋势图' if zh else 'Data Trend')
        self.title_var=tk.StringVar(value=title_default);self._entry(left,'图表标题' if zh else 'Chart title',self.title_var)
        self.chart_type=tk.StringVar(value='折线图' if zh else 'Line');self._option(left,'图表类型' if zh else 'Chart type',self.chart_type,['折线图','散点图','折线＋数据点'] if zh else ['Line','Scatter','Line + markers'])
        xvalues=['记录序号' if zh else 'Record index']+[str(c) for c in self.data.columns if c not in ('values','percent')]
        self.x_axis=tk.StringVar(value=xvalues[0]);self._option(left,'横轴数据来源' if zh else 'X-axis data source',self.x_axis,xvalues)
        self.x_name=tk.StringVar(value=xvalues[0]);self._entry(left,'横轴名称' if zh else 'X-axis name',self.x_name)
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
        ctk.CTkButton(actions,text='关闭' if zh else 'Close',command=self.request_close,fg_color='#64748b').pack(side='left',padx=5)

    def _entry(self,parent,label,var):
        ctk.CTkLabel(parent,text=label,text_color='#475569').pack(anchor='w',padx=10,pady=(5,2));e=ctk.CTkEntry(parent,textvariable=var);e.pack(fill='x',padx=10,pady=(0,7));e.bind('<KeyRelease>',lambda _e:self.after(120,self.refresh_preview));return e
    def _option(self,parent,label,var,values):
        ctk.CTkLabel(parent,text=label,text_color='#475569').pack(anchor='w',padx=10,pady=(5,2));ctk.CTkOptionMenu(parent,variable=var,values=values,command=lambda _v:self.refresh_preview()).pack(fill='x',padx=10,pady=(0,7))
    def axis_label(self,item):
        n=item['name'].get().strip();u=item['unit'].get().strip();return f'{n}（{u}）' if u else n
    def selected(self): return [(k,v) for k,v in self.series.items() if v['enabled'].get()]
    def plotting_data(self):
        chosen=self.selected();record_label='记录序号' if self.lang=='zh' else 'Record index';xchoice=self.x_axis.get();xdata=list(range(1,len(self.data)+1)) if xchoice==record_label or xchoice not in self.data.columns else list(self.data[xchoice])
        converted=[convert_series(item['parsed'],item['detected_unit'],item['unit'].get()) for _,item in chosen]
        indices=representative_indices(converted,MAX_CHART_POINTS)
        rows=[]
        for idx in indices:
            values=[series[idx] for series in converted]
            if any(value is not None for value in values):rows.append((xdata[idx],values,idx))
        return chosen,rows

    def draw(self):
        chosen,rows=self.plotting_data()
        if not chosen: raise ValueError('请至少选择一个数据系列。' if self.lang=='zh' else 'Select at least one series.')
        self.figure.clear();ax=self.figure.add_subplot(111);axes=[ax]
        if len(chosen)>1: axes.append(ax.twinx())
        lines=[];ctype=self.chart_type.get().lower()
        for series_index,(key,item) in enumerate(chosen):
            target=axes[min(series_index,len(axes)-1)];points=[(x,values[series_index]) for x,values,_ in rows if values[series_index] is not None]
            if points:
                xs,ys=zip(*points)
                if '散点' in ctype or 'scatter' in ctype: line=target.scatter(xs,ys,color=item['color'],s=20,label=item['name'].get())
                else:
                    marker='o' if ('数据点' in ctype or 'marker' in ctype) else None
                    line,=target.plot(xs,ys,color=item['color'],linewidth=1.8,marker=marker,markersize=4,label=item['name'].get())
                lines.append(line)
            target.set_ylabel(self.axis_label(item),color=item['color']);target.tick_params(axis='y',labelcolor=item['color'])
        xchoice=self.x_axis.get();ax.set_xlabel(self.x_name.get().strip() or xchoice);ax.set_title(self.title_var.get().strip());ax.grid(self.grid_var.get(),color='#94a3b8',alpha=.42,linewidth=.75)
        if self.legend_var.get() and lines:ax.legend(lines,[x.get_label() for x in lines],loc='upper center',bbox_to_anchor=(0.5,-0.13),ncol=max(1,len(lines)),frameon=False)
        self.figure.tight_layout(rect=[0,0.12,1,1]);return len(rows),len(self.data)-len(rows)
    def refresh_preview(self):
        try:
            valid,skipped=self.draw();self.canvas.draw_idle();self.stats.configure(text=(f'提取结果：{len(self.data):,} 条  ·  实际绘图：{valid:,} 条  ·  未参与绘图：{skipped:,} 条' if self.lang=='zh' else f'Extracted: {len(self.data):,}  ·  Plotted: {valid:,}  ·  Not plotted: {skipped:,}'))
        except (tk.TclError,ValueError) as e:
            if self.winfo_exists(): self.stats.configure(text=str(e))
    def collect_settings(self):
        return {'title':self.title_var.get(),'chart_type':self.chart_type.get(),'x_axis':self.x_axis.get(),'x_name':self.x_name.get(),'grid':self.grid_var.get(),'legend':self.legend_var.get(),'series':{k:{'enabled':v['enabled'].get(),'name':v['name'].get(),'unit':v['unit'].get()} for k,v in self.series.items()}}
    def apply_settings(self, settings):
        if not settings: return
        for key,var in (('title',self.title_var),('chart_type',self.chart_type),('x_axis',self.x_axis),('x_name',self.x_name)):
            if key in settings: var.set(settings[key])
        if 'grid' in settings:self.grid_var.set(settings['grid'])
        if 'legend' in settings:self.legend_var.set(settings['legend'])
        for key,values in settings.get('series',{}).items():
            if key in self.series:
                for field in ('enabled','name','unit'):
                    if field in values:self.series[key][field].set(values[field])
    def request_close(self):
        current=self.collect_settings()
        if current != self.snapshot:
            answer=messagebox.askyesnocancel('保存图表设置' if self.lang=='zh' else 'Save Chart Settings','是否保存当前修改后关闭？' if self.lang=='zh' else 'Save current changes before closing?',parent=self)
            if answer is None:return
            if answer:self.parent_app.chart_settings=current
        self.destroy()

    def export_excel(self, path):
        chosen,rows=self.plotting_data();wb=Workbook();chart_ws=wb.active;chart_ws.title='Chart Preview';data_ws=wb.create_sheet('Chart Data');xname=self.x_name.get().strip() or self.x_axis.get();data_ws.append([xname]+[self.axis_label(v) for _,v in chosen])
        for x,values,_idx in rows:data_ws.append([x]+values)
        data_ws.freeze_panes='A2';data_ws.auto_filter.ref=data_ws.dimensions
        chart_ws['A1']=self.title_var.get().strip();chart_ws['A1'].font=chart_ws['A1'].font.copy(bold=True,size=16)
        self.draw()
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path=Path(temp_dir)/'chart.png';self.figure.savefig(image_path,dpi=180,bbox_inches='tight',facecolor='white')
            image=ExcelImage(str(image_path));image.width=1100;image.height=650;chart_ws.add_image(image,'A3');wb.save(path)

    def export_chart(self):
        if not self.selected(): messagebox.showwarning('提示' if self.lang=='zh' else 'Notice','请至少选择一个数据系列。' if self.lang=='zh' else 'Select at least one series.',parent=self);return
        p=filedialog.asksaveasfilename(parent=self,title='导出图表' if self.lang=='zh' else 'Export Chart',defaultextension='.png',initialfile=(Path(self.source_name).stem if self.source_name else 'chart')+'_chart.png',filetypes=[('PNG','*.png'),('Excel','*.xlsx'),('PDF','*.pdf'),('SVG','*.svg')])
        if not p:return
        try:
            if Path(p).suffix.lower()=='.xlsx':self.export_excel(p)
            else:self.draw();self.figure.savefig(p,dpi=200,bbox_inches='tight')
            messagebox.showinfo('导出成功' if self.lang=='zh' else 'Export Complete',f'图表已保存：\n{p}' if self.lang=='zh' else f'Chart saved:\n{p}',parent=self)
        except Exception as e:messagebox.showerror('导出失败' if self.lang=='zh' else 'Export Failed',str(e),parent=self)

def open_chart_dialog(parent,data,lang='zh',source_name='',settings=None):
    if data is None or data.empty or not any(c in data.columns for c in ('values','percent')):
        messagebox.showinfo('提示' if lang=='zh' else 'Information','请先导入并自动提取 values 和 percent 数据。' if lang=='zh' else 'Import and auto-extract values and percent data first.',parent=parent);return None
    return ChartDialog(parent,data,lang,source_name,settings)
