# C# 控制台扫雷

一个 .NET 8 控制台扫雷示例项目，保留在本仓库作为 C# 基础交互程序示例。

## 运行
```powershell
cd Minesweeper
dotnet run
```

## 操作
- 输入 `x y`：揭开第 x 列、第 y 行。
- 输入 `x y f`：标记或取消标记格子。
- 默认棋盘：9 × 9，10 个地雷。
- 首次揭开及相邻区域不会布雷。

## 项目结构
- `Program.cs`：游戏逻辑与控制台交互。
- `Minesweeper.csproj`：.NET 8 项目配置。
