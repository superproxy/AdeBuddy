"""IDE 安装/卸载模块。

支持两种安装方式：
- CLI：通过 brew / npm / script（curl|bash）/ app_cli（App 内 CLI 建软链）/ manual（下载页）安装
- App：通过 brew install --cask / brew uninstall --cask，或下载 dmg

各 IDE 的安装元数据在 IDE_INSTALL_META 中定义：
    cli_install: {method: brew|npm|script|app_cli|manual, package?, script_url?, app_path?, cli_relpath?, link_name?, url?}
    app_install: {method: cask|manual, package?, url?}
    homepage: 官方主页

app_cli method：CLI 随 App 分发（如 Cursor.app 内的 cursor 命令），通过建软链
    <link_dir>/<link_name> → <app_path>/<cli_relpath> 使其出现在 PATH 上。
    link_dir 优先 /usr/local/bin，不可写则回退 ~/.local/bin。
"""
import shutil
import subprocess
import sys
from pathlib import Path


# ===== IDE 安装元数据 =====
# cli_install: 安装 CLI 的方式（brew/npm/manual）与包名
# app_install: 安装 App 的方式（cask/download/manual）与包名/URL
IDE_INSTALL_META = {
    "Claude": {
        # 官方推荐 native installation（curl/PowerShell 脚本），自动更新
        # 见 https://code.claude.com/docs/en/setup#uninstall-claude-code
        "cli_install": {
            "method": "script",
            "script_url": "https://claude.ai/install.sh",
            "script_url_win": "https://claude.ai/install.ps1",
            "url": "https://claude.ai/download",
            # 卸载：覆盖 native（~/.local/bin+share）+ npm + legacy（~/.claude/local）+ 配置（~/.claude+~/.claude.json）
            "uninstall_cmd_mac": "rm -f ~/.local/bin/claude; rm -rf ~/.local/share/claude ~/.claude/local ~/.claude; rm -f ~/.claude.json; npm uninstall -g @anthropic-ai/claude-code 2>/dev/null; true",
            "uninstall_cmd_win": "del /q \"%USERPROFILE%\\.local\\bin\\claude.exe\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.local\\share\\claude\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.claude\\local\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.claude\" 2>nul & del /q \"%USERPROFILE%\\.claude.json\" 2>nul & npm uninstall -g @anthropic-ai/claude-code 2>nul & exit /b 0",
        },
        "app_install": {
            "method": "system_uninstall",
            "url": "https://claude.ai/download",
            "uninstall_cmd_mac": "rm -rf '/Applications/Claude.app' ~/.claude 2>/dev/null; true",
            "uninstall_cmd_win": "rmdir /s /q \"%LOCALAPPDATA%\\Programs\\claude\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.claude\" 2>nul & exit /b 0",
        },
        "homepage": "https://claude.ai/download",
    },
    "Codex": {
        "cli_install": {
            "method": "npm",
            "package": "@openai/codex",
            "uninstall_cmd": "npm uninstall -g @openai/codex 2>/dev/null; rm -f $(which codex) 2>/dev/null; rm -rf /opt/homebrew/lib/node_modules/@openai/codex ~/.nvm/versions/node/*/lib/node_modules/@openai/codex",
            # Windows：npm 全局 shim 在 %APPDATA%\npm\（codex / codex.cmd / codex.ps1），
            # node_modules 在 %APPDATA%\npm\node_modules\@openai\codex；多 node 环境（nvm-windows）
            # 下 npm uninstall -g 只删当前前缀，需 fallback 删默认 npm 目录 + 配置目录
            "uninstall_cmd_win": "rmdir /s /q \"%APPDATA%\\npm\\node_modules\\@openai\\codex\" 2>nul & del /q \"%APPDATA%\\npm\\codex\" \"%APPDATA%\\npm\\codex.cmd\" \"%APPDATA%\\npm\\codex.ps1\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.codex\" 2>nul & exit /b 0",
        },
        "app_install": {
            "method": "system_uninstall",
            "url": "https://openai.com/codex/download",
            "uninstall_cmd_mac": "rm -rf '/Applications/Codex.app' ~/.codex 2>/dev/null; true",
            "uninstall_cmd_win": "rmdir /s /q \"%LOCALAPPDATA%\\Programs\\codex\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.codex\" 2>nul & exit /b 0",
        },
        "homepage": "https://openai.com/codex",
    },
    "Cursor": {
        # 官方 CLI 安装脚本（跨平台），命令名为 agent
        # 见 https://cursor.com/cn/docs/cli/installation
        "cli_install": {
            "method": "script",
            "script_url": "https://cursor.com/install",
            "script_url_win": "https://cursor.com/install?win32=true",
            "url": "https://cursor.com/cn/docs/cli/installation",
            # 卸载：删除 native binary（agent）+ 配置目录
            "uninstall_cmd_mac": "rm -f ~/.local/bin/agent; rm -rf ~/.cursor; true",
            "uninstall_cmd_win": "del /q \"%USERPROFILE%\\.local\\bin\\agent.exe\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.cursor\" 2>nul & exit /b 0",
        },
        "app_install": {
            "method": "system_uninstall",
            "url": "https://cursor.com",
            "uninstall_cmd_mac": "rm -rf '/Applications/Cursor.app' ~/.cursor 2>/dev/null; true",
            "uninstall_cmd_win": "rmdir /s /q \"%LOCALAPPDATA%\\Programs\\cursor\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.cursor\" 2>nul & exit /b 0",
        },
        "homepage": "https://cursor.com",
    },
    "Trae": {
        "cli_install": {"method": "manual", "url": "https://www.trae.ai"},
        "app_install": {
            "method": "system_uninstall",
            "url": "https://www.trae.ai",
            "uninstall_cmd_mac": "rm -rf '/Applications/Trae.app' ~/.trae 2>/dev/null; true",
            "uninstall_cmd_win": "rmdir /s /q \"%LOCALAPPDATA%\\Programs\\Trae\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.trae\" 2>nul & exit /b 0",
        },
        "homepage": "https://www.trae.ai",
    },
    "TraeCN": {
        "cli_install": {
            "method": "powershell_script",
            "script_url": "https://trae.cn/trae-cli/install.ps1",
            "url": "https://www.trae.cn",
            "uninstall_cmd_mac": "rm -f ~/.local/bin/trae-cli ~/.local/bin/traecli && rm -rf ~/.local/share/trae-cli",
            "uninstall_cmd_win": "powershell -NoProfile -Command \"Remove-Item -Recurse -Force $env:USERPROFILE\\.trae-cli -ErrorAction SilentlyContinue; Remove-Item -Force $env:USERPROFILE\\.local\\bin\\trae-cli.exe -ErrorAction SilentlyContinue; Remove-Item -Force $env:USERPROFILE\\.local\\bin\\traecli.exe -ErrorAction SilentlyContinue\"",
        },
        "app_install": {
            "method": "system_uninstall",
            "url": "https://www.trae.cn",
            "uninstall_cmd_mac": "rm -rf '/Applications/Trae CN.app' ~/.trae-cn ~/.traecn 2>/dev/null; true",
            "uninstall_cmd_win": "rmdir /s /q \"%LOCALAPPDATA%\\Programs\\Trae CN\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.trae-cn\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.traecn\" 2>nul & exit /b 0",
        },
        "homepage": "https://www.trae.cn",
    },
    "TraeSoloCN": {
        "cli_install": {
            "method": "manual",
            "url": "https://www.trae.cn",
            "uninstall_cmd_mac": "rm -rf ~/.trae-solo-cn ~/.traesolocn 2>/dev/null; true",
            "uninstall_cmd_win": "rmdir /s /q \"%USERPROFILE%\\.trae-solo-cn\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.traesolocn\" 2>nul & exit /b 0",
        },
        "app_install": {
            "method": "system_uninstall",
            "url": "https://www.trae.cn/download",
            "uninstall_cmd_mac": "rm -rf '/Applications/Trae Solo CN.app' ~/.trae-solo-cn ~/.traesolocn 2>/dev/null; true",
            "uninstall_cmd_win": "rmdir /s /q \"%LOCALAPPDATA%\\Programs\\Trae Solo CN\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.trae-solo-cn\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.traesolocn\" 2>nul & exit /b 0",
        },
        "homepage": "https://www.trae.cn",
    },
    "OpenCode": {
        "cli_install": {"method": "brew", "package": "opencode", "uninstall_cmd": "rm -f $(which opencode) 2>/dev/null; rm -rf ~/.config/opencode"},
        "app_install": {
            "method": "system_uninstall",
            "url": "https://opencode.ai/downloads",
            "uninstall_cmd_mac": "rm -rf '/Applications/OpenCode.app' ~/.config/opencode ~/.opencode 2>/dev/null; true",
            "uninstall_cmd_win": "rmdir /s /q \"%LOCALAPPDATA%\\Programs\\opencode\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.opencode\" 2>nul & exit /b 0",
        },
        "homepage": "https://opencode.ai",
    },
    "Qoder": {
        "cli_install": {
            "method": "script",
            "script_url": "https://qoder.com/install",
            "uninstall_cmd_mac": "rm -f ~/.local/bin/qoder; rm -rf ~/.qoder; true",
            "uninstall_cmd_win": "del /q \"%USERPROFILE%\\.local\\bin\\qoder.exe\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.qoder\" 2>nul & exit /b 0",
        },
        "app_install": {
            "method": "system_uninstall",
            "url": "https://qoder.com/zh/cli",
            "uninstall_cmd_mac": "rm -rf '/Applications/Qoder.app' ~/.qoder 2>/dev/null; true",
            "uninstall_cmd_win": "rmdir /s /q \"%LOCALAPPDATA%\\Programs\\Qoder\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.qoder\" 2>nul & exit /b 0",
        },
        "homepage": "https://qoder.com/zh/cli",
    },
    "QoderCN": {
        "cli_install": {
            "method": "script",
            "script_url": "https://qoder.com.cn/install",
            "uninstall_cmd_mac": "rm -f ~/.local/bin/qoder-cn; rm -rf ~/.qoder-cn ~/.qodercn; true",
            "uninstall_cmd_win": "del /q \"%USERPROFILE%\\.local\\bin\\qoder-cn.exe\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.qoder-cn\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.qodercn\" 2>nul & exit /b 0",
        },
        "app_install": {
            "method": "system_uninstall",
            "url": "https://qoder.com.cn/download",
            "uninstall_cmd_mac": "rm -rf '/Applications/Qoder CN.app' ~/.qoder-cn ~/.qodercn 2>/dev/null; true",
            "uninstall_cmd_win": "rmdir /s /q \"%LOCALAPPDATA%\\Programs\\Qoder CN\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.qoder-cn\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.qodercn\" 2>nul & exit /b 0",
        },
        "homepage": "https://qoder.com.cn/cli",
    },
    "OpenClaw": {
        "cli_install": {"method": "npm", "package": "openclaw", "uninstall_cmd": "npm uninstall -g openclaw 2>/dev/null; rm -f $(which openclaw) 2>/dev/null; rm -rf ~/.local/share/openclaw"},
        "app_install": {
            "method": "system_uninstall",
            "url": "https://github.com/openclaw/openclaw",
            "uninstall_cmd_mac": "rm -rf '/Applications/OpenClaw.app' ~/.openclaw 2>/dev/null; true",
            "uninstall_cmd_win": "rmdir /s /q \"%LOCALAPPDATA%\\Programs\\openclaw\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.openclaw\" 2>nul & exit /b 0",
        },
        "homepage": "https://github.com/openclaw/openclaw",
    },
    "Hermes": {
        "cli_install": {"method": "manual", "url": ""},
        "app_install": {"method": "manual", "url": ""},
        "homepage": "",
    },
    "WorkBuddy": {
        "cli_install": {"method": "manual", "url": "https://github.com/workbuddy/workbuddy/releases"},
        "app_install": {
            "method": "system_uninstall",
            "url": "https://github.com/workbuddy/workbuddy/releases",
            "uninstall_cmd_mac": "rm -rf /Applications/WorkBuddy.app ~/.workbuddy 2>/dev/null; true",
            "uninstall_cmd_win": "rmdir /s /q \"%LOCALAPPDATA%\\WorkBuddy\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.workbuddy\" 2>nul & exit /b 0",
        },
        "homepage": "https://github.com/workbuddy/workbuddy",
    },
    "ZCode": {
        "cli_install": {
            "method": "manual",
            "url": "https://zcode.z.ai/cn",
            "uninstall_cmd_mac": "rm -f ~/.local/bin/zcode; rm -rf ~/.zcode; true",
            "uninstall_cmd_win": "del /q \"%USERPROFILE%\\.local\\bin\\zcode.exe\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.zcode\" 2>nul & exit /b 0",
        },
        "app_install": {
            "method": "system_uninstall",
            "url": "https://zcode.z.ai/cn/download",
            "uninstall_cmd_mac": "rm -rf '/Applications/ZCode.app' ~/.zcode 2>/dev/null; true",
            "uninstall_cmd_win": "rmdir /s /q \"%LOCALAPPDATA%\\Programs\\ZCode\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.zcode\" 2>nul & exit /b 0",
        },
        "homepage": "https://zcode.z.ai/cn",
    },
    "IDEA": {
        "cli_install": {"method": "manual", "url": "https://www.jetbrains.com/idea"},
        "app_install": {
            "method": "system_uninstall",
            "url": "https://www.jetbrains.com/idea",
            "uninstall_cmd_mac": "rm -rf '/Applications/IntelliJ IDEA.app' '/Applications/IntelliJ IDEA CE.app' ~/.idea ~/.jetbrains 2>/dev/null; true",
            "uninstall_cmd_win": "rmdir /s /q \"%LOCALAPPDATA%\\JetBrains\" 2>nul & rmdir /s /q \"%USERPROFILE%\\.idea\" 2>nul & exit /b 0",
        },
        "homepage": "https://www.jetbrains.com/idea",
    },
    "Agents": {
        "cli_install": {"method": "manual", "url": ""},
        "app_install": {"method": "manual", "url": ""},
        "homepage": "",
    },
}


