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
from chart_dialog import representative_indices, MAX_CHART_POINTS
size=80645
values=[float(i%1000) for i in range(size)];values[12345]=-9999.0;values[67890]=9999.0
percent=[float((i//100)%101) for i in range(size)]
indices=representative_indices([values,percent])
assert len(indices)<=MAX_CHART_POINTS
assert indices[0]==0 and indices[-1]==size-1
assert 12345 in indices and 67890 in indices
assert indices==sorted(set(indices))
print("CHART_DOWNSAMPLE_TEST_OK",len(indices))
