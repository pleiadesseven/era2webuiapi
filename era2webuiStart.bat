@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd era2webui

start python add_prompt編集ボタン.py
start python imageviewer.py

:variChoice
echo バリアントを選択
echo [1] eratohoYM
echo [2] eraTW
echo [3] eraim@scgpro
set /p variChoice="(1-3): "
if "!variChoice!"=="1" start python era2webui.py
if "!variChoice!"=="2" start python era2webuiimas.py
if "!variChoice!"=="3" start python era2webuiTW.py





REM スクリプトの終了
echo 処理を終了します。