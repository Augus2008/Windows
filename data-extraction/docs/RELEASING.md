# 发布流程

1. 确认 `main` 工作区干净。
2. 更新 `APP_VERSION`、`BUILD_DATE`、README 与 CHANGELOG。
3. 运行提取、国际化和 GUI 测试。
4. 提交变更并创建标签：
```bash
git tag -a data-extraction-vX.Y.Z -m "数据提取工具 vX.Y.Z"
git push origin main
git push origin data-extraction-vX.Y.Z
```
5. GitHub Actions 在 `windows-latest`：
   - 安装依赖
   - 运行自动提取测试
   - 运行中英文 GUI 测试
   - 构建单文件 EXE
   - 启动冒烟测试
   - 上传 Artifact 与 Release 附件
6. 检查 Release 名称、说明、附件和 SHA-256。
7. 稳定版将 `prerelease` 设为 false，并标记 Latest。

## 回滚
不要移动已发布标签。发现问题时修复后发布补丁版本，如 `v0.11.1`。
