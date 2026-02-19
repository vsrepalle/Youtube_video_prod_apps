@echo off
title YouTube Multi-Channel Automation 2026
cls
echo ========================================
echo   🚀 STARTING VIDEO GENERATION
echo ========================================
python main_controller.py

echo.
echo ========================================
echo   📦 STARTING BATCH UPLOAD
echo ========================================
python batch_manager.py

echo.
echo ========================================
echo   ✅ ALL TASKS COMPLETED
echo ========================================
pause

@echo off
:: ... existing render and upload commands ...
python dashboard.py
pause