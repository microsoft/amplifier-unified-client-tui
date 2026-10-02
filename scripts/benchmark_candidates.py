"""Reusable current-client observer helpers; no execution harness."""






import math
import statistics


def summary(values):
    ordered = sorted(values)
    return {
        "n": len(values),
        "median_ms": statistics.median(values),
        "p95_ms": ordered[math.ceil(len(ordered) * 0.95) - 1],
    }


def editor_contains(display, token):
    """Observe complete ASCII tokens across visual wraps, confined to the editor."""
    tops = [
        i
        for i, line in enumerate(display)
        if ("╭" in line and "Message" in line) or line.strip().startswith("Message ·")
    ]
    if not tops:
        return False
    parts = []
    open_input = "╭" not in display[tops[-1]]
    pad = len(display[tops[-1]]) - len(display[tops[-1]].lstrip())
    for line in display[tops[-1] + 1 :]:
        if "╰" in line or "[ Actions ]" in line:
            break
        if open_input:
            parts.append(line[pad : len(line) - pad if pad else None])
        elif "│" in line:
            parts.append(line.partition("│")[2].rpartition("│")[0])
    return token.strip() in "".join(parts)

