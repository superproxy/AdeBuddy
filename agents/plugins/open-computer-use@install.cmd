@echo off
chcp 65001 > nul
echo ========================================
echo   Open Computer Use Install Script
echo ========================================
echo.

echo [1/3] Installing open-computer-use via npm...
npm i -g open-computer-use
if %errorlevel% neq 0 (
    echo [ERROR] npm install failed
    pause
    exit /b 1
)
echo [OK] open-computer-use installed successfully
echo.

echo [2/3] Installing open-computer-use skill...
npx -y skills add iFurySt/open-computer-use --skill open-computer-use -g
if %errorlevel% neq 0 (
    echo [WARN] skill install failed, please install manually:
    echo   npx skills add iFurySt/open-computer-use --skill open-computer-use -g
) else (
    echo [OK] Skill installed successfully
)
echo.

echo [3/3] Setup open-computer-use...
open-computer-use setup
if %errorlevel% neq 0 (
    echo [WARN] setup failed, you may need to run manually:
    echo   open-computer-use setup
) else (
    echo [OK] Setup completed
)
echo.

echo ========================================
echo   Install Complete!
echo ========================================
echo.
echo MCP configuration to add to your mcp.json:
echo   "open-computer-use": {
echo     "command": "npx",
echo     "args": ["-y", "open-computer-use", "mcp"]
echo   }
echo.
echo Or run plugin manager:
echo   python scripts\plugin-manager.py install agents\plugins\computer-use.plugin.json
echo.
pause
