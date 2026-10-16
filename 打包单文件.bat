@echo off
chcp 65001 >nul
rem 公众号排版工坊 · 把离线网页版打包成零依赖单 HTML（dist\公众号排版工坊.html）
cd /d "%~dp0"
python tools\build_web_single.py
echo.
echo 打包完成，文件在 dist 目录，可任意托管或直接发送。
start "" "%~dp0dist"
pause
