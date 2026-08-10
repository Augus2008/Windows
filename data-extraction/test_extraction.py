import re
samples = [
    "[14:22:02.314] NPMA/I : values:4184mV percent:100%",
    "[14:22:03.325] NPMA/I : values:4183mV percent:99%",
]
result=[]
for line in samples:
    v=re.search(r"(?i)(?<![A-Za-z0-9_])values\s*[:=]\s*([^\s,;]+)",line)
    p=re.search(r"(?i)(?<![A-Za-z0-9_])percent\s*[:=]\s*([^\s,;]+)",line)
    if v and p:result.append((v.group(1),p.group(1)))
assert result == [("4184mV","100%"),("4183mV","99%")], result
print("EXTRACTION_TEST_OK")
