"""Batch import UI: one background reader, main-thread-only widgets, atomic commit."""
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from window_theme import BrandedToplevel
from audit_ledger import AuditLedger
from batch_io import load_selection, ImportCancelled, enrich_fields


class BatchImportMixin:
    def import_file(self):
        if getattr(self, '_import_busy', False):
            return
        paths = filedialog.askopenfilenames(title=self.tr('select_file'), filetypes=[
            (self.tr('data_files'), '*.xlsx *.xls *.csv *.txt *.log *.trc'),
            (self.tr('all_files'), '*.*')])
        if paths:
            self.begin_import(paths)

    def begin_import(self, paths):
        if getattr(self, '_import_busy', False):
            return
        self._import_busy = True
        self.import_btn.configure(state='disabled')
        window = BrandedToplevel(self)
        window.title(self.tr('batch_loading'))
        window.geometry('470x180')
        window.transient(self)
        window.grab_set()
        label = ctk.CTkLabel(window, text=self.tr('batch_loading'), wraplength=420)
        label.pack(padx=20, pady=20)
        events = queue.Queue()
        cancelled = threading.Event()
        button = ctk.CTkButton(window, text=self.tr('batch_cancel'), command=cancelled.set)
        button.pack(pady=10)
        window.protocol('WM_DELETE_WINDOW', cancelled.set)
        parsers = {'text': type(self).load_text, '.log': type(self).load_log,
                   '.trc': type(self).load_trc}

        def worker():
            try:
                result = load_selection(paths, parsers,
                    lambda i, n, name: events.put(('progress', (i, n, name))), cancelled)
                events.put(('done', result))
            except ImportCancelled:
                events.put(('cancelled', None))
            except Exception as exc:
                events.put(('error', str(exc)))

        def poll():
            while True:
                try:
                    event, value = events.get_nowait()
                except queue.Empty:
                    break
                if event == 'progress':
                    i, n, name = value
                    label.configure(text=self.tr('batch_progress', i=i, n=n, name=name))
                    continue
                window.grab_release()
                window.destroy()
                self._import_busy = False
                self.import_btn.configure(state='normal')
                if event == 'done' and not cancelled.is_set():
                    try:
                        self.commit_import(value)
                    except Exception as exc:
                        messagebox.showerror(self.tr('import_failed'),
                            self.tr('batch_failed', error=str(exc)))
                elif event == 'error' and not cancelled.is_set():
                    messagebox.showerror(self.tr('import_failed'),
                        self.tr('batch_failed', error=value))
                return
            self.after(60, poll)

        threading.Thread(target=worker, daemon=True).start()
        self.after(60, poll)

    def commit_import(self, payload):
        frame = payload['frame']
        result = frame.copy()
        if len(payload['paths']) == 1:
            work = enrich_fields(frame)
            if {'values', 'percent'}.issubset(work.columns):
                mask = work['values'].fillna('').astype(str).str.strip().ne('')
                mask &= work['percent'].fillna('').astype(str).str.strip().ne('')
                result = work.loc[mask, ['values', 'percent']].copy()
        # Preserve old models and widgets until the new view has rendered successfully.
        fields = ('audit', 'source_record_column', 'paths', 'path', 'source_file_column', 'source', 'result', 'visible', 'chart_settings')
        previous = {key: getattr(self, key) for key in fields}
        labels = {key: getattr(self, key).cget('text') for key in ('file', 'meta', 'status', 'rows')}
        sheet = (list(self.sheet.cget('values')), self.sheet.cget('state'), self.sheet.get())
        try:
            self.audit=AuditLedger(payload)
            self.source_record_column=payload.get('record_column')
            self.paths = payload['paths']
            self.path = self.paths[0]
            self.source_file_column = payload['source_column']
            self.source = frame
            self.result = result
            self.visible = {c: True for c in result.columns}
            self.chart_settings = None
            if len(self.paths) == 1:
                names = payload['sheet_names']
                if names:
                    self.sheet.configure(values=names, state='readonly')
                    self.sheet.set(payload['manifest'][0]['worksheets_read'][0])
            self.refresh_localized_state()
        except Exception:
            for key, value in previous.items():
                setattr(self, key, value)
            self.sheet.configure(values=sheet[0], state=sheet[1])
            self.sheet.set(sheet[2])
            if self.result is None:
                self.tree.delete(*self.tree.get_children())
                self.tree['columns'] = ()
            else:
                self.refresh()
            for key, text in labels.items():
                getattr(self, key).configure(text=text)
            raise
        if list(result.index)!=list(frame.index) or list(result.columns)!=list(frame.columns):
            self.audit.record('auto_extract','source',list(frame.index),list(frame.index),list(result.index),{},list(result.columns))
        # Destructive operations only after rendering succeeds; failures keep filters.
        self.clear_conditions()

    def batch_label(self):
        return self.tr('batch_name', n=len(self.paths))

    def refresh_batch_state(self):
        self.file.configure(text=self.tr('batch_imported', n=len(self.paths)))
        value = self.tr('batch_source')
        self.sheet.configure(values=[value], state='disabled')
        self.sheet.set(value)
        self.meta.configure(text=self.tr('batch_summary', n=len(self.paths),
            source=len(self.source), result=len(self.result)))
        self.status.configure(text=self.tr('batch_ready'))
        self.refresh()