def _run_cmd(cmd: list[str], timeout: int = 300) -> dict:
    """运行命令并返回结果。

    Returns:
        {ok: bool, returncode: int, stdout: str, stderr: str, cmd: str}
    """
    try:
        r = subprocess.run(
            cmd,
            capture_output=True, text=True,
            timeout=timeout,
        )
        return {
            "ok": r.returncode == 0,
            "returncode": r.returncode,
            "stdout": r.stdout or "",
            "stderr": r.stderr or "",
            "cmd": " ".join(cmd),
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "returncode": -1, "stdout": "", "stderr": "timeout",
                "cmd": " ".join(cmd)}
    except Exception as e:
        return {"ok": False, "returncode": -1, "stdout": "", "stderr": str(e),
                "cmd": " ".join(cmd)}


def _select_link_dir() -> Path:
    """选择可写的软链目录：优先 /usr/local/bin（标准 PATH），不可写则回退 ~/.local/bin。

    app_cli method 用它给 App 内 CLI 建软链，使其出现在 PATH 上。
    """
    candidates = [Path("/usr/local/bin"), Path.home() / ".local" / "bin"]
    for d in candidates:
        try:
            d.mkdir(parents=True, exist_ok=True)
            probe = d / ".agentbuddy.write_probe"
            probe.touch()
            probe.unlink(missing_ok=True)
            return d
        except (PermissionError, OSError):
            continue
    # 兜底：~/.local/bin（即使不可写也返回，由调用方报错）
    return Path.home() / ".local" / "bin"


