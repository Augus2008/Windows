using System;

namespace Minesweeper
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("=======================================");
            Console.WriteLine("         C# 扫雷游戏");
            Console.WriteLine("=======================================");
            Console.WriteLine();
            
            int width = 9;
            int height = 9;
            int mineCount = 10;
            
            var game = new MinesweeperGame(width, height, mineCount);
            game.Play();
        }
    }

    public class MinesweeperGame
    {
        private int width;
        private int height;
        private int mineCount;
        private Cell[,] board;
        private bool gameOver;
        private bool firstClick;
        private int revealedCount;

        public MinesweeperGame(int width, int height, int mineCount)
        {
            this.width = width;
            this.height = height;
            this.mineCount = mineCount;
            this.board = new Cell[height, width];
            this.gameOver = false;
            this.firstClick = true;
            this.revealedCount = 0;
            
            InitializeBoard();
        }

        private void InitializeBoard()
        {
            for (int y = 0; y < height; y++)
            {
                for (int x = 0; x < width; x++)
                {
                    board[y, x] = new Cell();
                }
            }
        }

        private void PlaceMines(int excludeX, int excludeY)
        {
            Random random = new Random();
            int placed = 0;
            
            while (placed < mineCount)
            {
                int x = random.Next(width);
                int y = random.Next(height);
                
                if (Math.Abs(x - excludeX) <= 1 && Math.Abs(y - excludeY) <= 1)
                    continue;
                
                if (!board[y, x].IsMine)
                {
                    board[y, x].IsMine = true;
                    placed++;
                }
            }
            
            for (int y = 0; y < height; y++)
            {
                for (int x = 0; x < width; x++)
                {
                    if (!board[y, x].IsMine)
                    {
                        board[y, x].NeighborMines = CountNeighborMines(x, y);
                    }
                }
            }
        }

        private int CountNeighborMines(int x, int y)
        {
            int count = 0;
            for (int dy = -1; dy <= 1; dy++)
            {
                for (int dx = -1; dx <= 1; dx++)
                {
                    if (dx == 0 && dy == 0) continue;
                    
                    int nx = x + dx;
                    int ny = y + dy;
                    
                    if (nx >= 0 && nx < width && ny >= 0 && ny < height)
                    {
                        if (board[ny, nx].IsMine) count++;
                    }
                }
            }
            return count;
        }

        public void Play()
        {
            while (!gameOver)
            {
                DrawBoard();
                
                Console.WriteLine();
                Console.WriteLine("操作说明:");
                Console.WriteLine("  输入格式: x y [f]");
                Console.WriteLine("  例如: 4 5    (揭开第4列第5行)");
                Console.WriteLine("  例如: 4 5 f  (标记/取消标记第4列第5行)");
                Console.WriteLine();
                Console.Write("请输入操作: ");
                
                string? input = Console.ReadLine();
                if (string.IsNullOrWhiteSpace(input)) continue;
                
                ProcessInput(input);
                
                CheckWin();
            }
        }

        private void ProcessInput(string input)
        {
            string[] parts = input.Split(' ', StringSplitOptions.RemoveEmptyEntries);
            
            if (parts.Length < 2) return;
            
            if (!int.TryParse(parts[0], out int x) || !int.TryParse(parts[1], out int y))
            {
                Console.WriteLine("输入无效！请使用数字。");
                Console.ReadKey();
                return;
            }
            
            x--; y--;
            
            if (x < 0 || x >= width || y < 0 || y >= height)
            {
                Console.WriteLine("坐标超出范围！");
                Console.ReadKey();
                return;
            }

            bool flag = parts.Length > 2 && parts[2].ToLower() == "f";
            
            if (flag)
            {
                ToggleFlag(x, y);
            }
            else
            {
                Reveal(x, y);
            }
        }

        private void ToggleFlag(int x, int y)
        {
            if (board[y, x].IsRevealed) return;
            board[y, x].IsFlagged = !board[y, x].IsFlagged;
        }

        private void Reveal(int x, int y)
        {
            if (board[y, x].IsRevealed || board[y, x].IsFlagged) return;
            
            if (firstClick)
            {
                PlaceMines(x, y);
                firstClick = false;
            }
            
            board[y, x].IsRevealed = true;
            revealedCount++;
            
            if (board[y, x].IsMine)
            {
                gameOver = true;
                DrawBoard();
                Console.WriteLine();
                Console.WriteLine("砰！你踩到地雷了！游戏结束！");
                Console.WriteLine();
                ShowAllMines();
                return;
            }
            
            if (board[y, x].NeighborMines == 0)
            {
                RevealNeighbors(x, y);
            }
        }

        private void RevealNeighbors(int x, int y)
        {
            for (int dy = -1; dy <= 1; dy++)
            {
                for (int dx = -1; dx <= 1; dx++)
                {
                    if (dx == 0 && dy == 0) continue;
                    
                    int nx = x + dx;
                    int ny = y + dy;
                    
                    if (nx >= 0 && nx < width && ny >= 0 && ny < height)
                    {
                        if (!board[ny, nx].IsRevealed && !board[ny, nx].IsFlagged)
                        {
                            board[ny, nx].IsRevealed = true;
                            revealedCount++;
                            
                            if (board[ny, nx].NeighborMines == 0)
                            {
                                RevealNeighbors(nx, ny);
                            }
                        }
                    }
                }
            }
        }

        private void CheckWin()
        {
            if (revealedCount == width * height - mineCount)
            {
                gameOver = true;
                DrawBoard();
                Console.WriteLine();
                Console.WriteLine("恭喜你！成功排除所有地雷！");
            }
        }

        private void ShowAllMines()
        {
            for (int y = 0; y < height; y++)
            {
                for (int x = 0; x < width; x++)
                {
                    if (board[y, x].IsMine)
                    {
                        board[y, x].IsRevealed = true;
                    }
                }
            }
            DrawBoard();
        }

        private void DrawBoard()
        {
            Console.Clear();
            Console.WriteLine("=======================================");
            Console.WriteLine("         C# 扫雷游戏");
            Console.WriteLine("=======================================");
            Console.WriteLine();
            
            Console.Write("   ");
            for (int x = 0; x < width; x++)
            {
                Console.Write($" {x + 1}");
            }
            Console.WriteLine();
            
            Console.Write("  +");
            for (int x = 0; x < width; x++)
            {
                Console.Write("--");
            }
            Console.WriteLine("-+");
            
            for (int y = 0; y < height; y++)
            {
                Console.Write($"{y + 1,2}|");
                for (int x = 0; x < width; x++)
                {
                    Console.Write(" ");
                    Console.Write(GetCellDisplay(board[y, x]));
                }
                Console.WriteLine(" |");
            }
            
            Console.Write("  +");
            for (int x = 0; x < width; x++)
            {
                Console.Write("--");
            }
            Console.WriteLine("-+");
            
            Console.WriteLine();
            Console.WriteLine($"地雷数: {mineCount}  |  已揭开: {revealedCount}  |  剩余: {width * height - mineCount - revealedCount}");
        }

        private string GetCellDisplay(Cell cell)
        {
            if (cell.IsFlagged) return "F";
            if (!cell.IsRevealed) return "#";
            if (cell.IsMine) return "*";
            if (cell.NeighborMines == 0) return ".";
            return cell.NeighborMines.ToString();
        }
    }

    public class Cell
    {
        public bool IsMine { get; set; }
        public bool IsRevealed { get; set; }
        public bool IsFlagged { get; set; }
        public int NeighborMines { get; set; }
    }
}
