# 数据提取（Windows 桌面版）

用于导入、预览、筛选、去重并导出 Excel、CSV、TXT 数据。

## 功能
- 导入 `.xlsx` / `.xls` / `.csv` / `.txt`
- Excel 工作表选择，常见中文编码 CSV 自动识别
- 全列关键词搜索与多条件 AND/OR 筛选
- 包含、等于、前后缀、大小比较、空值判断等条件
- 按需选择显示/导出的列、去重、预览前 500 行
- 导出 Excel、CSV、制表符分隔 TXT

## Windows 开发运行
```bat
py -m pip install -r requirements.txt
py app.py
```

## 打包 EXE
双击 `build_windows.bat`，或运行：
```bat
py -m pip install pyinstaller
py -m PyInstaller --noconfirm --clean --windowed --name "数据提取" app.py
```
产物为 `dist/数据提取/数据提取.exe`。

## LOG 日志支持
- 导入 `.log` 串口/设备日志并解析为行号、日期时间、运行时间、级别、模块、日志内容和原始行。
- 自动识别 ERROR / WARN / OK / INFO，支持“一键仅看异常”。

## v0.3.0 交互改进
- 无分隔符 TXT 自动按“行号 + 文本内容”载入，整行支持搜索和条件筛选。
- 表格支持多行选择、Ctrl+C 复制、右键复制单元格或所选行。
- 强化 AND/OR 状态对比；列操作改为下拉菜单。

## v0.5.0 LOG 字段提取
- LOG 导入后自动提取 `status:`、`values:`、`percent:` 后的值为独立列。
- 可在列操作中仅保留这些列后导出 Excel、CSV 或 TXT。

## v0.6.0 TRC 追踪日志支持
- 支持 `.trc` 大型设备追踪日志。
- 自动拆分时间、计数器、序号、上下文、任务、标志、模块、级别、日志内容和原始行。
- 自动提取 status、values、percent、vol、user、width、height 等常见字段。
- “仅看异常”兼容 TRC 的 E/W/F 级别。

## v0.7.0 导入即提取
- 导入 LOG / TRC 后自动筛出同时包含 values 与 percent 的记录。
- 结果默认仅显示 values、percent 两列，可直接导出，无需手工设置筛选条件。
- 高级筛选保留为可选功能，并可随时“重新自动提取”。

## v0.8.0 界面与信息完善
- 工具名称统一为“数据提取工具”，标题栏与界面显示版本 v0.8.0。
- 关于区域显示版本号、编译日期和 Copyright 2026 ehisuy。
- “工作表”改为“数据源 / 工作表”：Excel 可选择工作表，CSV/TXT/LOG/TRC 显示对应全部记录。
- AND/OR 切换改为统一青绿色与深灰蓝配色。

## v0.9.0 中文 / English
- 右上角改为“语言 / Language”，支持中文与 English 即时切换，无需重启。
- “关于 / About”改为可点击按钮，点击后弹出版本、编译日期与版权信息。
- 主界面、筛选条件、列操作、右键复制、导入导出和提示弹窗均支持双语。
