@echo off
chcp 65001 >nul
echo.
echo  公众号排版工坊 · 本地可视化工作台
echo  启动后会自动打开浏览器；关闭本窗口即停止服务。
echo.
python "%~dp0serve.py"
if errorlevel 1 pause