def install_ide(ide_key: str, mode: str = "cli") -> dict:
    """安装 IDE。

    Args:
        ide_key: IDE 标识（如 "OpenCode"）
        mode: "cli" 或 "app"

    Returns:
        {ok: bool, ide: str, mode: str, method: str, message: str, cmd: str, stdout: str, stderr: str}
    """
    meta = IDE_INSTALL_META.get(ide_key)
    if not meta:
        return {"ok": False, "ide": ide_key, "mode": mode, "method": "",
                "message": f"Unknown IDE: {ide_key}", "cmd": "", "stdout": "", "stderr": ""}

    if mode == "cli":
        install_meta = meta.get("cli_install", {})
    elif mode == "app":
        install_meta = meta.get("app_install", {})
    else:
        return {"ok": False, "ide": ide_key, "mode": mode, "method": "",
                "message": f"Invalid mode: {mode}", "cmd": "", "stdout": "", "stderr": ""}

    method = install_meta.get("method", "manual")
    package = install_meta.get("package", "")
    url = install_meta.get("url", "")
    script_url = install_meta.get("script_url", "")

    if method == "manual":
        return {
            "ok": False, "ide": ide_key, "mode": mode, "method": "manual",
            "message": f"需手动安装，请访问: {url or meta.get('homepage', '')}",
            "cmd": "", "stdout": "", "stderr": "",
            "url": url or meta.get("homepage", ""),
        }

    if method == "app_cli":
        # CLI 随 App 分发（如 Cursor.app 内的 cursor 命令）：建软链到 PATH
        app_path = install_meta.get("app_path", "")
        cli_relpath = install_meta.get("cli_relpath", "")
        link_name = install_meta.get("link_name", ide_key.lower())
        fallback_url = url or meta.get("homepage", "")
        if not app_path or not cli_relpath:
            return {"ok": False, "ide": ide_key, "mode": mode, "method": "app_cli",
                    "message": "app_cli 配置不完整（缺 app_path/cli_relpath）",
                    "cmd": "", "stdout": "", "stderr": "", "url": fallback_url}
        cli_in_app = Path(app_path) / cli_relpath
        if not cli_in_app.exists():
            return {"ok": False, "ide": ide_key, "mode": mode, "method": "app_cli",
                    "message": f"未找到 App 内 CLI（{cli_in_app}），请先安装 App（点'安装 App'）",
                    "cmd": "", "stdout": "", "stderr": "", "url": fallback_url}
        link_dir = _select_link_dir()
        link_target = link_dir / link_name
        cmd_str = f"ln -sf {cli_in_app} {link_target}"
        try:
            # 覆盖已有软链/文件（先删再建，避免 symlink_to 覆盖文件时的行为差异）
            if link_target.is_symlink() or link_target.exists():
                link_target.unlink()
            link_target.symlink_to(cli_in_app)
            return {
                "ok": True, "ide": ide_key, "mode": mode, "method": "app_cli",
                "message": f"已创建软链: {link_target} → {cli_in_app}",
                "cmd": cmd_str, "stdout": "", "stderr": "",
            }
        except PermissionError:
            return {"ok": False, "ide": ide_key, "mode": mode, "method": "app_cli",
                    "message": f"无权限写入 {link_dir}，请手动执行: sudo ln -sf {cli_in_app} {link_target}",
                    "cmd": f"sudo ln -sf {cli_in_app} {link_target}",
                    "stdout": "", "stderr": "PermissionError", "url": fallback_url}
        except Exception as e:
            return {"ok": False, "ide": ide_key, "mode": mode, "method": "app_cli",
                    "message": f"创建软链失败: {e}", "cmd": cmd_str,
                    "stdout": "", "stderr": str(e), "url": fallback_url}

    if method == "script":
        # macOS/Linux: curl -fsSL <script_url> | bash
        # Windows: irm <script_url_win> | iex（若配了 script_url_win，否则回退 manual）
        if sys.platform == "win32":
            script_url_win = install_meta.get("script_url_win", "")
            if not script_url_win:
                return {"ok": False, "ide": ide_key, "mode": mode, "method": "manual",
                        "message": f"需手动安装，请访问: {url or meta.get('homepage', '')}",
                        "cmd": "", "stdout": "", "stderr": "",
                        "url": url or meta.get("homepage", "")}
            shell_cmd = f"irm {script_url_win} | iex"
            r = _run_cmd(["powershell", "-NoProfile", "-Command", shell_cmd], timeout=600)
            return {
                "ok": r["ok"], "ide": ide_key, "mode": mode, "method": "script",
                "message": "安装成功" if r["ok"] else f"安装失败 (exit={r['returncode']})",
                "cmd": shell_cmd, "stdout": r["stdout"][-2000:], "stderr": r["stderr"][-2000:],
            }
        if not shutil.which("curl"):
            return {"ok": False, "ide": ide_key, "mode": mode, "method": "script",
                    "message": "未安装 curl", "cmd": "", "stdout": "", "stderr": ""}
        if not script_url:
            return {"ok": False, "ide": ide_key, "mode": mode, "method": "script",
                    "message": "未配置 script_url", "cmd": "", "stdout": "", "stderr": ""}
        shell_cmd = f"curl -fsSL {script_url} | bash"
        r = _run_cmd(["bash", "-c", shell_cmd], timeout=600)
        return {
            "ok": r["ok"], "ide": ide_key, "mode": mode, "method": "script",
            "message": "安装成功" if r["ok"] else f"安装失败 (exit={r['returncode']})",
            "cmd": shell_cmd, "stdout": r["stdout"][-2000:], "stderr": r["stderr"][-2000:],
        }

    if method == "powershell_script":
        # Windows PowerShell: irm <script_url> | iex
        # 非 Windows 平台回退 manual（PowerShell 脚本仅 Windows 适用）
        if sys.platform != "win32":
            return {
                "ok": False, "ide": ide_key, "mode": mode, "method": "manual",
                "message": f"需手动安装，请访问: {url or meta.get('homepage', '')}",
                "cmd": "", "stdout": "", "stderr": "",
                "url": url or meta.get("homepage", ""),
            }
        if not script_url:
            return {"ok": False, "ide": ide_key, "mode": mode, "method": "powershell_script",
                    "message": "未配置 script_url", "cmd": "", "stdout": "", "stderr": ""}
        shell_cmd = f"irm {script_url} | iex"
        r = _run_cmd(["powershell", "-NoProfile", "-Command", shell_cmd], timeout=600)
        return {
            "ok": r["ok"], "ide": ide_key, "mode": mode, "method": "powershell_script",
            "message": "安装成功" if r["ok"] else f"安装失败 (exit={r['returncode']})",
            "cmd": shell_cmd, "stdout": r["stdout"][-2000:], "stderr": r["stderr"][-2000:],
        }

    if method == "brew":
        if not shutil.which("brew"):
            return {"ok": False, "ide": ide_key, "mode": mode, "method": "brew",
                    "message": "未安装 Homebrew，请先安装: https://brew.sh",
                    "cmd": "", "stdout": "", "stderr": ""}
        cmd = ["brew", "install", package]
        r = _run_cmd(cmd, timeout=600)
        return {
            "ok": r["ok"], "ide": ide_key, "mode": mode, "method": "brew",
            "message": "安装成功" if r["ok"] else f"安装失败 (exit={r['returncode']})",
            "cmd": r["cmd"], "stdout": r["stdout"][-2000:], "stderr": r["stderr"][-2000:],
        }

    if method == "cask":
        if not shutil.which("brew"):
            return {"ok": False, "ide": ide_key, "mode": mode, "method": "cask",
                    "message": "未安装 Homebrew，请先安装: https://brew.sh",
                    "cmd": "", "stdout": "", "stderr": ""}
        cmd = ["brew", "install", "--cask", package]
        r = _run_cmd(cmd, timeout=600)
        return {
            "ok": r["ok"], "ide": ide_key, "mode": mode, "method": "cask",
            "message": "安装成功" if r["ok"] else f"安装失败 (exit={r['returncode']})",
            "cmd": r["cmd"], "stdout": r["stdout"][-2000:], "stderr": r["stderr"][-2000:],
        }

    if method == "npm":
        if not shutil.which("npm"):
            return {"ok": False, "ide": ide_key, "mode": mode, "method": "npm",
                    "message": "未安装 npm，请先安装 Node.js",
                    "cmd": "", "stdout": "", "stderr": ""}
        cmd = ["npm", "install", "-g", package]
        r = _run_cmd(cmd, timeout=600)
        return {
            "ok": r["ok"], "ide": ide_key, "mode": mode, "method": "npm",
            "message": "安装成功" if r["ok"] else f"安装失败 (exit={r['returncode']})",
            "cmd": r["cmd"], "stdout": r["stdout"][-2000:], "stderr": r["stderr"][-2000:],
        }

    return {"ok": False, "ide": ide_key, "mode": mode, "method": method,
            "message": f"Unsupported method: {method}", "cmd": "", "stdout": "", "stderr": ""}


