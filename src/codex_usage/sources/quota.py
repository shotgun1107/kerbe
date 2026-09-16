"""One-shot, read-only Codex App Server rate-limit client.

Uses Codex's existing login; never reads credentials or starts a model turn.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

from codex_usage import __version__


class QuotaError(ValueError):
    """A sanitized quota query failure safe to display in the CLI."""


def find_codex(executable: str) -> str | None:
    resolved = shutil.which(executable)
    if resolved is not None or executable != "codex" or os.name != "nt":
        return resolved
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return None
    programs = Path(local_app_data) / "Programs"
    # Desktop installs need not add the bundled engine to the user's PATH.
    candidates = []
    for pattern in (
        "Codex*/resources/codex.exe",
        "Codex*/app/resources/codex.exe",
        "Codex*/*/app/resources/codex.exe",
    ):
        try:
            for path in programs.glob(pattern):
                try:
                    if path.is_file():
                        candidates.append((path.stat().st_mtime_ns, str(path)))
                except OSError:
                    continue
        except OSError:
            continue
    return max(candidates)[1] if candidates else None


def read_rate_limits(*, executable: str = "codex", timeout: float = 15) -> dict[str, Any]:
    if not math.isfinite(timeout) or not 0 < timeout <= 120:
        raise QuotaError("조회 제한시간은 0초 초과 120초 이하여야 합니다.")
    resolved = find_codex(executable)
    if resolved is None:
        raise QuotaError("Codex 실행 파일을 찾지 못했습니다. --codex-path로 지정하세요.")
    if os.name == "nt" and resolved.lower().endswith((".cmd", ".bat", ".ps1")):
        raise QuotaError("--codex-path에 Codex의 네이티브 codex.exe를 지정하세요.")
    try:
        return asyncio.run(_query(resolved, timeout))
    except TimeoutError:
        raise QuotaError("한도 조회 시간이 초과됐습니다. 연결 상태를 확인하고 다시 조회하세요.") from None
    except (OSError, UnicodeError, ValueError) as error:
        if isinstance(error, QuotaError):
            raise
        raise QuotaError("Codex 한도 응답을 읽지 못했습니다. CLI 설치와 연결 상태를 확인하세요.") from None


async def _query(executable: str, timeout: float) -> dict[str, Any]:
    process = None
    try:
        async with asyncio.timeout(timeout):
            process = await asyncio.create_subprocess_exec(
                executable, "app-server",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
                limit=1024 * 1024,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            assert process.stdin is not None and process.stdout is not None

            async def send(message: dict[str, Any]) -> None:
                process.stdin.write((json.dumps(message) + "\n").encode("utf-8"))
                await process.stdin.drain()

            async def receive(request_id: int) -> dict[str, Any]:
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        raise QuotaError("Codex가 응답 전에 종료됐습니다. 설치와 로그인 상태를 확인하세요.")
                    try:
                        message = json.loads(line)
                    except (ValueError, UnicodeError):
                        raise QuotaError("Codex가 올바르지 않은 JSON 응답을 반환했습니다.") from None
                    if not isinstance(message, dict):
                        raise QuotaError("Codex 응답 형식을 확인할 수 없습니다.")
                    if "method" in message:
                        # Ignore notifications; refuse unexpected server requests.
                        if "id" in message:
                            await send({"id": message["id"], "error": {
                                "code": -32601, "message": "Unsupported client method",
                            }})
                        continue
                    if message.get("id") != request_id:
                        continue
                    if "error" in message:
                        # Never echo server errors: they can contain account details.
                        raise QuotaError("한도 조회가 거부됐습니다. Codex의 ChatGPT 로그인·네트워크·버전 지원을 확인하세요.")
                    result = message.get("result")
                    if not isinstance(result, dict):
                        raise QuotaError("Codex 한도 응답 형식을 확인할 수 없습니다.")
                    return result

            await send({"id": 1, "method": "initialize", "params": {
                "clientInfo": {"name": "codex_usage_tracker", "version": __version__},
            }})
            await receive(1)
            await send({"method": "initialized", "params": {}})
            await send({"id": 2, "method": "account/rateLimits/read"})
            return await receive(2)
    finally:
        if process is not None:
            if process.returncode is None:
                try:
                    process.terminate()
                except ProcessLookupError:
                    pass
                try:
                    await asyncio.wait_for(process.wait(), timeout=2)
                except TimeoutError:
                    process.kill()
                    await process.wait()
            if process.stdin is not None:
                process.stdin.close()
