"""Modal format choice only; audited export remains the business boundary."""
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from window_theme import BrandedToplevel


class ExportChoiceMixin:
    export_format_window = None

    def open_export_format(self):
        w = self.export_format_window
        if w is not None and w.winfo_exists():
            w.deiconify(); w.lift(); w.focus_set()
            return w
        if self.result is None:
            messagebox.showinfo(self.tr('info'), self.tr('export_first'))
            return None
        # Never steal an import/column/dialog grab or race an in-flight import.
        if getattr(self, '_import_busy', False) or self.grab_current() is not None:
            return None
        w = self.export_format_window = BrandedToplevel(self)
        try:
            w.withdraw(); w.transient(self)
            w.title(self.tr('export_choose'))
            w.configure(fg_color='#F5F7FA')
            w.geometry('480x340'); w.minsize(440, 320)
            w.grid_columnconfigure(0, weight=1)
            self.export_format_heading = self.label(w, self.tr('export_choose'), bold=True)
            self.export_format_heading.grid(row=0, column=0, padx=22, pady=(18,10))
            self.export_format_buttons = {}
            self.export_format_descriptions = {}
            for row, (fmt, ext) in enumerate((('Excel','.xlsx'),('CSV','.csv'),('TXT','.txt')), 1):
                box = ctk.CTkFrame(w, fg_color='transparent')
                box.grid(row=row, column=0, sticky='ew', padx=22, pady=5)
                box.grid_columnconfigure(1, weight=1)
                button = self.button(box, lambda f=fmt: self.choose_export_format(f), width=150)
                button.configure(text=f'{fmt} ({ext})')
                button.grid(row=0, column=0, padx=(0,14))
                self.export_format_buttons[fmt] = button
                hint = self.label(box, self.tr('export_hint_' + fmt.lower()), anchor='w', justify='left', wraplength=205)
                hint.configure(font=(self.ui_font,12))
                hint.grid(row=0, column=1, sticky='w')
                self.export_format_descriptions[fmt] = hint
            self.export_format_cancel = self.button(w, self.close_export_format, width=110)
            self.export_format_cancel.configure(text=self.tr('export_cancel'))
            self.export_format_cancel.grid(row=4, column=0, sticky='e', padx=22, pady=16)
            w.protocol('WM_DELETE_WINDOW', self.close_export_format)
            w.bind('<Escape>', self._escape_export_format)
            w.bind('<Destroy>', self._export_format_destroyed, add='+')
            w.deiconify(); w.wait_visibility(); w.grab_set(); w.focus_set()
            return w
        except Exception:
            self.close_export_format()
            raise

    def _escape_export_format(self, event=None):
        self.close_export_format()
        return 'break'

    def _export_format_destroyed(self, event):
        if event.widget is self.export_format_window:
            self.export_format_window = None

    def close_export_format(self):
        w = self.export_format_window
        self.export_format_window = None
        if w is not None and w.winfo_exists():
            try:
                if self.grab_current() is w:
                    w.grab_release()
            finally:
                w.destroy()

    def choose_export_format(self, fmt):
        if fmt not in ('Excel', 'CSV', 'TXT'):
            raise ValueError('Unsupported export format')
        w = self.export_format_window
        if w is None or not w.winfo_exists():
            return
        self.fmt.set(fmt)
        self.close_export_format()
        return self.export()

    def destroy(self):
        self.close_export_format()
        super().destroy()
