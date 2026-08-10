# 开发与构建

## 技术栈
- Python 3.12
- CustomTkinter / Tkinter
- pandas、openpyxl、xlrd
- PyInstaller

## 本地运行
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

## 测试
```powershell
python test_extraction.py
python test_i18n.py
python test_gui_i18n.py
python -m py_compile app.py i18n.py i18n_runtime.py
```

## 构建单文件 EXE
```powershell
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name DataExtractionTool app.py
```
产物：`dist/DataExtractionTool.exe`。

## 目录
- `app.py`：界面与业务逻辑
- `i18n.py`：中英文资源
- `i18n_runtime.py`：语言切换运行时
- `test_*.py`：提取、语言和 GUI 回归测试

## 代码约定
- 用户界面文字应进入 `i18n.py`。
- 不将 `.grid()` / `.pack()` 返回值赋给控件变量。
- 新格式应保留原始行，解析失败不得静默丢数据。
- 新版本必须更新版本号、CHANGELOG 和文档。
