from app.digest.schemas import DigestData

_PERIOD_LABEL = {1: "Today", 7: "This Week"}


def _fmt_move(move) -> str:
    arrow = "▲" if move.pct_change >= 0 else "▼"
    return f"{arrow} {move.item_name} {move.pct_change:+.1f}% (${move.price_then:.2f} -> ${move.price_now:.2f})"


def render_text(digest: DigestData, unsubscribe_url: str | None = None) -> str:
    period_label = _PERIOD_LABEL.get(digest.period_days, f"Last {digest.period_days} Days")
    lines = [f"FARSIGHT — {period_label} in Pokemon TCG", ""]

    if digest.is_empty:
        lines.append("No notable market activity to report right now. Check back next cycle.")
        if unsubscribe_url:
            lines.append(f"\nUnsubscribe: {unsubscribe_url}")
        return "\n".join(lines)

    if digest.trending_cards:
        lines.append("TRENDING CARDS")
        for move in digest.trending_cards:
            lines.append(f"  {_fmt_move(move)}")
        lines.append("")

    if digest.top_movers:
        lines.append("TOP MOVERS")
        for move in digest.top_movers:
            lines.append(f"  {_fmt_move(move)}")
        lines.append("")

    if digest.restocks:
        lines.append("RESTOCKS")
        for r in digest.restocks:
            retailer = f" ({r.retailer})" if r.retailer else ""
            lines.append(f"  * {r.product_name}{retailer}")
        lines.append("")

    if digest.news:
        lines.append("NEWS")
        for n in digest.news:
            lines.append(f"  * {n.title} — {n.url}")
        lines.append("")

    if unsubscribe_url:
        lines.append(f"Unsubscribe: {unsubscribe_url}")

    return "\n".join(lines).rstrip() + "\n"
