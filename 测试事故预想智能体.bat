@echo off
echo ========================================
echo 事故预想智能体 - 快速测试
echo ========================================
echo.

echo 步骤1: 检查服务状态...
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | findstr "aperag"
echo.

echo 步骤2: 打开浏览器测试页面...
echo.
echo 请手动打开浏览器访问以下地址:
echo.
echo [1] 智能体列表页:
echo     http://localhost:3000/workspace/agents
echo.
echo [2] 事故预想专家工作台:
echo     http://localhost:3000/workspace/agents/specific/accident_deduction
echo.

echo 步骤3: 测试功能...
echo.
echo 在工作台页面的"任务指令"文本框中输入:
echo     #1主变重瓦斯保护动作事故预想
echo.
echo 然后点击"发送指令"按钮
echo.

echo ========================================
echo 按任意键自动打开浏览器...
pause >nul

start http://localhost:3000/workspace/agents

echo.
echo 浏览器已打开！
echo.
echo 在智能体列表中找到:
echo   - 标题: "The Accident Deduction Agent (事故预想专家)"
echo   - 图标: 粉色警告三角形
echo   - 点击"激活智能体"按钮
echo.
pause
