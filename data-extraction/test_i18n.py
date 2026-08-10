from i18n import TEXT
required={"app_name","import_auto","supported","source","source_empty","export_format","export","about","header","files","language","advanced","all","any","add","clear","quick","search","dedupe","reextract","restore","columns","choose_columns","show_all","preview","rows","preview_limit","about_title","about_body","ops"}
assert set(TEXT)=={"zh","en"}
for lang in TEXT:
    missing=required-set(TEXT[lang]);assert not missing,(lang,missing)
    assert len(TEXT[lang]["ops"])==10
assert TEXT["zh"]["app_name"]=="数据提取工具"
assert TEXT["en"]["app_name"]=="Data Extraction Tool"
print("I18N_RESOURCE_TEST_OK")
