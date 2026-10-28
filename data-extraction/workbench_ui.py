"""Read-only workbench presentation; no model or ledger mutations."""
from numbers import Number
import re
import tkinter as tk
from tkinter import ttk, font as tkfont
import customtkinter as ctk
import pandas as pd
from window_theme import apply_application_icon
BG = '#F5F7FA'
INK = '#172B4D'
MUTED = '#66788A'
BORDER = '#E3E8F0'
BLUE = '#2563EB'
NEUTRAL = '#EDF1F7'



class WorkbenchMixin:
    def destroy(self):
        # Tk timers must not outlive their root (also supports repeated GUI tests).
        for job in self.tk.call('after','info'):
            self.tk.call('after','cancel',job)
        super().destroy()

    def _style(self):
        families = tkfont.families(self)
        self.ui_font = next((f for f in ('Microsoft YaHei UI','Microsoft YaHei','WenQuanYi Zen Hei','文泉驿正黑') if f in families), 'Arial')
        ctk.ThemeManager.theme['CTkFont']['family'] = self.ui_font
        s = ttk.Style(self); s.theme_use('clam')
        s.configure('Treeview', background='white', fieldbackground='white', foreground=INK, rowheight=30, font=(self.ui_font,10), borderwidth=0)
        s.configure('Treeview.Heading', background='#F0F4F9', foreground=INK, font=(self.ui_font,10,'bold'), relief='flat', padding=(8,8))
        s.map('Treeview',background=[('selected','#DBEAFE')],foreground=[('selected',INK)])

    def label(self, parent, text='', bold=False, **kw):
        return ctk.CTkLabel(parent,text=text,font=(self.ui_font,13,'bold' if bold else 'normal'),text_color=INK,**kw)

    def button(self,parent,command,**kw):
        return ctk.CTkButton(parent,text='',command=command,height=34,corner_radius=6,fg_color=NEUTRAL,hover_color='#DFE6F0',text_color=INK,border_width=1,border_color=BORDER,font=(self.ui_font,12),**kw)
    def _ui(self):
        self.configure(fg_color=BG)
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self.sidebar = side = ctk.CTkFrame(self,width=248,corner_radius=0,fg_color='#F0F4F9',border_width=1,border_color=BORDER)
        side.grid(row=0,column=0,sticky='nsew'); side.grid_propagate(False)
        apply_application_icon(self)
        self.source_label=self.label(side,bold=True,anchor='center',justify='center'); self.source_label.pack(fill='x',padx=18,pady=(24,8))
        self.import_btn=self.button(side,self.import_file); self.import_btn.pack(fill='x',padx=18)
        self.file=self.label(side,wraplength=205,justify='center',anchor='center'); self.file.configure(font=(self.ui_font,11)); self.file.pack(fill='x',padx=20,pady=(10,8))
        self.source_files=ctk.CTkScrollableFrame(side,fg_color='transparent',height=160)
        self.source_files.pack(fill='both',expand=True,padx=12,pady=4)
        self.source_file_items=[]; self._manifest_signature=None
        self.sheet=ctk.CTkComboBox(side,values=[''],state='readonly',command=self.change_sheet,height=32,width=206)
        self.sheet.pack(fill='x',padx=18,pady=(8,10))
        self.help_btn=self.button(side,self.show_help_menu)
        self.help_btn.pack(side='bottom',fill='x',padx=18,pady=(0,12))
        self.clear_all_btn=self.button(side,self.clear_all_data); self.clear_all_btn.configure(text_color='#B42332')
        self.clear_all_btn.pack(side='bottom',fill='x',padx=18,pady=(6,6))
        self.main=main=ctk.CTkFrame(self,fg_color='transparent',corner_radius=0)
        main.grid(row=0,column=1,sticky='nsew',padx=20,pady=12)
        main.grid_columnconfigure(0,weight=1); main.grid_rowconfigure(5,weight=1)
        # Retain hidden status fields, without an empty header row.
        self.status=self.label(main,bold=True,anchor='w')
        self.meta=self.label(main,anchor='w')
        self.fmt=tk.StringVar(self,value='Excel')
        stats=ctk.CTkFrame(main,fg_color='transparent'); stats.grid(row=1,column=0,sticky='ew',pady=(0,10))
        self.stat_labels=[]; self.stat_values=[]
        for i in range(3):
            stats.grid_columnconfigure(i,weight=1,uniform='stats')
            card=ctk.CTkFrame(stats,fg_color='white',border_width=1,border_color=BORDER,corner_radius=8)
            card.grid(row=0,column=i,sticky='ew',padx=(0,8) if i<2 else 0)
            title=self.label(card,anchor='center',justify='center'); title.pack(fill='x',padx=14,pady=(8,0))
            value=self.label(card,bold=True,anchor='center',justify='center'); value.configure(font=(self.ui_font,22,'bold')); value.pack(fill='x',padx=14,pady=(0,8))
            self.stat_labels.append(title); self.stat_values.append(value)
        search=ctk.CTkFrame(main,fg_color='transparent'); search.grid(row=2,column=0,sticky='ew'); search.grid_columnconfigure(1,weight=1)
        self.search_caption=self.label(search)
        self.search_caption.grid(row=0,column=0,padx=(0,8))
        self.quick=tk.StringVar()
        self.quick_entry=ctk.CTkEntry(search,textvariable=self.quick,height=34,border_color=BORDER,fg_color='white')
        self.quick_entry.grid(row=0,column=1,sticky='ew'); self.quick_entry.bind('<Return>',lambda _:self.apply())
        self.search_btn=self.button(search,self.apply,width=122); self.search_btn.grid(row=0,column=2,padx=8)
        self.filter_toggle=self.button(search,self.toggle_filter_panel,width=128); self.filter_toggle.grid(row=0,column=3)
        self.filter_panel=box=ctk.CTkFrame(main,fg_color='white',border_width=1,border_color=BORDER)
        box.grid(row=3,column=0,sticky='ew',pady=(8,0)); box.grid_columnconfigure(0,weight=1)
        self.advanced_label=self.label(box,bold=True)
        self.advanced_label.grid(row=0,column=0,sticky='w',padx=12,pady=4)
        self.logic=ctk.CTkSegmentedButton(box,values=['全部条件 AND','任一条件 OR'],height=28,selected_color='#DBEAFE',selected_hover_color='#BFDBFE',text_color=INK,unselected_color=NEUTRAL,command=self.refresh_pending)
        self.logic.set('全部条件 AND'); self.logic.grid(row=0,column=1,padx=12,pady=4)
        viewport=ctk.CTkFrame(box,fg_color='transparent',height=64)
        viewport.grid(row=1,column=0,columnspan=2,sticky='ew',padx=6); viewport.grid_propagate(False); viewport.pack_propagate(False)
        self.condbox=ctk.CTkScrollableFrame(viewport,fg_color='transparent',height=52)
        self.condbox.pack(fill='both',expand=True)
        self.add_btn=self.button(box,self.add_condition,width=112); self.add_btn.grid(row=2,column=0,sticky='w',padx=12,pady=6)
        self.clear_btn=self.button(box,self.clear_conditions,width=112); self.clear_btn.grid(row=2,column=1,sticky='e',padx=12,pady=6)
        box.grid_remove(); self.filter_panel_open=False
        tools=ctk.CTkFrame(main,fg_color='transparent'); tools.grid(row=4,column=0,sticky='ew',pady=8)
        self.dedupe_btn=self.button(tools,self.dedupe,width=108)
        self.reextract_btn=self.button(tools,self.extract_primary,width=122)
        self.restore_btn=self.button(tools,self.reset,width=116)
        for b in (self.dedupe_btn,self.reextract_btn,self.restore_btn): b.pack(side='left',padx=(0,8))
        self.colmenu=ctk.CTkOptionMenu(tools,values=[''],width=132,height=34,fg_color=NEUTRAL,button_color='#DFE6F0',button_hover_color='#CBD5E1',text_color=INK,command=self.column_action)
        self.colmenu.pack(side='left')
        self.table_panel=table=ctk.CTkFrame(main,fg_color='white',corner_radius=8,border_width=1,border_color=BORDER)
        table.grid(row=5,column=0,sticky='nsew'); table.grid_columnconfigure(0,weight=1); table.grid_rowconfigure(1,weight=1)
        self.preview_toolbar=top=ctk.CTkFrame(table,fg_color='transparent')
        top.grid(row=0,column=0,sticky='ew',padx=12,pady=10)
        top.grid_columnconfigure(0,weight=1)
        top.grid_columnconfigure(1,weight=0)
        top.grid_columnconfigure(2,weight=0)
        self.preview_label=self.label(top,bold=True);self.preview_label.grid(row=0,column=0,sticky='w')
        self.preview_actions=actions=ctk.CTkFrame(top,fg_color='transparent')
        actions.grid(row=0,column=1,sticky='e',padx=(8,8))
        self.audit_btn=self.button(actions,self.open_audit,width=128);self.audit_btn.pack(side='left',padx=(0,8))
        self.chart_btn=self.button(actions,self.open_chart,width=170);self.chart_btn.pack(side='left')
        self.export_btn=self.button(top,self.open_export_format,width=170)
        self.export_btn.configure(fg_color=BLUE,hover_color='#1D4ED8',text_color='#ffffff',font=(self.ui_font,13,'bold'))
        self.export_btn.grid(row=0,column=2,sticky='e')
        self.table_wrap=wrap=ctk.CTkFrame(table,fg_color='white',corner_radius=0)
        wrap.grid(row=1,column=0,sticky='nsew',padx=12,pady=(0,6)); wrap.grid_columnconfigure(0,weight=1); wrap.grid_rowconfigure(0,weight=1)
        self.tree=ttk.Treeview(wrap,show='headings',selectmode='extended')
        self.tree.grid(row=0,column=0,sticky='nsew')
        y=ctk.CTkScrollbar(wrap,orientation='vertical',command=self.tree.yview,width=12,button_color='#CBD5E1',button_hover_color='#94A3B8'); y.grid(row=0,column=1,sticky='ns')
        x=ctk.CTkScrollbar(wrap,orientation='horizontal',command=self.tree.xview,height=12,button_color='#CBD5E1',button_hover_color='#94A3B8'); x.grid(row=1,column=0,sticky='ew')
        self.tree.configure(yscrollcommand=y.set,xscrollcommand=x.set)
        self.tree.tag_configure('even',background='white'); self.tree.tag_configure('odd',background='#F7F9FC')
        self.tree.bind('<Control-c>',self.copy_selection); self.tree.bind('<Button-3>',self.popup_copy_menu)
        self.empty_state=ctk.CTkFrame(wrap,fg_color='white')
        self.empty_label=self.label(self.empty_state,bold=True); self.empty_label.pack(padx=20,pady=(18,8))
        self.empty_import_btn=self.button(self.empty_state,self.import_file,width=140); self.empty_import_btn.pack(pady=(0,18))
        footer=ctk.CTkFrame(main,fg_color='transparent'); footer.grid(row=6,column=0,sticky='ew',pady=(6,0)); footer.grid_columnconfigure(0,weight=1)
        self.rows=self.label(footer); self.rows.grid(row=0,column=0,sticky='w')
        self.verification_label=self.label(footer); self.verification_label.configure(text_color=MUTED); self.verification_label.grid(row=0,column=1,sticky='e')
        self.pending_label=self.label(footer); self.pending_label.configure(text_color=MUTED); self.pending_label.grid(row=1,column=0,columnspan=2,sticky='w')
        self.bind('<Configure>',self._fit_context,add='+')
        self.bind('<KeyRelease>',self.refresh_pending,add='+')
        self.bind('<ButtonRelease-1>',lambda e:self.after_idle(self.refresh_pending),add='+')
        self.quick.trace_add("write",lambda *_:self.refresh_pending())

    def _fit_context(self,event=None):
        if event is None or event.widget is self:
            width=max(160,self.winfo_width()-640)
            self.status.configure(wraplength=width)
            self.meta.configure(wraplength=width)
    def show_filter_panel(self,show=True):
        self.filter_panel_open=bool(show)
        if show:self.filter_panel.grid()
        else:self.filter_panel.grid_remove()
        self.filter_toggle.configure(text=self.tr('wb_hide_filters' if show else 'wb_filters'))

    def toggle_filter_panel(self):
        self.show_filter_panel(not self.filter_panel_open)

    def refresh_workbench(self):
        if not hasattr(self,'stat_values'):return
        self.title(f'{self.tr("app_name")} v{self.app_version} - {self.tr("wb_preview")}')
        for widget,key in ((self.search_caption,'wb_search_hint'),(self.pending_label,'wb_pending'),(self.empty_import_btn,'wb_import')):
            widget.configure(text=self.tr(key))
        self.import_btn.configure(text=self.tr('wb_import'))
        self.show_filter_panel(self.filter_panel_open)
        manifest=self.audit.manifest if self.audit else []
        count=len(manifest) if manifest else len(self.paths) or int(self.path is not None)
        read=sum(f['read_rows'] for f in manifest) if manifest else (len(self.source) if self.source is not None else 0)
        result=len(self.result) if self.result is not None else 0
        for label,key,value,num in zip(self.stat_labels,('wb_files','wb_read','wb_result'),self.stat_values,(count,read,result)):
            label.configure(text=self.tr(key)); value.configure(text=f'{num:,}')
        if self.source is not None:
            self.status.configure(text=self.tr('wb_context',n=count))
            self.meta.configure(text=self.tr('wb_loaded'))
        else:
            self.status.configure(text=self.tr('header_empty')); self.meta.configure(text=self.tr('files'))
        self.rows.configure(text=self.tr('rows',n=result)+(self.tr('preview_limit') if result>500 else ''))
        signature=(self.lang,repr(manifest))
        if signature!=self._manifest_signature:
            for child in self.source_files.winfo_children(): child.destroy()
            self.source_file_items=[]
            from pathlib import Path
            for f in manifest:
                name=Path(f['path']).name
                details=self.tr('wb_file_rows',n=f['read_rows'])
                if f.get('worksheets_read'):
                    details+='\n'+self.tr('wb_sheet',name=', '.join(f['worksheets_read']))
                if f.get('worksheets_skipped'):details+='\n'+self.tr('wb_skipped',n=len(f['worksheets_skipped']))
                item=self.label(self.source_files,name+'\n'+details,wraplength=187,justify='left',anchor='w')
                item.pack(fill='x',padx=4,pady=8); self.source_file_items.append(item)
            self._manifest_signature=signature
        empty=self.result is None or self.result.empty
        if empty:
            self.empty_label.configure(text=self.tr('wb_empty' if self.source is None else 'wb_no_results'))
            if self.source is None:self.empty_import_btn.pack(pady=(0,18))
            else:self.empty_import_btn.pack_forget()
            self.empty_state.place(relx=.5,rely=.46,anchor='center'); self.empty_state.lift()
        else:self.empty_state.place_forget()
        self.export_btn.configure(state='normal' if self.result is not None else 'disabled')
        self.verification_label.configure(text=self.tr(self._verification_key()),text_color=MUTED)
        self.refresh_pending()
        self._fit_context()

    def _verification_key(self):
        if self.result is None:return 'wb_unverified'
        if not self.audit or not self.audit.exports:return 'wb_not_exported'
        latest=self.audit.exports[-1]
        if latest.get('status')!='verified' or latest.get('superseded_by'):return 'wb_not_exported'
        from audit_ledger import export_identity
        from verified_export import _text, _digest
        try:
            if latest.get('result_identity')!=export_identity(self.result.index,self.audit.lineage):return 'wb_not_exported'
            d=self.data()
            table=[[_text(c) for c in d.columns]]+[[_text(v) for v in row] for row in d.itertuples(index=False,name=None)]
            if latest.get('content_sha256')==_digest(table):return 'wb_verified'
        except (KeyError,ValueError,TypeError):pass
        return 'wb_not_exported'

    def style_preview_rows(self):
        d=self.data()
        for i,item in enumerate(self.tree.get_children()):self.tree.item(item,tags=('even' if i%2==0 else 'odd',))
        count=max(1,len(d.columns)); available=max(650,self.winfo_width()-328)
        for i,c in enumerate(d.columns):
            text=str(c)
            identity=c in (self.source_record_column,self.source_file_column) or bool(re.search(r'(^|[^a-z])(id|no|code)([^a-z]|$)|编号|序号|记录|标识',text,re.I)) or text.lower().endswith('id')
            values=d[c].dropna()
            raw_numeric=not values.empty and all(isinstance(v,Number) and not isinstance(v,bool) for v in values)
            numeric=(pd.api.types.is_numeric_dtype(d[c].dtype) or raw_numeric) and not pd.api.types.is_bool_dtype(d[c].dtype) and not identity
            sample=d[c].head(40).fillna('').astype(str)
            longest=max([len(text)]+[min(40,len(v)) for v in sample])
            width=max(110,min(300,longest*9+30))
            if count<=5:width=max(width,min(240,available//count))
            if c==self.source_record_column:width=120
            if c==self.source_file_column:width=180
            self.tree.column(f'data_col_{i}',anchor='e' if numeric else 'w',width=width,minwidth=80,stretch=count<=5)
            self.tree.heading(f'data_col_{i}',anchor='w')

    def _normalized_controls(self,controls):
        from i18n import TEXT
        conditions=[]
        for row in controls.get('conditions',[]):
            op=row['operator']
            idx=next((TEXT[lang]['ops'].index(op) for lang in TEXT if op in TEXT[lang]['ops']),op)
            conditions.append((row['column'],idx,row['value']))
        logic=controls.get('logic') in (TEXT['zh']['any'],TEXT['en']['any']) if conditions else False
        return (controls.get('quick','').strip(),logic,conditions)

    def refresh_pending(self,event=None):
        from audit_ui import controls
        applied={}
        if self.audit:
            event=next((e for e in reversed(self.audit.history) if e['operation']!='dedupe'),{})
            if event.get('operation')=='apply':applied=event['filters']
        current=self._normalized_controls(controls(self))
        if self.source is None or (not current[0] and not current[2] and not applied):key='wb_ready'
        elif current!=self._normalized_controls(applied):key='wb_pending'
        else:key='wb_applied'
        self.pending_label.configure(text=self.tr(key))


def refresh_after_action(action):
    """Decorate a completed business action only with view synchronization."""
    from functools import wraps
    @wraps(action)
    def call(self,*args,**kwargs):
        try:return action(self,*args,**kwargs)
        finally:self.refresh_workbench()
    return call
