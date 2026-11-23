@echo off
setlocal
cd /d "%~dp0"
if not exist "runtime\m10.pid" (
  echo 未找到本项目运行记录。
  exit /b 0
)
for /f "usebackq delims=" %%P in ("runtime\m10.pid") do taskkill /PID %%P /T /F >nul 2>&1
del /q "runtime\m10.pid" >nul 2>&1
echo m10 已停止。
endlocal
