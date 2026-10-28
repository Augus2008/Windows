TEXT = {
'zh': {
'app_name':'数据提取工具','import_auto':'＋  导入并自动提取',
'supported':'支持导入：Excel、CSV、TXT、LOG、TRC','source':'数据源 / 工作表',
'source_empty':'导入后显示数据源','export_format':'导出格式','export':'⇩  导出当前结果','chart_export':'▥  生成图表并导出',
'source_trc':'TRC · 全部记录','source_log':'LOG · 全部记录','source_csv':'CSV · 全部记录','source_txt':'TXT · 全部记录','lang_zh':'中文','lang_en':'English',
'about':'关于','header_empty':'请先导入要处理的文件','header':'导入文件，自动提取 values 和 percent',
'files':'支持 Excel、CSV、TXT、LOG 与 TRC 文件','language':'语言','language_menu':'语言','clear_all':'清空全部数据','confirm_clear':'确定要清空已导入文件和全部数据吗？','confirm':'确认',
'advanced':'高级筛选（可选）','all':'全部条件 AND','any':'任一条件 OR',
'add':'＋ 添加条件','clear':'清空筛选','quick':'快速搜索全部列…',
'search':'搜索 / 应用筛选','dedupe':'去除重复行','reextract':'重新自动提取',
'restore':'恢复原始数据','columns':'列操作','choose_columns':'选择显示列…',
'show_all':'显示全部列','preview':'结果预览','rows':'筛选结果：{n:,} 行',
'preview_limit':'（仅预览前 500 行）','select_file':'选择数据文件',
'data_files':'数据文件','all_files':'所有文件','imported':'已导入\n{name}',
'about_title':'软件信息 — 数据提取工具','about_body':'版本号：v{version}\n{date}\nCopyright 2026 木头人',
'info':'提示','error':'错误','import_failed':'导入失败','export_failed':'导出失败',
'no_file':'请先导入数据文件。','condition_value':'输入筛选值','numeric_error':'大于/小于需要输入数字','no_fields':'没有识别到 values 和 percent 字段。','no_records':'没有找到同时包含 values 和 percent 的记录。','export_first':'请先导入数据并筛选。','auto_ok':'已自动提取 values / percent：{n:,} 条',
'auto_none':'未识别到 values / percent，可使用高级筛选',
'summary':'{name}  ·  原始 {source:,} 行  ·  提取 {result:,} 行',
'save_title':'保存提取结果','save_name':'提取结果','export_ok':'导出成功',
'saved':'已保存 {n:,} 行数据：\n{path}','copy_cell':'复制单元格',
'done':'完成','deduped':'已移除 {n} 行重复数据。','log_only':'仅 LOG / TRC 日志文件支持一键查看异常。',
'copy_rows':'复制所选行（Ctrl+C）','select_columns_title':'选择显示与导出列',
'select_columns':'选择需要保留的列','save_selection':'保存选择','at_least_one':'至少保留一列。',
'ops':['包含','不包含','等于','不等于','开头是','结尾是','大于','小于','非空','为空']
},
'en': {
'app_name':'Data Extraction Tool','import_auto':'+  Import & Auto Extract',
'supported':'Import: Excel, CSV, TXT, LOG, TRC','source':'Data Source / Worksheet',
'source_empty':'Import a file to show source','export_format':'Export Format','export':'Export Current Result','chart_export':'▥  Create & Export Chart',
'source_trc':'TRC · All Records','source_log':'LOG · All Records','source_csv':'CSV · All Records','source_txt':'TXT · All Records','lang_zh':'中文','lang_en':'English',
'about':'About','header_empty':'Please import the file to process first','header':'Import a file to auto-extract values and percent',
'files':'Supports Excel, CSV, TXT, LOG and TRC files','language':'Language','language_menu':'Language','clear_all':'Clear All Data','confirm_clear':'Clear the imported file and all data?','confirm':'Confirm',
'advanced':'Advanced Filters (Optional)','all':'Match All (AND)','any':'Match Any (OR)',
'add':'+ Add Condition','clear':'Clear Filters','quick':'Search all columns...',
'search':'Search / Apply','dedupe':'Remove Duplicates','reextract':'Auto Extract Again',
'restore':'Restore Original','columns':'Column Actions','choose_columns':'Choose Columns...',
'show_all':'Show All Columns','preview':'Result Preview','rows':'Filtered: {n:,} rows',
'preview_limit':' (first 500 rows only)','select_file':'Select Data File',
'data_files':'Data Files','all_files':'All Files','imported':'Imported\n{name}',
'about_title':'Software information — Data Extraction Tool','about_body':'Version: v{version}\n{date}\nCopyright 2026 木头人',
'info':'Information','error':'Error','import_failed':'Import Failed','export_failed':'Export Failed',
'no_file':'Please import a data file first.','condition_value':'Enter filter value','numeric_error':'Greater/Less Than requires a number','no_fields':'No values and percent fields were detected.','no_records':'No records containing both values and percent were found.','export_first':'Import and filter data first.','auto_ok':'Auto-extracted values / percent: {n:,}',
'auto_none':'No values / percent found. Advanced filters are available.',
'summary':'{name}  ·  Source {source:,} rows  ·  Extracted {result:,} rows',
'save_title':'Save Extracted Results','save_name':'extracted-results','export_ok':'Export Complete',
'saved':'Saved {n:,} rows to:\n{path}','copy_cell':'Copy Cell',
'done':'Done','deduped':'Removed {n} duplicate rows.','log_only':'This action is available only for LOG / TRC files.',
'copy_rows':'Copy Selected Rows (Ctrl+C)','select_columns_title':'Choose Display / Export Columns',
'select_columns':'Choose columns to keep','save_selection':'Save Selection','at_least_one':'Keep at least one column.',
'ops':['Contains','Does Not Contain','Equals','Not Equal','Starts With','Ends With','Greater Than','Less Than','Not Empty','Empty']
}}