def _get_uninstall_cmd(install_meta: dict) -> str:
    """按平台选择卸载命令。

    支持的字段（按优先级）：
      1. uninstall_cmd_mac / uninstall_cmd_win — 平台专用
      2. uninstall_cmd — 通用（仅 macOS/Linux 下使用 bash 执行）
    """
    is_win = sys.platform == "win32"
    if is_win:
        cmd = install_meta.get("uninstall_cmd_win", "")
        if cmd:
            return cmd
    else:
        cmd = install_meta.get("uninstall_cmd_mac", "")
        if cmd:
            return cmd
    return install_meta.get("uninstall_cmd", "")


def _run_uninstall_cmd(cmd: str) -> dict:
    """执行卸载命令（按平台选择 shell）。

    macOS/Linux: bash -c '<cmd>'
    Windows:     cmd /c '<cmd>'
    """
    if sys.platform == "win32":
        return _run_cmd(["cmd", "/c", cmd], timeout=120)
    return _run_cmd(["bash", "-c", cmd], timeout=120)


def _do_windows_system_uninstall(ide_key: str, mode: str) -> dict | None:
    """Windows 系统级卸载：从注册表查 UninstallString 并执行产品自带卸载程序。

    Returns:
        卸载结果 dict，未找到卸载命令返回 None（由调用方回退）。
    """
    if sys.platform != "win32":
        return None
    try:
        from .detect import lookup_windows_uninstall_cmd, IDE_DETECT_META
    except Exception:
        return None
    # 用 IDE label 反查注册表卸载命令
    label = IDE_DETECT_META.get(ide_key, {}).get("label", ide_key)
    sys_cmd = lookup_windows_uninstall_cmd(label)
    if not sys_cmd:
        return None
    r = _run_uninstall_cmd(sys_cmd)
    return {
        "ok": r["ok"], "ide": ide_key, "mode": mode, "method": "system_uninstall",
        "message": "已调用系统卸载程序" if r["ok"] else f"系统卸载失败 (exit={r['returncode']})",
        "cmd": sys_cmd, "stdout": r["stdout"][-2000:], "stderr": r["stderr"][-2000:],
    }


