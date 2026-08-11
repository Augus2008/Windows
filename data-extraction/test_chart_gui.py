import tempfile
from pathlib import Path
import pandas as pd
from app import App
from chart_dialog import ChartDialog
app=App();app.update_idletasks();app.update()
data=pd.DataFrame({"values":["4184mV","4.17V","bad"],"percent":["100%","98%","97%"]})
dlg=ChartDialog(app,data,"zh","sample.trc");dlg.update_idletasks();dlg.update()
assert set(dlg.series)=={"values","percent"}
assert dlg.axis_label(dlg.series["values"])=="数值（mV）"
valid,skipped=dlg.draw();assert valid==3 and skipped==0
# Single-series mode and unit conversion must also render.
dlg.series["percent"]["enabled"].set(False);dlg.series["values"]["unit"].set("V")
valid,skipped=dlg.draw();assert valid==2 and skipped==1
with tempfile.TemporaryDirectory() as d:
    out=Path(d)/"chart.png";dlg.figure.savefig(out,dpi=100);assert out.stat().st_size>1000
dlg.destroy();app.destroy();print("CHART_GUI_TEST_OK")
