# 数据提取工具

[![Windows Build](https://github.com/Augus2008/Windows/actions/workflows/build-data-extraction.yml/badge.svg)](https://github.com/Augus2008/Windows/actions/workflows/build-data-extraction.yml)
[![Release](https://img.shields.io/github/v/release/Augus2008/Windows?filter=data-extraction-v*&label=stable)](https://github.com/Augus2008/Windows/releases/tag/data-extraction-v0.12.4)

面向 Windows 的本地数据提取程序，重点用于从 LOG / TRC 中快速提取 `values` 与 `percent`。

## 下载

当前源码版本：**v0.13.0**（批量导入；尚未发布新版 Windows EXE）

以下下载仍为已发布的 v0.12.4，不包含本次新功能。
[前往 GitHub Release 下载 DataExtractionTool.exe](https://github.com/Augus2008/Windows/releases/tag/data-extraction-v0.12.4)

无需安装 Python。程序为单文件 EXE，首次启动可能需要数秒完成运行时解压。

## 核心流程

1. 点击“导入文件（可多选）”。
2. 选择一个或多个 Excel、CSV、TXT、LOG 或 TRC。
3. 对包含目标字段的日志，自动生成 `values`、`percent` 两列。
4. 预览、复制、去重或高级筛选。
5. 导出 Excel、CSV 或 TXT。

## 主要特性
- LOG / TRC 导入即提取 `values` 与 `percent`。
- Excel 工作表切换；CSV/TXT 编码与分隔符兼容。
- 多条件 AND / OR 筛选与整表关键词搜索。
- 复制单元格、复制多行、选择导出列、去重。
- 中文 / English 即时切换。
- 清空全部数据后恢复初始状态。
- 图表设置与实时预览：可独立或联合绘制 values / percent，自定义名称、单位、横轴与图表类型。
- 图表内部自动拆分纯数值和单位，支持常见电压/电流单位换算，导出 PNG / PDF / SVG。
- 全程本地处理，不主动上传数据。

## 文档
- [用户指南](docs/USER_GUIDE.md)
- [格式与解析规则](docs/FORMATS.md)
- [开发与构建](docs/DEVELOPMENT.md)
- [发布流程](docs/RELEASING.md)
- [故障排查](docs/TROUBLESHOOTING.md)
- [更新日志](../CHANGELOG.md)

## 校验
Release 页提供正式构建。下载后可使用 SHA-256 校验文件完整性。

## 许可证
许可证尚未确定；如需复用、分发或商用，请先联系维护者。

## 多文件批量筛选（v0.13.0）

- 点击“导入文件（可多选）”，用 Ctrl/Shift 同时选择多个文件。每次成功导入替换当前数据，不追加到上次结果。
- 支持 Excel、CSV、TXT、LOG、TRC 混合导入；Excel 每个文件只读第一个工作表。单文件 Excel 仍可切换工作表。
- 按列名对齐合并，缺少的列留空，保留输入顺序和全部行；日志中的 values/percent 自动补充，不静默丢掉其他记录。
- 新增“来源文件”列；输入已有同名列则自动改用“来源文件_2”等名称，不覆盖原数据。同名文件来自不同目录时用完整路径区分。来源列名不随界面语言变化。
- 合并后统一使用 AND/OR、多条件和关键词筛选，再导出一个 Excel/CSV/TXT 文件。来源列也可用于筛选和导出。
- “重新自动提取”聚焦同时含 values/percent 的行并保留来源列；“恢复原始数据”回到完整合并数据。去重包含来源列，不会自动删除不同文件的相同行。
- 后台读取避免界面冻结；任一文件读取失败或取消时保留原数据，不悄悄跳过坏文件。取消在当前文件读取结束后生效。
- 预览仍只显示前 500 行，筛选和导出使用完整结果。批量数据存于内存，超大文件建议分批处理。
