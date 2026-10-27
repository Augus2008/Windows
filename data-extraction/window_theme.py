"""Consistent in-memory titlebar icons for all application-owned windows."""
import customtkinter as ctk

def make_brand_image():
    """Supersampled table/filter mark, generated in memory without asset files."""
    from PIL import Image, ImageDraw
    im=Image.new('RGBA',(152,152),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((0,0,151,151),radius=32,fill='#DBEAFE')
    d.rounded_rectangle((29,30,115,119),radius=10,fill='white',outline='#2563EB',width=7)
    d.rectangle((32,34,112,53),fill='#2563EB')
    for y in (75,96):d.line((33,y,111,y),fill='#93B4EE',width=4)
    d.line((60,56,60,114),fill='#93B4EE',width=4)
    d.polygon([(72,67),(137,67),(114,94),(114,121),(97,131),(97,94)],fill='#2563EB',outline='white',width=5)
    return im

def apply_application_icon(window):
    from PIL import Image, ImageTk
    image=make_brand_image()
    icons=tuple(ImageTk.PhotoImage(image.resize((n,n),Image.Resampling.LANCZOS),master=window)
                for n in (16,32,48,64,128))
    # CTk's delayed Windows default must not overwrite the custom icon.
    window._iconbitmap_method_called=True
    window._application_icon_images=icons
    window.iconphoto(True,*icons)
    return icons

class BrandedToplevel(ctk.CTkToplevel):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        apply_application_icon(self)
