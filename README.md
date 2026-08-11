# Windows 工具集

Windows 桌面工具与示例项目集合。当前仓库以 **数据提取工具** 为主要维护项目。

## 项目一览

| 项目 | 状态 | 说明 |
|---|---|---|
| [数据提取工具](data-extraction/) | 稳定维护 | 从 Excel、CSV、TXT、LOG、TRC 中读取、筛选、提取和导出数据；LOG/TRC 支持导入即提取 `values` 与 `percent`。 |
| [C# 控制台扫雷](Minesweeper/) | 示例 | .NET 8 控制台交互示例。 |

## 数据提取工具

当前稳定版：**v0.12.2**
[下载 Windows EXE](https://github.com/Augus2008/Windows/releases/tag/data-extraction-v0.12.2) · [项目主页](data-extraction/README.md) · [文档中心](data-extraction/docs/README.md)

主要能力：
- Excel、CSV、TXT、LOG、TRC 本地读取。
- 导入日志后自动筛出 `values` 与 `percent`。
- 中文 / English、复制、筛选、去重和 Excel / CSV / TXT 导出。
- GitHub Actions 在 Windows 环境完成测试、单文件 EXE 构建和启动检查。

## 贡献与支持

- [更新日志](CHANGELOG.md)
- [贡献指南](CONTRIBUTING.md)
- [安全策略](SECURITY.md)
- [支持说明](SUPPORT.md)
- [行为准则](CODE_OF_CONDUCT.md)
- 许可证：待维护者确定

> 请勿在 Issue、截图、日志或样本中提交密码、Token、私钥、设备序列号或其他敏感数据。
