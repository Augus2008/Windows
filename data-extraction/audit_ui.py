"""Main-thread audit GUI and transactional result-stage integration."""
from pathlib import Path
from copy import deepcopy
from functools import wraps
from datetime import datetime, timezone
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from window_theme import BrandedToplevel
from audit_ledger import save_report, export_identity

def controls(app):
    return {'quick':app.quick.get(),'logic':app.logic.get(),
      'conditions':[{'column':c.get(),'operator':o.get(),'value':v.get()}
                    for _,c,o,v in app.conditions]}

def report(app):
    return app.audit.report(list(app.data().columns),controls(app))

def save(app,data=None):
    if data is None and not app.audit:return
    if data is None:data=report(app)
    path=filedialog.asksaveasfilename(title=app.tr('audit_save'),defaultextension='.json',filetypes=[('JSON','*.json')])
    if not path:return
    try:
        protected=[x['path'] for x in data['files']+data['exports']]
        save_report(data,path,protected)
        messagebox.showinfo(app.tr('done'),path)
    except Exception as e:messagebox.showerror(app.tr('error'),str(e))

def open_report(app):
    if not app.audit:
        messagebox.showinfo(app.tr('info'),app.tr('export_first')); return
    import json
    window=BrandedToplevel(app); window.title(app.tr('audit_title'))
    window.geometry('980x650'); window.transient(app)
    text=ctk.CTkTextbox(window,wrap='none'); text.pack(fill='both',expand=True,padx=12,pady=12)
    data=report(app)
    summary=app.tr('audit_explain')+'\n\n'
    summary+=app.tr('audit_headers')+'\n'
    for f in data['files']:
        summary+=f"{f['path']} | {app.tr('audit_read') if f['status']=='read' else f['status']} | {f['worksheets_read']} / {f['worksheets_skipped']} | {f['read_rows']} | {f['current_kept']} | {f['excluded']}\n"
    text.insert('1.0',summary+'\n'+json.dumps(data,ensure_ascii=False,indent=2)); text.configure(state='disabled')
    ctk.CTkButton(window,text=app.tr('audit_save'),command=lambda:save(app,data)).pack(pady=10)
    return window

def export(app):
    from verified_export import export_verified
    if app.result is None:
        messagebox.showinfo(app.tr('info'),app.tr('export_first')); return
    fmt=app.fmt.get(); ext={'Excel':'.xlsx','CSV':'.csv','TXT':'.txt'}[fmt]
    path=filedialog.asksaveasfilename(title=app.tr('save_title'),defaultextension=ext,
      initialfile=app.tr('save_name')+ext,filetypes=[(fmt,'*'+ext)])
    if not path:return
    dest=Path(path).resolve()
    try:
        import os
        for src in app.paths:
            if dest==src.resolve() or (dest.exists() and os.path.samefile(dest,src)):
                raise ValueError(app.tr('audit_source_refused'))
        data=app.data().copy()
        metadata=export_verified(data,dest,fmt)
        if metadata.get('status')!='verified':raise ValueError('Export not verified')
        if app.audit:
            metadata.update(verified_at_utc=datetime.now(timezone.utc).isoformat(),export_number=len(app.audit.exports)+1,path=str(dest),stage=len(app.audit.history),
                result_identity=export_identity(app.result.index,app.audit.lineage),
                source_snapshots=[{'file_id':f['file_id'],'sha256':f['sha256']} for f in app.audit.manifest])
            metadata['result_records']=[{'file_id':app.audit.lineage[i][0],'record_number':app.audit.lineage[i][1]} for i in app.result.index]
            for prior in app.audit.exports:
                if prior['path']==str(dest):
                    prior['superseded_by']=metadata['export_number']
                    prior['overwritten_at_utc']=metadata['verified_at_utc']
            app.audit.exports.append(metadata)
    except Exception as e:
        messagebox.showerror(app.tr('export_failed'),str(e)); return
    messagebox.showinfo(app.tr('export_ok'),app.tr('audit_verified',n=len(data),path=str(dest)))


def stage_wrapper(original,operation):
    @wraps(original)
    def call(self,*args,**kwargs):
        if self.source is None:return original(self,*args,**kwargs)
        old=self.result; visible=self.visible.copy()
        ledger=deepcopy(getattr(self,'audit',None))
        filters=controls(self) if operation=='apply' else {}
        try:
            answer=original(self,*args,**kwargs)
            if self.result is old:return answer
            if self.audit:
                basis='result' if operation=='dedupe' else 'source'
                base=old if basis=='result' else self.source
                self.audit.record(operation,basis,list(old.index),list(base.index),
                    list(self.result.index),filters,list(self.data().columns))
                if operation!='apply':
                    self.audit.history[-1]['controls_snapshot_not_applied']=controls(self)
                if operation=='only_errors':
                    self.audit.history[-1]['applied_levels']=['ERROR','WARN','E','W','F','FATAL']
            if operation=='reset':self.clear_conditions()
            return answer
        except Exception as e:
            self.result=old; self.visible=visible; self.audit=ledger
            self.refresh()
            messagebox.showerror(self.tr('error'),str(e))
            return False
    return call


def install(App):
    App.open_audit=open_report
    App.save_audit=save
    App.export=export
    for name in ('apply','extract_primary','dedupe','reset','only_errors'):
        setattr(App,name,stage_wrapper(getattr(App,name),name))
