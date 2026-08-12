import tempfile
import zipfile
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
grid_lines=dlg.figure.axes[0].get_xgridlines();assert grid_lines and grid_lines[0].get_color()=="#94a3b8" and abs(grid_lines[0].get_alpha()-.42)<1e-9
with tempfile.TemporaryDirectory() as d:
    out=Path(d)/"chart.xlsx";dlg.export_excel(out);wb=load_workbook(out)
    ws=wb["Chart Data"];preview=wb["Chart Preview"];assert ws["A1"].value=="采样点" and ws.max_row==4
    assert len(preview._images)==1 and not preview._charts and not ws._charts
    with zipfile.ZipFile(out) as archive:
        names=archive.namelist();assert any(n.startswith("xl/media/") for n in names) and not any(n.startswith("xl/charts/") for n in names)
# Saving modified settings must persist them on the parent app.
with patch("chart_dialog.messagebox.askyesnocancel",return_value=True):dlg.request_close()
assert app.chart_settings["x_name"]=="采样点"
dlg2=ChartDialog(app,data,"zh","sample.trc",app.chart_settings);dlg2.update_idletasks();dlg2.update();assert dlg2.x_name.get()=="采样点"
dlg2.destroy();print("CHART_GUI_TEST_OK")
# Large export must contain only the actual representative points used by the chart.
large=pd.DataFrame({"values":[f"{3500+i%700}mV" for i in range(80645)],"percent":[f"{i%101}%" for i in range(80645)]})
dlg3=ChartDialog(app,large,"zh","large.trc");dlg3.update_idletasks();dlg3.update();chosen,rows=dlg3.plotting_data();assert 1<len(rows)<=5000
with tempfile.TemporaryDirectory() as d:
    out=Path(d)/"large-chart.xlsx";dlg3.export_excel(out);wb=load_workbook(out,read_only=False)
    ws=wb["Chart Data"];preview=wb["Chart Preview"];assert ws.max_row==len(rows)+1
    assert len(preview._images)==1 and not preview._charts and not ws._charts
    with zipfile.ZipFile(out) as archive:
        names=archive.namelist();assert any(n.startswith("xl/media/") for n in names) and not any(n.startswith("xl/charts/") for n in names)
dlg3.destroy();app.destroy();print("LARGE_CHART_EXCEL_TEST_OK",len(rows))
