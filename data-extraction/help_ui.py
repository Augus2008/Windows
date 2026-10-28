"""Read-only Help menu, built-in guide, language and About dialogs."""
import tkinter as tk
import customtkinter as ctk
from window_theme import BrandedToplevel
from help_content import HELP_SECTIONS, help_text

class HelpMixin:
    def init_help(self):
        self.help_window=None;self.about_window=None
        self.help_menu=tk.Menu(self,tearoff=False)
        self.help_language_menu=tk.Menu(self.help_menu,tearoff=False)
        self.help_language_var=tk.StringVar(self,value=self.lang)
        self.refresh_help_language()

    def refresh_help_language(self):
        if not hasattr(self,'help_menu'):return
        self.help_btn.configure(text=self.tr('about'))
        self.help_menu.delete(0,'end');self.help_language_menu.delete(0,'end')
        for label,lang,choice in [('中文','zh','中文'),('English','en','English')]:
            self.help_language_menu.add_radiobutton(label=label,variable=self.help_language_var,
                value=lang,command=lambda c=choice:self.language_action(c))
        self.help_language_var.set(self.lang)
        self.help_menu.add_command(label=self.tr('help_guide'),command=self.open_usage)
        self.help_menu.add_cascade(label=self.tr('language_menu'),menu=self.help_language_menu)
        self.help_menu.add_separator()
        self.help_menu.add_command(label=self.tr('software_info'),command=self.show_about)
        if self.help_window is not None and self.help_window.winfo_exists():
            self.help_window.title(self.tr('help_guide'))
            self.help_heading.configure(text=self.tr('help_guide'))
            self.help_hint.configure(text=self.tr('help_hint'))
            y=self.help_textbox.yview()[0]
            self.help_textbox.configure(state='normal')
            self.help_textbox.delete('1.0','end')
            for i,(_,title,body) in enumerate(HELP_SECTIONS[self.lang]):
                if i:self.help_textbox.insert('end','\n\n')
                self.help_textbox.insert('end',title+'\n','heading')
                self.help_textbox.insert('end',body)
            self.help_textbox.configure(state='disabled');self.help_textbox.yview_moveto(y)
            self.help_close.configure(text=self.tr('help_close'))
        if self.about_window is not None and self.about_window.winfo_exists():
            self.about_window.title(self.tr('about_title'))
            self.about_heading.configure(text=self.tr('app_name'))
            self.about_body.configure(text=self.tr('about_body',version=self.app_version,date=self.build_date))
            self.about_close.configure(text=self.tr('help_close'))

    def show_help_menu(self):
        self.refresh_help_language();self.update_idletasks()
        x=self.help_btn.winfo_rootx()
        y=self.help_btn.winfo_rooty()-self.help_menu.winfo_reqheight()
        try:self.help_menu.tk_popup(x,max(self.winfo_rooty(),y))
        finally:self.help_menu.grab_release()
    def open_usage(self):
        if self.help_window is not None and self.help_window.winfo_exists():
            self.help_window.deiconify();self.help_window.lift();return self.help_window
        w=self.help_window=BrandedToplevel(self);w.withdraw();w.transient(self);w.configure(fg_color='#F5F7FA')
        w.geometry('900x650');w.minsize(680,440)
        w.grid_columnconfigure(0,weight=1);w.grid_rowconfigure(2,weight=1)
        self.help_heading=self.label(w,bold=True);self.help_heading.configure(font=(self.ui_font,20,'bold'))
        self.help_heading.grid(row=0,column=0,sticky='w',padx=22,pady=(18,4))
        self.help_hint=self.label(w);self.help_hint.configure(text_color='#66788A')
        self.help_hint.grid(row=1,column=0,sticky='w',padx=22,pady=(0,10))
        self.help_textbox=ctk.CTkTextbox(w,wrap='word',font=(self.ui_font,14),fg_color='white',text_color='#172B4D',border_width=1,border_color='#E3E8F0')
        self.help_textbox.grid(row=2,column=0,sticky='nsew',padx=20)
        self.help_textbox._textbox.tag_configure('heading',font=(self.ui_font,15,'bold'),foreground='#172B4D',spacing1=10,spacing3=5)
        self.help_close=self.button(w,w.destroy,width=110)
        self.help_close.grid(row=3,column=0,sticky='e',padx=20,pady=12)
        w.bind('<Escape>',lambda e:w.destroy())
        self.refresh_help_language();w.deiconify();w.lift();return w
    def open_about(self):
        if self.about_window is not None and self.about_window.winfo_exists():
            self.about_window.deiconify();self.about_window.lift();return self.about_window
        w=self.about_window=BrandedToplevel(self);w.withdraw();w.transient(self);w.configure(fg_color='#F5F7FA')
        w.geometry('460x280');w.minsize(400,250)
        from window_theme import make_brand_image
        w._body_logo=ctk.CTkImage(make_brand_image(),size=(48,48))
        ctk.CTkLabel(w,text='',image=w._body_logo).pack(pady=(20,6))
        self.about_heading=self.label(w,bold=True);self.about_heading.pack()
        self.about_body=self.label(w,justify='center',wraplength=410);self.about_body.pack(fill='both',expand=True,padx=20,pady=8)
        self.about_close=self.button(w,w.destroy,width=110);self.about_close.pack(pady=(0,14))
        w.bind('<Escape>',lambda e:w.destroy())
        self.refresh_help_language();w.deiconify();w.lift();return w
