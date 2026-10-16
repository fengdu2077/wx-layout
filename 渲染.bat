@echo off
chcp 65001 >nul
if "%~1"=="" goto :noarg
python "%~dp0render.py" "%~1" --open
if errorlevel 1 pause
goto :end
:noarg
echo.
echo  请把 .md 文件用鼠标拖到本脚本图标上，不要直接双击。
echo.
pause
:end