# Batch import text; provenance data column names remain stable across languages.
TEXT['zh'].update({'import_auto': '＋  导入文件（可多选）', 'select_file': '选择数据文件（可多选；Excel 仅读首表）', 'supported': '支持单文件 / 多文件：Excel、CSV、TXT、LOG、TRC', 'batch_loading': '正在导入，请稍候', 'batch_cancel': '取消导入', 'batch_progress': '正在读取 {i}/{n}：{name}', 'batch_failed': '本次导入未完成，原数据未改变。\n{error}', 'batch_name': '{n} 个文件合并结果', 'batch_imported': '已合并 {n} 个文件\nExcel 仅读取首个工作表', 'batch_source': '全部文件合并 · Excel 首表', 'batch_ready': '多文件已合并，可统一筛选并导出一个文件', 'batch_summary': '{n} 个文件  ·  合并 {source:,} 行  ·  结果 {result:,} 行'})
TEXT['en'].update({'import_auto': '+  Import Files (Multiple)', 'select_file': 'Select files (multiple; first Excel sheet only)', 'supported': 'Single / multiple files: Excel, CSV, TXT, LOG, TRC', 'batch_loading': 'Importing, please wait', 'batch_cancel': 'Cancel Import', 'batch_progress': 'Reading {i}/{n}: {name}', 'batch_failed': 'Import was not completed. Previous data is unchanged.\n{error}', 'batch_name': 'Merged result of {n} files', 'batch_imported': 'Merged {n} files\nFirst worksheet only for each Excel file', 'batch_source': 'All files merged · First Excel sheet', 'batch_ready': 'Files merged. Filter together and export one file.', 'batch_summary': '{n} files  ·  Merged {source:,} rows  ·  Result {result:,} rows'})

TEXT['zh'].update(audit_title='批量对账 / 对账报告',audit_save='保存 JSON 报告（含本机路径）',
 audit_explain='逐文件对账；记录编号是解析后的数据记录，不是物理行号。\n排除数=源记录-当前保留；操作阶段和未应用控件见下方。报告含本机路径隐私。',
 audit_source_refused='禁止覆盖已导入的源文件',
 audit_verified='已保存 {n} 条并完整回读验证成功：{path}\n请点击“批量对账 / 对账报告”保存 JSON，含本次导出哈希与阶段。')

