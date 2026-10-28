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
            w.configure(fg_color='#FFFFFF')
            w.geometry('440x270'); w.minsize(400,250); w.resizable(False, False)
            w.grid_columnconfigure(0, weight=1)
            head = ctk.CTkFrame(w, fg_color='transparent')
            head.grid(row=0, column=0, sticky='ew', padx=22, pady=(16, 4))
            head.grid_columnconfigure(1, weight=1)
            from window_theme import make_brand_image
            w._choice_logo = ctk.CTkImage(make_brand_image(), size=(28, 28))
            ctk.CTkLabel(head, text='', image=w._choice_logo, width=28, height=28).grid(row=0, column=0, rowspan=2, padx=(0, 10))
            self.export_format_heading = self.label(head, self.tr('export_choose'), bold=True, anchor='w')
            self.export_format_heading.configure(font=(self.ui_font, 15, 'bold'))
            self.export_format_heading.grid(row=0, column=1, sticky='w')
            self.export_format_hint = self.label(head, self.tr('export_choose_hint'), anchor='w')
            self.export_format_hint.configure(font=(self.ui_font, 11), text_color='#66788A')
            self.export_format_hint.grid(row=1, column=1, sticky='w')
            self.export_format_buttons = {}
            self.export_format_descriptions = {}
            for row, (fmt, ext) in enumerate((('Excel', '.xlsx'), ('CSV', '.csv'), ('TXT', '.txt')), 1):
                item = ctk.CTkButton(w, text='', height=42, corner_radius=6,
                    fg_color='#F7F9FC', hover_color='#EDF3FE', border_width=1, border_color='#E3E8F0',
                    text_color='#172B4D', anchor='center', font=(self.ui_font, 12, 'bold'),
                    command=lambda f=fmt: self.choose_export_format(f))
                item.grid(row=row, column=0, sticky='ew', padx=22, pady=(4 if row == 1 else 2, 0))
                item._format_name = f'{fmt} ({ext})'
                item._format_hint = self.tr('export_hint_' + fmt.lower())
                item.configure(text=self._format_row_text(item))
                item.bind('<Enter>', lambda e, b=item: b.configure(fg_color='#EDF3FE'))
                item.bind('<Leave>', lambda e, b=item: b.configure(fg_color='#F7F9FC'))
                self.export_format_buttons[fmt] = item
                self.export_format_descriptions[fmt] = item._format_hint
            self.export_format_cancel = self.button(w, self.close_export_format, width=88)
            self.export_format_cancel.configure(text=self.tr('export_cancel'), height=30)
            self.export_format_cancel.grid(row=4, column=0, sticky='e', padx=22, pady=(10, 14))
            w.protocol('WM_DELETE_WINDOW', self.close_export_format)
            w.bind('<Escape>', self._escape_export_format)
            w.bind('<Destroy>', self._export_format_destroyed, add='+')
            w.deiconify(); w.wait_visibility(); w.grab_set(); w.focus_set()
            return w
        except Exception:
            self.close_export_format()
            raise

    def _format_row_text(self, item):
        return f"{item._format_name}    {item._format_hint}"

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
