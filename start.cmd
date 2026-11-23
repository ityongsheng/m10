@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist logs mkdir logs
if not exist runtime mkdir runtime
set "PYTHON=python"
if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"
if exist "runtime\m10.pid" (
  for /f "usebackq delims=" %%P in ("runtime\m10.pid") do tasklist /FI "PID eq %%P" | find "%%P" >nul
  if not errorlevel 1 (
    echo m10 已在运行，浏览器地址：http://127.0.0.1:8000/
    start "" "http://127.0.0.1:8000/"
    exit /b 0
  )
  del /q "runtime\m10.pid" >nul 2>&1
)
if not exist "backend\app.py" if not exist "backend\main.py" (
  echo [阻断] backend\app.py 或 backend\main.py 尚未构建。
  echo 请先完成后端实现；当前不会伪装成启动成功。
  pause
  exit /b 2
)
set "LOG=logs\startup-%DATE:~0,4%%DATE:~5,2%%DATE:~8,2%-%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%.log"
set "LOG=%LOG: =0%"
set "ERR=%LOG%.err"
set "BACKEND=backend.main:app"
if exist "backend\app.py" set "BACKEND=backend.app:app"
powershell -NoProfile -Command "$p=Start-Process -FilePath '%PYTHON%' -ArgumentList '-m','uvicorn','%BACKEND%','--host','127.0.0.1','--port','8000' -WorkingDirectory '%CD%' -RedirectStandardOutput '%LOG%' -RedirectStandardError '%ERR%' -PassThru; Set-Content -Path 'runtime\m10.pid' -Value $p.Id"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8000/"
echo m10 已启动，日志：%LOG%
endlocal
