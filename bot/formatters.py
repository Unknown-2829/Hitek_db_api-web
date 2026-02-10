"""
Result Formatters
Clean address data and format DB results in OSINT/Hacker monospace style.
"""

import re
from html import escape
from typing import Any


def clean_address(raw: str | None) -> str:
    """
    Clean garbage from address field.
    - Strip leading '!'
    - Replace '!!' and '!' with ', '
    - Collapse multiple commas/spaces
    - Strip trailing commas
    """
    if not raw:
        return "N/A"

    addr = raw.strip()
    # Replace !! with comma separator
    addr = addr.replace("!!", ", ")
    addr = addr.replace("!", ", ")
    # Remove leading commas/spaces
    addr = addr.lstrip(", ")
    # Collapse multiple commas and spaces
    addr = re.sub(r"[,\s]{2,}", ", ", addr)
    # Remove trailing comma
    addr = addr.rstrip(", ").strip()

    return addr if addr else "N/A"


def _safe(value: Any) -> str:
    """HTML-escape a value, return 'N/A' for empty."""
    if value is None:
        return "N/A"
    s = str(value).strip()
    return escape(s) if s else "N/A"


def format_single_result(row: dict[str, Any], index: int = 0) -> str:
    """Format a single DB row into OSINT-style monospace block."""

    mobile = _safe(row.get("mobile"))
    name = _safe(row.get("name"))
    fname = _safe(row.get("fname"))
    email = _safe(row.get("email"))
    address = clean_address(row.get("address"))
    address = escape(address)
    circle = _safe(row.get("circle"))
    op_id = _safe(row.get("operator_id"))
    alt_mobile = _safe(row.get("alt_mobile"))

    lines = [
        f"┌─────────────────────────────────┐",
        f"│  📱 MOBILE  ➜  <code>{mobile}</code>",
        f"│  👤 NAME    ➜  {name}",
        f"│  👨 FATHER  ➜  {fname}",
        f"│  📧 EMAIL   ➜  <code>{email}</code>",
        f"│  🏠 ADDR    ➜  {address}",
        f"│  📡 CIRCLE  ➜  {circle}",
        f"│  🆔 ID      ➜  <code>{op_id}</code>",
    ]

    if alt_mobile and alt_mobile != "N/A":
        lines.append(f"│  📞 ALT     ➜  <code>{alt_mobile}</code>")

    lines.append(f"└─────────────────────────────────┘")

    return "\n".join(lines)


def format_results(rows: list[dict[str, Any]], query: str, search_type: str) -> str:
    """Format multiple results with header and count."""

    if not rows:
        return (
            "<pre>"
            "╔══════════════════════════════════╗\n"
            "║   ❌  NO RESULTS FOUND           ║\n"
            "╚══════════════════════════════════╝"
            "</pre>\n\n"
            f"🔍 Query: <code>{escape(query)}</code>\n"
            f"📂 Type: {escape(search_type)}"
        )

    count = len(rows)
    header = (
        "<pre>"
        "╔══════════════════════════════════╗\n"
        f"║  🔎 FOUND: {count} RESULT{'S' if count > 1 else ''}               ║\n"
        "╠══════════════════════════════════╣\n"
        f"║  🔍 QUERY : {escape(query):<20s} ║\n"
        f"║  📂 TYPE  : {escape(search_type):<20s} ║\n"
        "╚══════════════════════════════════╝"
        "</pre>\n"
    )

    result_blocks = []
    for i, row in enumerate(rows, 1):
        block = f"\n<b>━━━ Result {i}/{count} ━━━</b>\n"
        block += f"<pre>{format_single_result(row, i)}</pre>"
        result_blocks.append(block)

    footer = f"\n\n<i>⚡ Powered by HiTek DB | {count} record{'s' if count > 1 else ''} found</i>"

    return header + "\n".join(result_blocks) + footer


def format_welcome() -> str:
    """Welcome message for /start command."""
    return (
        "<pre>"
        "╔══════════════════════════════════════╗\n"
        "║                                      ║\n"
        "║    ⚡ HiTek Database Bot ⚡           ║\n"
        "║    ━━━━━━━━━━━━━━━━━━━━━             ║\n"
        "║    🔍 1.78 Billion Records            ║\n"
        "║    ⚡ Instant Mobile Lookup            ║\n"
        "║    🛡️ Secure &amp; Private                ║\n"
        "║                                      ║\n"
        "╚══════════════════════════════════════╝"
        "</pre>\n\n"
        "<b>📖 How to Search:</b>\n\n"
        "  📱 <code>/search 9999999891</code>  — Search by mobile\n"
        "  👤 <code>/search Krishan</code>      — Search by name\n"
        "  📧 <code>/email test@gmail.com</code> — Search by email\n"
        "  🏠 <code>/addr Delhi</code>           — Search by address\n"
        "  👨 <code>/fname Rajender</code>       — Search by father name\n\n"
        "  💬 Or just send a <b>mobile number</b> directly!\n\n"
        "<b>📊 Other Commands:</b>\n"
        "  /help  — Show all commands\n"
        "  /stats — Bot statistics\n\n"
        "<i>⚠️ Rate limit: 1 search every 2 seconds</i>"
    )


def format_help() -> str:
    """Help message with all user commands."""
    return (
        "<b>📖 User Commands:</b>\n\n"
        "  /start           — Welcome message\n"
        "  /help            — This help menu\n"
        "  /search &lt;query&gt;  — Search by mobile or name\n"
        "  /email &lt;query&gt;   — Search by email\n"
        "  /addr &lt;query&gt;    — Search by address\n"
        "  /fname &lt;query&gt;   — Search by father's name\n"
        "  /stats           — Bot statistics\n\n"
        "<i>💡 Tip: Just send a mobile number directly to search!</i>"
    )


def format_admin_help() -> str:
    """Admin command help."""
    return (
        "<b>🔐 Admin Commands:</b>\n\n"
        "  /admin           — This admin help menu\n"
        "  /logs            — Download search log file\n"
        "  /dbstats         — Database statistics\n"
        "  /alert &lt;msg&gt;     — Broadcast to all users\n"
        "  /clearlog        — Clear search log file\n"
        "  /setmode &lt;mode&gt;  — Set bot mode (public/private)\n"
        "  /getmode         — Show current bot mode\n"
        "  /users           — Show tracked user count\n"
        "  /ban &lt;user_id&gt;   — Ban a user\n"
        "  /unban &lt;user_id&gt; — Unban a user\n"
        "  /banlist         — Show banned users\n"
    )


def format_stats(
    total_searches: int,
    total_users: int,
    bot_mode: str,
    uptime: str,
) -> str:
    """Format bot statistics."""
    return (
        "<pre>"
        "╔══════════════════════════════════╗\n"
        "║       📊 BOT STATISTICS          ║\n"
        "╠══════════════════════════════════╣\n"
        f"║  🔍 Searches : {total_searches:<17} ║\n"
        f"║  👥 Users    : {total_users:<17} ║\n"
        f"║  🔒 Mode     : {bot_mode.upper():<17} ║\n"
        f"║  ⏱️ Uptime   : {uptime:<17} ║\n"
        "╚══════════════════════════════════╝"
        "</pre>"
    )