def _do_system_uninstall(ide_key: str, mode: str, install_meta: dict, meta: dict, force: bool = False) -> dict:
    """系统级卸载（跨平台）。

    - Windows：优先注册表 UninstallString（产品自带卸载程序），失败回退 uninstall_cmd 强删
    - macOS：删 .app 目录 + uninstall_cmd
    - Linux：回退 uninstall_cmd
    - force=True：跳过系统卸载程序，直接 uninstall_cmd 强删（GUI 卸载器卡死/超时/需交互时用）
    """
    # Windows：优先系统卸载程序（force 模式跳过，直接走强删）
    if sys.platform == "win32" and not force:
        sys_result = _do_windows_system_uninstall(ide_key, mode)
        # 仅当系统卸载程序明确成功才返回；失败（GUI 卡死/超时/非零退出）则 fallback 强删
        if sys_result and sys_result.get("ok"):
            return sys_result
    # 回退/强制：配置的 uninstall_cmd（rmdir 强删目录）
    uninstall_cmd = _get_uninstall_cmd(install_meta)
    if uninstall_cmd:
        r = _run_uninstall_cmd(uninstall_cmd)
        ok = r["ok"]
        # exit=0 不代表目录真删掉（Windows `exit /b 0` / macOS `; true` 都会强制返回 0），
        # 需跨平台校验安装目录是否还在
        if ok:
            ok = not _app_dir_exists(ide_key, meta)
        msg_prefix = "强制卸载成功" if force else "卸载成功"
        msg_fail = "强制卸载失败" if force else "卸载失败"
        message = msg_prefix if ok else f"{msg_fail} (exit={r['returncode']}，目录可能被占用，请关闭进程后重试或手动删除)"
        return {
            "ok": ok, "ide": ide_key, "mode": mode, "method": "system_uninstall",
            "message": message,
            "cmd": uninstall_cmd, "stdout": r["stdout"][-2000:], "stderr": r["stderr"][-2000:],
        }
    return {
        "ok": False, "ide": ide_key, "mode": mode, "method": "system_uninstall",
        "message": "未找到系统卸载程序，需手动卸载",
        "cmd": "", "stdout": "", "stderr": "",
        "url": meta.get("homepage", ""),
    }


