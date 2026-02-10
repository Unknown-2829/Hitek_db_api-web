"""
Result Formatters
Professional OSINT-style output — clean, compact, easy to copy.
Renders perfectly on all Telegram clients.
"""

import re
from html import escape
from typing import Any


def clean_address(raw: str | None) -> str:
    """Clean garbage from address field."""
    if not raw:
        return "N/A"
    addr = raw.strip()
    addr = addr.replace("!!", ", ").replace("!", ", ")
    addr = addr.lstrip(", ")
    addr = re.sub(r"[,\s]{2,}", ", ", addr)
    addr = addr.rstrip(", ").strip()
    return addr if addr else "N/A"


def _safe(value: Any) -> str:
    """HTML-escape a value, return 'N/A' for empty."""
    if value is None:
        return "N/A"
    s = str(value).strip()
    return escape(s) if s else "N/A"


def format_single_result(row: dict[str, Any], index: int = 0, total: int = 0) -> str:
    """Format a single DB row — professional OSINT data card."""
    mobile = _safe(row.get("mobile"))
    name = _safe(row.get("name"))
    fname = _safe(row.get("fname"))
    email = _safe(row.get("email"))
    address = escape(clean_address(row.get("address")))
    circle = _safe(row.get("circle"))
    op_id = _safe(row.get("operator_id"))
    alt_mobile = _safe(row.get("alt_mobile"))

    header = f"▓▓▓ <b>RECORD {index}/{total}</b> ▓▓▓\n" if index else ""

    block = (
        f"{header}"
        f"<code>┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        f"<code>┃</code> 📱  <code>{mobile}</code>\n"
        f"<code>┃</code> 👤  {name}\n"
        f"<code>┃</code> 👨  {fname}\n"
    )

    if email and email != "N/A":
        block += f"<code>┃</code> 📧  <code>{email}</code>\n"

    block += (
        f"<code>┃</code> 📍  {address}\n"
        f"<code>┃</code> 📡  {circle}\n"
        f"<code>┃</code> 🆔  <code>{op_id}</code>\n"
    )

    if alt_mobile and alt_mobile != "N/A":
        block += f"<code>┃</code> 📞  <code>{alt_mobile}</code>\n"

    block += f"<code>┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</code>"

    return block


def format_results(rows: list[dict[str, Any]], query: str, search_type: str, elapsed_ms: int = 0) -> str:
    """Format search results — professional OSINT output."""
    time_str = f"  ⏱ <code>{elapsed_ms}ms</code>" if elapsed_ms else ""

    if not rows:
        return (
            "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n"
            "  ❌ <b>TARGET NOT FOUND</b>\n"
            "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n\n"
            f"  🎯 Target : <code>{escape(query)}</code>\n"
            f"  📂 Method : {escape(search_type)}{time_str}\n\n"
            "<i>Verify the number and try again.</i>"
        )

    count = len(rows)

    header = (
        "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n"
        f"  🎯 <b>TARGET LOCATED — {count} HIT{'S' if count > 1 else ''}</b>\n"
        "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n\n"
        f"  🔍 Query  : <code>{escape(query)}</code>\n"
        f"  📂 Method : {escape(search_type)}{time_str}\n\n"
    )

    result_blocks = []
    for i, row in enumerate(rows, 1):
        result_blocks.append(format_single_result(row, i, count))

    footer = (
        f"\n\n<code>{'─' * 31}</code>\n"
        f"📊 <b>{count}</b> record{'s' if count > 1 else ''}"
        f" | ⚡ <b>HiTek OSINT</b>"
    )

    return header + "\n\n".join(result_blocks) + footer


def format_welcome() -> str:
    """Welcome message — professional OSINT tool branding."""
    return (
        "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n"
        "       ⚡ <b>HiTek OSINT</b> ⚡\n"
        "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n\n"
        "  📊  <b>1.78B</b> Records Indexed\n"
        "  ⚡  Instant Mobile Lookup\n"
        "  🔒  Encrypted &amp; Secure\n\n"
        "<code>─────────────────────────────────</code>\n\n"
        "📱 <b>Quick Start:</b>\n"
        "  ▸ Send any <b>10-digit mobile</b>\n"
        "  ▸ <code>/search 9876543210</code>\n\n"
        "📋 <b>Commands:</b>\n"
        "  /help   — Command list\n"
        "  /stats  — Statistics"
    )


def format_help() -> str:
    """Help — compact command reference."""
    return (
        "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n"
        "        📖 <b>Command List</b>\n"
        "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n\n"
        "<b>🔍 Search:</b>\n"
        "  /search <code>&lt;number&gt;</code>\n"
        "  <i>Or just type a 10-digit number</i>\n\n"
        "<b>📊 Info:</b>\n"
        "  /stats — Bot statistics\n"
        "  /help  — This menu\n\n"
        "<b>📱 Input:</b>\n"
        "  ✅ <code>9876543210</code>\n"
        "  🔄 <code>+91 98765 43210</code> → auto-fix\n"
        "  🔄 <code>09876543210</code> → auto-fix"
    )


def format_admin_help() -> str:
    """Admin panel — organized command reference."""
    return (
        "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n"
        "        🔐 <b>Admin Panel</b>\n"
        "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n\n"
        "<b>⚙️ System:</b>\n"
        "  /setmode <code>&lt;public|private&gt;</code>\n"
        "  /getmode — Current mode\n\n"
        "<b>📝 Logs:</b>\n"
        "  /logs     — Download log\n"
        "  /clearlog — Clear log\n\n"
        "<b>📊 Stats:</b>\n"
        "  /dbstats — Database info\n"
        "  /users   — User count\n\n"
        "<b>📡 Broadcast:</b>\n"
        "  /alert <code>&lt;msg&gt;</code>\n\n"
        "<b>🚫 Moderation:</b>\n"
        "  /ban <code>&lt;id&gt;</code>  · /unban <code>&lt;id&gt;</code>  · /banlist"
    )


def format_stats(
    total_searches: int,
    total_users: int,
    bot_mode: str,
    uptime: str,
) -> str:
    """Bot statistics."""
    mode_emoji = "🌐" if bot_mode.lower() == "public" else "🔒"
    return (
        "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n"
        "       📊 <b>Statistics</b>\n"
        "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n\n"
        f"  🔍  Searches  :  <code>{total_searches:,}</code>\n"
        f"  👥  Users     :  <code>{total_users:,}</code>\n"
        f"  {mode_emoji}  Mode      :  <code>{bot_mode.upper()}</code>\n"
        f"  ⏱  Uptime    :  <code>{uptime}</code>"
    )


def format_dbstats(row_count: int, size_str: str) -> str:
    """Database statistics."""
    return (
        "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n"
        "       💾 <b>Database Info</b>\n"
        "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n\n"
        f"  📊  Rows    :  <code>{row_count:,}</code>\n"
        f"  💽  Size    :  <code>{size_str}</code>\n"
        f"  📁  Path    :  <code>/data/users.db</code>\n"
        f"  🔧  Journal :  <code>WAL</code>\n"
        f"  💾  Cache   :  <code>64MB</code>\n"
        f"  🗺  MMap    :  <code>2GB</code>"
    )