TEXT['en'].update(audit_title='Batch reconciliation / Audit report',
 audit_save='Save JSON report (contains local paths)',
 audit_explain='Record numbers are parsed data records, NOT physical lines. Excluded = source minus kept. See stages and pending controls below. Reports contain local path privacy.',
 audit_source_refused='Cannot overwrite an imported source file',
 audit_verified='Saved {n} rows; full read-back VERIFIED: {path}. Open Batch reconciliation / Audit report to save JSON with export hash and stage.')

TEXT['zh'].update(audit_headers='文件 | 状态 | 工作表(已读 / 有意跳过) | 源/读取记录 | 当前保留 | 排除',audit_read='读取成功')
TEXT['en'].update(audit_headers='file | status | worksheets(read / skipped) | source/read | kept | excluded',audit_read='read successfully')

# Desktop workbench vocabulary (shared keys in both locales).
TEXT['zh'].update({
'wb_preview':'UI 预览',
'wb_import':'导入文件','wb_filters':'筛选条件','wb_hide_filters':'收起条件',
'wb_pending':'筛选控件有更改，点击应用后生效',
'wb_applied':'筛选控件与已应用条件一致',
'wb_ready':'搜索或设置条件，然后点击应用',
'wb_files':'已读取文件','wb_read':'读取行数','wb_result':'当前结果',
'wb_context':'当前批次 · {n} 个文件','wb_loaded':'数据工作台 / 结果预览',
'wb_file_rows':'已读取 · {n} 行','wb_sheet':'当前工作表：{name}',
'wb_skipped':'仅读取所选表，另 {n} 张未读',
'wb_empty':'尚未导入数据\n导入文件，开始整理与筛选',
'wb_no_results':'当前结果为空\n尝试调整条件或恢复原始数据',
'wb_unverified':'导出未核验','wb_not_exported':'当前结果尚未导出',
'wb_verified':'当前结果 · 导出时回读通过',
})
TEXT['en'].update({
'wb_preview':'UI Preview',
'wb_import':'Import files','wb_filters':'Filter conditions','wb_hide_filters':'Hide conditions',
'wb_pending':'Controls changed; click Apply to use them',
'wb_applied':'Controls match the applied conditions',
'wb_ready':'Search or set conditions, then click Apply',
'wb_files':'Files read','wb_read':'Rows read','wb_result':'Current results',
'wb_context':'Current batch · {n} files','wb_loaded':'Data workspace / Result preview',
'wb_file_rows':'Read · {n} rows','wb_sheet':'Current sheet: {name}',
'wb_skipped':'Selected sheet only; {n} not read',
'wb_empty':'No data imported\nImport files to start preparing your data',
'wb_no_results':'No matching results\nAdjust filters or restore source data',
'wb_unverified':'Export not verified','wb_not_exported':'Current result not exported',
'wb_verified':'Current result · verified at export',
})

TEXT['zh']['wb_search_hint']='搜索全部列'
TEXT['en']['wb_search_hint']='Search all columns'

TEXT["zh"].update({"help":"帮助","help_guide":"使用指南","help_hint":"按操作顺序阅读；所有数据均在本机处理。","help_close":"关闭"})
TEXT["en"].update({"help":"Help","help_guide":"User guide","help_hint":"Follow the steps below. All data is processed locally.","help_close":"Close"})

# Compact sidebar and pre-export choice (not a second export implementation).
TEXT['zh'].update(supported='支持格式：Excel / CSV / TXT\nLOG / TRC',
    batch_imported='已导入 {n} 个文件\nExcel 仅读取首个工作表',
    export_choose='选择导出格式', export_choose_hint='结果将完整回读校验后保存', export_cancel='取消',
    export_hint_excel='Excel 文本保真', export_hint_csv='逗号分隔', export_hint_txt='制表符分隔')
TEXT['en'].update(supported='Formats: Excel / CSV / TXT\nLOG / TRC',
    batch_imported='Merged {n} files\nExcel: first worksheet only',
    export_choose='Choose export format', export_choose_hint='Saved only after full read-back verification', export_cancel='Cancel',
    export_hint_excel='Excel text fidelity', export_hint_csv='Comma-separated', export_hint_txt='Tab-separated')

TEXT['zh'].update(software_info='软件信息')
TEXT['en'].update(software_info='Software information')
