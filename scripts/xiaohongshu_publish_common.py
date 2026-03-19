#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import time
from pathlib import Path
from typing import List

XHS_STATE_DIR = Path('/Users/haha/.local/share/xiaohongshu-mcp')
XHS_SERVER_BIN = Path('/Users/haha/.local/bin/xiaohongshu-mcp')
XHS_SERVER_PORT = 18060
XHS_SERVER_URL = f'http://127.0.0.1:{XHS_SERVER_PORT}/mcp'
XHS_SERVER_PID = XHS_STATE_DIR / 'server.pid'
XHS_SERVER_LOG = XHS_STATE_DIR / 'server.log'
XHS_COOKIES = XHS_STATE_DIR / 'cookies.json'


def run(cmd: List[str], *, capture: bool = True, check: bool = True, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, text=True, capture_output=capture, env=env)


def _pid_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _read_pid() -> int | None:
    if not XHS_SERVER_PID.exists():
        return None
    try:
        return int(XHS_SERVER_PID.read_text().strip())
    except Exception:
        return None


def _wait_for_port(host: str, port: int, timeout_s: float) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def _pids_listening_on_port(port: int) -> list[int]:
    lsof_bin = '/usr/sbin/lsof' if Path('/usr/sbin/lsof').exists() else 'lsof'
    proc = subprocess.run(
        [lsof_bin, '-ti', f'tcp:{port}'],
        check=False,
        text=True,
        capture_output=True,
    )
    pids: list[int] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.isdigit():
            pids.append(int(line))
    return pids


def stop_xhs_server() -> None:
    candidate_pids = []
    pid = _read_pid()
    if pid:
        candidate_pids.append(pid)
    for port_pid in _pids_listening_on_port(XHS_SERVER_PORT):
        if port_pid not in candidate_pids:
            candidate_pids.append(port_pid)

    for pid in candidate_pids:
        if not _pid_is_alive(pid):
            continue
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.kill(pid, sig)
            except OSError:
                break
            for _ in range(20):
                if not _pid_is_alive(pid):
                    break
                time.sleep(0.2)
            if not _pid_is_alive(pid):
                break


def start_xhs_server() -> int:
    if not XHS_COOKIES.exists():
        raise RuntimeError(f'cookies.json 缺失：{XHS_COOKIES}')
    if not XHS_SERVER_BIN.exists():
        raise RuntimeError(f'xiaohongshu-mcp 不存在：{XHS_SERVER_BIN}')

    XHS_STATE_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env['COOKIES_PATH'] = str(XHS_COOKIES)

    with XHS_SERVER_LOG.open('a', encoding='utf-8') as logf:
        proc = subprocess.Popen(
            [str(XHS_SERVER_BIN), '-port', f':{XHS_SERVER_PORT}'],
            cwd=str(XHS_STATE_DIR),
            stdout=logf,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
            text=True,
        )
    XHS_SERVER_PID.write_text(str(proc.pid))

    if not _wait_for_port('127.0.0.1', XHS_SERVER_PORT, timeout_s=15):
        raise RuntimeError(f'xiaohongshu-mcp 启动超时，端口 {XHS_SERVER_PORT} 未就绪')
    return proc.pid


def ensure_xhs_server(restart: bool = False) -> int:
    if restart:
        stop_xhs_server()
        return start_xhs_server()

    pid = _read_pid()
    if pid and _pid_is_alive(pid) and _wait_for_port('127.0.0.1', XHS_SERVER_PORT, timeout_s=1.5):
        return pid
    if _wait_for_port('127.0.0.1', XHS_SERVER_PORT, timeout_s=1.5):
        port_pids = _pids_listening_on_port(XHS_SERVER_PORT)
        if port_pids:
            XHS_SERVER_PID.write_text(str(port_pids[0]))
            return port_pids[0]
    return start_xhs_server()


def check_xhs_login() -> str:
    proc = run([
        'mcporter', 'call', '--timeout', '20000', 'xiaohongshu.check_login_status()'
    ])
    return proc.stdout.strip()


def preflight_xhs(restart: bool = False) -> dict:
    pid = ensure_xhs_server(restart=restart)
    login_status = check_xhs_login()
    if '已登录' not in login_status and 'logged' not in login_status.lower():
        pid = ensure_xhs_server(restart=True)
        login_status = check_xhs_login()
    if '已登录' not in login_status and 'logged' not in login_status.lower():
        raise RuntimeError(f'小红书登录态异常：{login_status}')
    return {
        'server_pid': pid,
        'server_url': XHS_SERVER_URL,
        'cookies_path': str(XHS_COOKIES),
        'login_status': login_status,
    }


def append_publish_error_context(message: str) -> str:
    details = {
        'server_pid': _read_pid(),
        'server_url': XHS_SERVER_URL,
        'cookies_exists': XHS_COOKIES.exists(),
        'server_log': str(XHS_SERVER_LOG),
    }
    return f"{message} | context={json.dumps(details, ensure_ascii=False)}"