def _app_dir_exists(ide_key: str, meta: dict) -> bool:
    """校验 IDE 安装目录是否仍存在（强删后校验用，跨平台）。

    - macOS：检查 macos_apps 路径（.app 是否还在）
    - Windows：检查 windows_apps 模板的父目录是否还在
    - Linux：无固定 GUI app 目录概念，返回 False（信任 uninstall_cmd 返回码）
    """
    try:
        from .detect import IDE_DETECT_META, _expand_windows_path
    except Exception:
        return False
    detect_meta = IDE_DETECT_META.get(ide_key, {})
    if sys.platform == "darwin":
        for ap in detect_meta.get("macos_apps", []):
            if Path(ap).exists():
                return True
        return False
    if sys.platform == "win32":
        for tmpl in detect_meta.get("windows_apps", []):
            p = _expand_windows_path(tmpl)
            if p.parent.exists():
                return True
    # Linux 等：无 GUI app 目录，不校验
    return False


def uninstall_ide(ide_key: str, mode: str = "cli", force: bool = False) -> dict:
    """卸载 IDE。

    Args:
        ide_key: IDE 标识
        mode: "cli" 或 "app"
        force: 强制卸载——跳过系统卸载程序，直接按 uninstall_cmd 强删目录。
               用于 GUI 卸载器卡死/超时/需交互弹窗的场景（如 Trae/Cursor app）。

    Returns:
        {ok: bool, ide: str, mode: str, method: str, message: str, cmd: str, stdout: str, stderr: str}
    """
    meta = IDE_INSTALL_META.get(ide_key)
    if not meta:
        return {"ok": False, "ide": ide_key, "mode": mode, "method": "",
                "message": f"Unknown IDE: {ide_key}", "cmd": "", "stdout": "", "stderr": ""}

    if mode == "cli":
        install_meta = meta.get("cli_install", {})
    elif mode == "app":
        install_meta = meta.get("app_install", {})
    else:
        return {"ok": False, "ide": ide_key, "mode": mode, "method": "",
                "message": f"Invalid mode: {mode}", "cmd": "", "stdout": "", "stderr": ""}

    method = install_meta.get("method", "manual")
    package = install_meta.get("package", "")

    if method == "system_uninstall":
        # 系统级卸载：Windows 优先调注册表 UninstallString（产品自带卸载程序），
        # macOS 删 .app，回退到 uninstall_cmd；force=True 跳过系统卸载程序直接强删
        return _do_system_uninstall(ide_key, mode, install_meta, meta, force=force)

    if method == "manual":
        # manual 但配了 uninstall_cmd：按平台选择卸载命令
        uninstall_cmd = _get_uninstall_cmd(install_meta)
        if uninstall_cmd:
            r = _run_uninstall_cmd(uninstall_cmd)
            return {
                "ok": r["ok"], "ide": ide_key, "mode": mode, "method": "manual",
                "message": "卸载成功" if r["ok"] else f"卸载失败 (exit={r['returncode']})",
                "cmd": uninstall_cmd, "stdout": r["stdout"][-2000:], "stderr": r["stderr"][-2000:],
            }
        # manual 无 uninstall_cmd：Windows 下尝试系统卸载（注册表 UninstallString）
        if sys.platform == "win32":
            sys_result = _do_windows_system_uninstall(ide_key, mode)
            if sys_result:
                return sys_result
        return {
            "ok": False, "ide": ide_key, "mode": mode, "method": "manual",
            "message": "需手动卸载", "cmd": "", "stdout": "", "stderr": "",
        }

    if method == "script":
        # script 安装：按平台选择卸载命令（若配置），否则提示手动卸载
        uninstall_cmd = _get_uninstall_cmd(install_meta)
        if uninstall_cmd:
            r = _run_uninstall_cmd(uninstall_cmd)
            return {
                "ok": r["ok"], "ide": ide_key, "mode": mode, "method": "script",
                "message": "卸载成功" if r["ok"] else f"卸载失败 (exit={r['returncode']})",
                "cmd": uninstall_cmd, "stdout": r["stdout"][-2000:], "stderr": r["stderr"][-2000:],
            }
        return {
            "ok": False, "ide": ide_key, "mode": mode, "method": "script",
            "message": "script 安装方式需手动卸载（请参考官方文档）",
            "cmd": "", "stdout": "", "stderr": "",
            "url": meta.get("homepage", ""),
        }

    if method == "powershell_script":
        # powershell_script 安装：按平台选择卸载命令（若配置），否则提示手动卸载
        uninstall_cmd = _get_uninstall_cmd(install_meta)
        if uninstall_cmd:
            r = _run_uninstall_cmd(uninstall_cmd)
            return {
                "ok": r["ok"], "ide": ide_key, "mode": mode, "method": "powershell_script",
                "message": "卸载成功" if r["ok"] else f"卸载失败 (exit={r['returncode']})",
                "cmd": uninstall_cmd, "stdout": r["stdout"][-2000:], "stderr": r["stderr"][-2000:],
            }
        return {
            "ok": False, "ide": ide_key, "mode": mode, "method": "powershell_script",
            "message": "powershell_script 安装方式需手动卸载（请参考官方文档）",
            "cmd": "", "stdout": "", "stderr": "",
            "url": meta.get("homepage", ""),
        }

    if method == "brew":
        if shutil.which("brew"):
            r = _run_cmd(["brew", "uninstall", package], timeout=300)
            if r["ok"]:
                return {
                    "ok": True, "ide": ide_key, "mode": mode, "method": "brew",
                    "message": "卸载成功", "cmd": r["cmd"],
                    "stdout": r["stdout"][-2000:], "stderr": r["stderr"][-2000:],
                }
        # brew 失败或无 brew，fallback uninstall_cmd
        uninstall_cmd = _get_uninstall_cmd(install_meta)
        if uninstall_cmd:
            r = _run_uninstall_cmd(uninstall_cmd)
            return {
                "ok": r["ok"], "ide": ide_key, "mode": mode, "method": "brew",
                "message": "卸载成功" if r["ok"] else f"卸载失败 (exit={r['returncode']})",
                "cmd": uninstall_cmd, "stdout": r["stdout"][-2000:], "stderr": r["stderr"][-2000:],
            }
        return {"ok": False, "ide": ide_key, "mode": mode, "method": "brew",
                "message": "未安装 Homebrew 或 brew uninstall 失败", "cmd": "", "stdout": "", "stderr": ""}

    if method == "cask":
        if shutil.which("brew"):
            cmd = ["brew", "uninstall", "--cask", package]
            r = _run_cmd(cmd, timeout=300)
            if r["ok"]:
                return {
                    "ok": True, "ide": ide_key, "mode": mode, "method": "cask",
                    "message": "卸载成功", "cmd": r["cmd"],
                    "stdout": r["stdout"][-2000:], "stderr": r["stderr"][-2000:],
                }
        # cask 失败或无 brew（Windows/Linux），fallback uninstall_cmd
        uninstall_cmd = _get_uninstall_cmd(install_meta)
        if uninstall_cmd:
            r = _run_uninstall_cmd(uninstall_cmd)
            return {
                "ok": r["ok"], "ide": ide_key, "mode": mode, "method": "cask",
                "message": "卸载成功" if r["ok"] else f"卸载失败 (exit={r['returncode']})",
                "cmd": uninstall_cmd, "stdout": r["stdout"][-2000:], "stderr": r["stderr"][-2000:],
            }
        return {"ok": False, "ide": ide_key, "mode": mode, "method": "cask",
                "message": "未安装 Homebrew 或 brew uninstall 失败", "cmd": "", "stdout": "", "stderr": ""}

    if method == "npm":
        # 获取 cli_names 用于校验二进制是否真正删除
        cli_names = IDE_INSTALL_META.get(ide_key, {}).get("cli_install", {}).get("cli_names", [])
        try:
            from .detect import IDE_DETECT_META
            cli_names = IDE_DETECT_META.get(ide_key, {}).get("cli_names", cli_names)
        except Exception:
            pass

        if not force:
            if not shutil.which("npm"):
                return {"ok": False, "ide": ide_key, "mode": mode, "method": "npm",
                        "message": "未安装 npm", "cmd": "", "stdout": "", "stderr": ""}
            cmd = ["npm", "uninstall", "-g", package]
            r = _run_cmd(cmd, timeout=300)
            if r["ok"]:
                # npm uninstall 返回成功，但可能没真正删掉（多 npm 环境如 nvm vs homebrew）
                # 检查二进制是否还在，在则 fallback uninstall_cmd
                still_exists = any(shutil.which(n) for n in cli_names) if cli_names else False
                if not still_exists:
                    return {
                        "ok": True, "ide": ide_key, "mode": mode, "method": "npm",
                        "message": "卸载成功", "cmd": r["cmd"],
                        "stdout": r["stdout"][-2000:], "stderr": r["stderr"][-2000:],
                    }
        # force 模式 或 npm uninstall 失败/二进制仍在 → fallback uninstall_cmd 强删
        # 按平台选 shell：Windows 用 cmd /c，macOS/Linux 用 bash -c
        uninstall_cmd = _get_uninstall_cmd(install_meta)
        if uninstall_cmd:
            r2 = _run_uninstall_cmd(uninstall_cmd)
            ok = r2["ok"]
            # exit=0 不代表真删掉（Windows exit /b 0 / macOS ; true 都强制返回 0）
            # 校验 cli 二进制是否还在
            if ok and cli_names:
                ok = not any(shutil.which(n) for n in cli_names)
            msg_prefix = "强制卸载成功" if force else "卸载成功"
            msg_fail = "强制卸载失败" if force else "卸载失败"
            message = msg_prefix if ok else f"{msg_fail} (exit={r2['returncode']}，二进制可能被占用或 PATH 缓存，请重启终端后重试)"
            return {
                "ok": ok, "ide": ide_key, "mode": mode, "method": "npm",
                "message": message,
                "cmd": uninstall_cmd, "stdout": r2["stdout"][-2000:], "stderr": r2["stderr"][-2000:],
            }
        return {
            "ok": False, "ide": ide_key, "mode": mode, "method": "npm",
            "message": "卸载失败 (无 fallback uninstall_cmd)", "cmd": "", "stdout": "", "stderr": "",
        }

    return {"ok": False, "ide": ide_key, "mode": mode, "method": method,
            "message": f"Unsupported method: {method}", "cmd": "", "stdout": "", "stderr": ""}


