# 数据提取工具

[![Windows Build](https://github.com/Augus2008/Windows/actions/workflows/build-data-extraction.yml/badge.svg)](https://github.com/Augus2008/Windows/actions/workflows/build-data-extraction.yml)
[![Release](https://img.shields.io/github/v/release/Augus2008/Windows?filter=data-extraction-v*&label=stable)](https://github.com/Augus2008/Windows/releases/tag/data-extraction-v0.12.4)

面向 Windows 的本地数据提取程序，重点用于从 LOG / TRC 中快速提取 `values` 与 `percent`。

## 下载

当前基线：**v0.14.0**（批量对账 EXE 已独立交付）；当前工作树正在试作浅色数据工作台 UI，**该界面改版尚未构建 EXE**。

v0.13.0、v0.14.0 已分别独立交付，但尚未发布对应 GitHub Release。

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

## 批量对账与验证导出（v0.14.0）

新增逐文件记录统计、来源记录编号、阶段操作对账与报告保存；导出后完整回读比对行列及文本内容。请阅读[对账与校验说明](docs/AUDIT.md)，了解首表范围、解析行数口径、文本保真导出和隐私边界。

## UI 预览版
浅色数据工作台第一版仅用于评审。截图来自远端 Xvfb 实际 Tk 程序，使用合成样例，不代表 Windows 原生字体和缩放已验收。当前挂载目录的 EXE 不受这轮源码预览影响。

## v0.15.0 UI预览构建
基于0.14.0数据处理核心，新增浅色工作台、折叠筛选、真实文件清单、核验状态及表格＋漏斗Logo，移除品牌副标题。标题保留UI预览标记；不等于GitHub正式Release。

## v0.15.1 UI预览修复
条件列、运算符菜单和AND/OR选择后立即更新待应用提示，不自动执行筛选。用户仍需点击应用；此前已导出数据的核验状态保持指向当前实际结果。修复分支独立构建，不发布Release。

## 最新工作树布局修订（尚未构建）
基于已交付0.15.1，移除侧栏重复品牌、上移数据源、统计居中，并加入右上帮助（指南／语言／关于）；统一主窗口和应用自建弹窗图标，新增ICO供EXE使用。此轮仍是未提交源码预览，临时目录现有EXE不包含本次修订。

## 0.15.2 UI预览构建
本构建纳入顶部帮助、统计居中、数据源上移和主窗口及自建弹窗统一Logo。数据处理逻辑基于0.15.1，独立分支构建，不发布Release。

## 最新界面交互修订（源码预览，未构建）
侧栏数据源说明居中并压缩格式说明；导出格式合入导出按钮，点击后先弹格式选择，再选保存位置；帮助改为原生顶部菜单栏，保留系统标题栏；移除主区顶部重复提示。已交付0.15.2 EXE保持不变。

## 0.15.3 UI预览构建
包含侧栏说明居中和紧凑格式说明、导出前格式选择、顶部原生帮助菜单、主区重复提示移除。独立Windows CI构建，不发布Release；核心数据处理沿用0.15.2。

## 0.15.4 UI预览
格式选择窗收紧为440×270，三个格式选项文字居中；标题、说明和取消按钮位置保持不变，补齐悬停事件兼容。独立构建，不发布Release。
