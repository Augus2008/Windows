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