def reinstall_ide(ide_key: str, mode: str = "cli") -> dict:
    """重装 IDE（先卸载再安装）。

    Args:
        ide_key: IDE 标识
        mode: "cli" 或 "app"

    Returns:
        {ok: bool, ide, mode, method, message, cmd, stdout, stderr, uninstall_result?}
    """
    # 1. 先卸载（忽略卸载失败，继续安装）
    uninst = uninstall_ide(ide_key, mode)
    # 2. 再安装
    inst = install_ide(ide_key, mode)
    inst["reinstall"] = True
    inst["uninstall_result"] = {
        "ok": uninst.get("ok", False),
        "message": uninst.get("message", ""),
    }
    # 综合判断：安装成功即视为重装成功
    inst["message"] = f"重装成功（卸载: {uninst.get('message','')} → 安装: {inst.get('message','')}）" if inst["ok"] \
        else f"重装失败（卸载: {uninst.get('message','')} → 安装: {inst.get('message','')}）"
    return inst


def get_install_info(ide_key: str) -> dict:
    """获取 IDE 的安装元信息（不执行安装）。

    平台适配：
    - macOS：cask 方式有效（brew install --cask）
    - Windows/Linux：cask 不可用，自动降级为 manual + homepage URL
    """
    meta = IDE_INSTALL_META.get(ide_key)
    if not meta:
        return {"ide": ide_key, "available": False}
    cli_install = dict(meta.get("cli_install", {}))
    app_install = dict(meta.get("app_install", {}))
    homepage = meta.get("homepage", "")

    # 非 macOS 平台：cask/brew/app_cli 降级为 manual + homepage，保留 uninstall_cmd
    if sys.platform != "darwin":
        if cli_install.get("method") in ("cask", "brew", "app_cli"):
            cli_install = {**cli_install, "method": "manual", "url": homepage}
        if app_install.get("method") == "cask":
            app_install = {**app_install, "method": "manual", "url": homepage}

    # 非 Windows 平台：powershell_script 降级为 manual（PowerShell 脚本仅 Windows 适用）
    if sys.platform != "win32" and cli_install.get("method") == "powershell_script":
        cli_install = {"method": "manual", "url": homepage}

    return {
        "ide": ide_key,
        "available": True,
        "cli": cli_install,
        "app": app_install,
        "homepage": homepage,
    }


__all__ = ["IDE_INSTALL_META", "install_ide", "uninstall_ide", "reinstall_ide", "get_install_info"]
