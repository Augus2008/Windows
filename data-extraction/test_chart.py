import pandas as pd
from chart_dialog import parse_numeric_unit, analyze_series, convert_series
cases={"4184mV":(4184.0,"mV"),"4.184 V":(4.184,"V"),"100%":(100.0,"%"),"-12.5°C":(-12.5,"°C"),"1,250mA":(1250.0,"mA"),"1.2e3Pa":(1200.0,"Pa")}
for raw,expected in cases.items(): assert parse_numeric_unit(raw)==expected,(raw,parse_numeric_unit(raw))
assert parse_numeric_unit("bad")== (None,"")
parsed,unit=analyze_series(pd.Series(["4184mV","4.17V","bad",""]))
assert unit=="mV"
assert convert_series(parsed,unit,"mV")[:2]==[4184.0,4170.0]
assert convert_series(parsed,unit,"V")[:2]==[4.184,4.17]
print("CHART_PARSER_TEST_OK")
for raw in ("inf", "-inf", "nan", "1e999V", float('inf'), float('nan')):
    assert parse_numeric_unit(raw) == (None, ''), raw
assert convert_series([(1.0, 'A'), (2.0, 'V')], 'V', 'mV') == [None, 2000.0]
assert convert_series([(1.0, 'Pa')], 'Pa', 'V') == [None]
from test_chart_full import make_dialog
frame = pd.DataFrame({'values': ['1V', 'bad', None], 'percent': ['bad', None, '3%']})
dialog = make_dialog(frame)
_, rows = dialog.plotting_data()
assert len(rows) == 3 and [r[2] for r in rows] == [0, 1, 2]
assert rows[1][1] == [None, None]
print('CHART_FULL_ROWS_TEST_OK')
