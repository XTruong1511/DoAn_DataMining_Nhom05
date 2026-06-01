@echo off
chcp 65001 > nul
title IT Job Market Analytics System
color 0A

echo ========================================
echo    IT JOB MARKET ANALYTICS SYSTEM
echo ========================================
echo.

REM =====================================================
REM Install dependencies
REM =====================================================

echo [1/4] Kiem tra dependencies...
pip show pandas > nul 2>&1
if errorlevel 1 (
    echo Dang cai dat dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Khong the cai dat dependencies!
        pause
        exit /b 1
    )
) else (
    echo [OK] Dependencies da duoc cai dat
)
echo.

REM =====================================================
REM Run Data Pipeline
REM =====================================================

echo [2/4] Chay pipeline xu ly du lieu...
python run_pipeline.py
if errorlevel 1 (
    echo.
    echo [ERROR] Loi khi chay pipeline!
    pause
    exit /b 1
)
echo [OK] Pipeline hoan tat
echo.

REM =====================================================
REM Train Model
REM =====================================================

echo [3/4] Train model du doan luong...
python train_model.py
if errorlevel 1 (
    echo.
    echo [ERROR] Loi khi train model!
    pause
    exit /b 1
)
echo [OK] Model training hoan tat
echo.

REM =====================================================
REM Start Services
REM =====================================================

echo [4/4] Khoi dong cac services...
echo.

REM Start API Server
start "IT_API_SERVER" cmd /k "cd api && uvicorn main:app --reload --host 127.0.0.1 --port 8000"
echo   - API Server da khoi dong tren port 8000

timeout /t 3 /nobreak > nul

REM Start Dashboard
start "IT_DASHBOARD" cmd /k "streamlit run dashboard/app.py"
echo   - Dashboard da khoi dong tren port 8501

timeout /t 2 /nobreak > nul

REM =====================================================
REM System Started
REM =====================================================

cls
echo ========================================
echo      HE THONG DA KHOI DONG!
echo ========================================
echo.
echo API Server:
echo   http://127.0.0.1:8000
echo.
echo API Documentation:
echo   http://127.0.0.1:8000/docs
echo.
echo Dashboard:
echo   http://127.0.0.1:8501
echo.
echo ========================================
echo.
echo Nhan phim bat ky de DUNG he thong...
pause > nul

REM =====================================================
REM Stop Services
REM =====================================================

echo.
echo Dang dung cac services...

REM Kill API server
for /f "tokens=2" %%i in ('tasklist /fi "windowtitle eq IT_API_SERVER*" /nh 2^>nul') do (
    taskkill /pid %%i /f > nul 2>&1
)

REM Kill Dashboard
for /f "tokens=2" %%i in ('tasklist /fi "windowtitle eq IT_DASHBOARD*" /nh 2^>nul') do (
    taskkill /pid %%i /f > nul 2>&1
)

REM Kill any remaining uvicorn/streamlit processes
taskkill /f /im uvicorn.exe > nul 2>&1
taskkill /f /im streamlit.exe > nul 2>&1

echo Da dung tat ca services.
echo.
pause