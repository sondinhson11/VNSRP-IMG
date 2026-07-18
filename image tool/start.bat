@echo off
title VNSRP Toolbox - Khoi dong UI
color 0C

:MENU
cls
echo ===================================================
echo        VNSRP TOOLBOX - DANG CAI DAT THU VIEN
echo ===================================================
echo Dang kiem tra / cai dat cac thu vien can thiet...
pip install rembg onnxruntime Pillow requests beautifulsoup4 >nul 2>&1

:LAUNCH
cls
echo ===================================================
echo   DANG MO CUA SO UI CHINH...
echo ===================================================
start "VNSRP Toolbox" pythonw launcher.py
goto :EOF