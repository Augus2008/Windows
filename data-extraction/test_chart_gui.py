import tempfile
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from openpyxl import load_workbook
from app import App
from chart_dialog import ChartDialog
app=App();app.update_idletasks();app.update()
data=pd.DataFrame({"values":["4184mV","4.17V","bad"],"percent":["100%","98%","97%"]})
dlg=ChartDialog(app,data,"zh","sample.trc");dlg.update_idletasks();dlg.update()
assert set(dlg.series)=={"values","percent"} and dlg.axis_label(dlg.series["values"])=="数值（mV）"
dlg.x_name.set("采样点");valid,skipped=dlg.draw();assert valid==3 and skipped==0
legend=dlg.figure.axes[0].get_legend();assert legend is not None and legend._loc==9
with tempfile.TemporaryDirectory() as d:
    out=Path(d)/"chart.xlsx";dlg.export_excel(out);wb=load_workbook(out)
    ws=wb["Chart Data"];assert ws["A1"].value=="采样点" and len(ws._charts)==1 and ws.max_row==4
# Saving modified settings must persist them on the parent app.
with patch("chart_dialog.messagebox.askyesnocancel",return_value=True):dlg.request_close()
assert app.chart_settings["x_name"]=="采样点"
dlg2=ChartDialog(app,data,"zh","sample.trc",app.chart_settings);dlg2.update_idletasks();dlg2.update();assert dlg2.x_name.get()=="采样点"
dlg2.destroy();app.destroy();print("CHART_GUI_TEST_OK")
