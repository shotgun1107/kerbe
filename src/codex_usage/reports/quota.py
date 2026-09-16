"""Render account windows separately from project token usage."""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any
import unicodedata
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from codex_usage.sources.quota import QuotaError


def quota_timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        raise QuotaError("표시 시간대를 찾지 못했습니다. 예: Asia/Seoul, UTC") from None


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        return None
    try:
        return float(value) if math.isfinite(value) else None
    except OverflowError:
        return None


def _label(value: Any, fallback: str) -> str:
    if not isinstance(value, str) or not value.strip():
        return fallback
    return "".join(c for c in value[:100] if not unicodedata.category(c).startswith("C"))


def render_quota(
    response: dict[str, Any], *, timezone_name: str = "Asia/Seoul",
    observed_at: datetime | None = None,
) -> str:
    zone = quota_timezone(timezone_name)
    now = observed_at or datetime.now(timezone.utc)
    buckets = response.get("rateLimitsByLimitId")
    if buckets is None:
        legacy = response.get("rateLimits")
        buckets = {} if legacy is None else {"codex": legacy}
    if not isinstance(buckets, dict):
        raise QuotaError("한도 버킷 응답 형식을 확인할 수 없습니다.")
    lines = [
        "계정 구독 한도 (프로젝트 토큰 사용량과 별도)",
        f"조회 시각: {now.astimezone(zone):%Y-%m-%d %H:%M:%S %Z}",
    ]
    if not buckets:
        lines.append("한도 정보 없음: 현재 로그인 방식이나 계정에서 제공되지 않을 수 있습니다.")
    for key, bucket in sorted(buckets.items()):
        if not isinstance(bucket, dict):
            raise QuotaError("한도 버킷 응답 형식을 확인할 수 없습니다.")
        identity = _label(bucket.get("limitId"), _label(key, "알 수 없는 버킷"))
        name = _label(bucket.get("limitName"), identity)
        lines.append(f"\n{name}" + (f" [{identity}]" if name != identity else ""))
        found = False
        for role in ("primary", "secondary"):
            window = bucket.get(role)
            if window is None:
                continue
            if not isinstance(window, dict):
                raise QuotaError("한도 창 응답 형식을 확인할 수 없습니다.")
            found = True
            minutes = _number(window.get("windowDurationMins"))
            duration = "기간 미제공"
            if minutes is not None and minutes > 0:
                if minutes % 1440 == 0:
                    duration = f"{minutes / 1440:g}일"
                elif minutes % 60 == 0:
                    duration = f"{minutes / 60:g}시간"
                else:
                    duration = f"{minutes:g}분"
            used = _number(window.get("usedPercent"))
            remaining = "미제공"
            if used is not None and used >= 0:
                remaining = f"{max(0, min(100, 100 - used)):g}% (사용 {used:g}%)"
            reset = "미제공"
            timestamp = _number(window.get("resetsAt"))
            if timestamp is not None:
                try:
                    instant = datetime.fromtimestamp(timestamp, timezone.utc)
                    reset = instant.astimezone(zone).strftime("%Y-%m-%d %H:%M:%S %Z")
                    seconds = (instant - now).total_seconds()
                    if seconds <= 0:
                        reset += " (지난 시각 · 다시 조회 필요)"
                    else:
                        total_minutes = math.ceil(seconds / 60)
                        days, rest = divmod(total_minutes, 1440)
                        hours, mins = divmod(rest, 60)
                        reset += f" ({days}일 {hours}시간 {mins}분 후)"
                except (OverflowError, OSError, ValueError):
                    reset = "미제공"
            lines.append(f"  {duration} ({role}): 남음 {remaining}")
            lines.append(f"    초기화: {reset}")
        if not found:
            lines.append("  한도 창 정보 미제공")
        reached = bucket.get("rateLimitReachedType")
        if reached is not None:
            lines.append(f"  서버 한도 상태: {_label(reached, '도달 상태 확인 필요')}")
    lines.append("\n현재 조회값이며 남은 토큰·메시지 수로 환산하지 않습니다.")
    return "\n".join(lines) + "\n"
