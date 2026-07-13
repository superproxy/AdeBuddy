@echo off
chcp 65001 >nul 2>&1
REM AdeBuddy Release 脚本：打 tag + 推送，触发 GitHub Actions 自动构建发布
REM
REM 用法:
REM   release.cmd              # 交互式确认版本号（自动 patch +1）
REM   release.cmd 1.0.0        # 指定版本号
REM   release.cmd 1.0.0 -p     # 跳过确认直接推送
REM
REM 流程:
REM   1. 检查工作区干净
REM   2. 确认版本号
REM   3. 创建 git tag v<version>
REM   4. 推送 tag 到 origin
REM   5. GitHub Actions 自动构建 macOS + Windows 并发布 Release

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM ===== 颜色（Windows Terminal / ANSI） =====
set "G=[92m"
set "Y=[93m"
set "R=[91m"
set "C=[96m"
set "N=[0m"

echo %C%========================================%N%
echo %C%  AdeBuddy Release%N%
echo %C%========================================%N%

REM ===== 参数解析 =====
set "VERSION=%~1"
set "AUTO_PUSH=0"
if /i "%~2"=="-p" set "AUTO_PUSH=1"
if /i "%~2"=="--push" set "AUTO_PUSH=1"

REM ===== 1. 检查工作区 =====
git diff --quiet --exit-code >nul 2>&1
if errorlevel 1 (
    echo %Y%[release]%N% 工作区有未提交的变更，请先提交:
    git status --short
    echo %R%[release][ERROR]%N% 请先 git commit 后再 release
    exit /b 1
)
echo %G%[release]%N% 工作区干净

REM ===== 2. 确认版本号 =====
if not defined VERSION (
    REM 自动推断：取最近 tag + patch +1
    set "LATEST_TAG="
    for /f "tokens=*" %%t in ('git describe --tags --abbrev=0 2^>nul') do set "LATEST_TAG=%%t"
    if defined LATEST_TAG (
        REM 去掉前导 v
        set "VER=!LATEST_TAG:v=!"
        for /f "tokens=1,2,3 delims=." %%a in ("!VER!") do (
            set /a "PATCH=%%c+1"
            set "SUGGESTED=%%a.%%b.!PATCH!"
        )
        echo %Y%[release]%N% 上一个版本: !LATEST_TAG!
        set /p "INPUT=输入版本号 [!SUGGESTED!]: "
        if "!INPUT!"=="" (
            set "VERSION=!SUGGESTED!"
        ) else (
            set "VERSION=!INPUT!"
        )
    ) else (
        set /p "VERSION=输入版本号 (如 1.0.0): "
    )
)

if "!VERSION!"=="" (
    echo %R%[release][ERROR]%N% 版本号不能为空
    exit /b 1
)

set "TAG=v!VERSION!"
echo %G%[release]%N% 版本: !VERSION!  Tag: !TAG!

REM ===== 3. 检查 tag 是否已存在 =====
git rev-parse "!TAG!" >nul 2>&1
if not errorlevel 1 (
    echo %R%[release][ERROR]%N% Tag !TAG! 已存在，请用其他版本号
    exit /b 1
)

REM ===== 4. 确认推送 =====
if "!AUTO_PUSH!"=="0" (
    echo.
    echo %Y%[release]%N% 即将执行:
    echo   1. git tag !TAG!
    echo   2. git push origin !TAG!
    echo   3. GitHub Actions 自动构建 macOS + Windows
    echo   4. 自动创建 GitHub Release (含 .dmg / .zip / .exe)
    echo.
    set /p "CONFIRM=确认发布? [y/N]: "
    if /i not "!CONFIRM!"=="y" (
        echo %Y%[release]%N% 已取消
        exit /b 0
    )
)

REM ===== 5. 创建并推送 tag =====
echo %G%[release]%N% 创建 tag: !TAG!
git tag "!TAG!"
if errorlevel 1 (
    echo %R%[release][ERROR]%N% 创建 tag 失败
    exit /b 1
)

echo %G%[release]%N% 推送 tag: !TAG!
git push origin "!TAG!"
if errorlevel 1 (
    echo %R%[release][ERROR]%N% 推送 tag 失败，请手动执行: git push origin !TAG!
    exit /b 1
)

REM ===== 6. 完成 =====
echo.
echo %G%========================================%N%
echo %G%  Release 已触发!%N%
echo %G%========================================%N%
echo.
echo   Tag:        !TAG!
echo   Actions:    看 GitHub Actions 页面
echo   Releases:   看 GitHub Releases 页面
echo.
echo   构建完成后，Releases 页面将出现:
echo     - AdeBuddy-!VERSION!-macos.dmg / .zip
echo     - AdeBuddy-Setup-!VERSION!-x64.exe
echo.

endlocal
