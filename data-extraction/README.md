# 数据提取工具

[![Windows Build](https://github.com/Augus2008/Windows/actions/workflows/build-data-extraction.yml/badge.svg)](https://github.com/Augus2008/Windows/actions/workflows/build-data-extraction.yml)
[![Release](https://img.shields.io/github/v/release/Augus2008/Windows?filter=data-extraction-v*&label=stable)](https://github.com/Augus2008/Windows/releases/tag/data-extraction-v0.12.1)

面向 Windows 的本地数据提取程序，重点用于从 LOG / TRC 中快速提取 `values` 与 `percent`。

## 下载

当前稳定版：**v0.12.1**
[前往 GitHub Release 下载 DataExtractionTool.exe](https://github.com/Augus2008/Windows/releases/tag/data-extraction-v0.12.1)

无需安装 Python。程序为单文件 EXE，首次启动可能需要数秒完成运行时解压。

## 核心流程

1. 点击“导入并自动提取”。
2. 选择 Excel、CSV、TXT、LOG 或 TRC。
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
