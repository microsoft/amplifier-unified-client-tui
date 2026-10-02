"""Reusable current-client observer helpers; no execution harness."""








import random
import statistics
from pathlib import Path

from benchmark_candidates import summary


def process_tree_rss(pid):
    """Linux point-in-time RSS, including native host/children; not peak or PSS."""
    pending, seen, total = [pid], set(), 0
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        try:
            status = Path(f"/proc/{current}/status").read_text()
            for line in status.splitlines():
                if line.startswith("VmRSS:"):
                    total += int(line.split()[1])
            pending.extend(
                int(value)
                for value in Path(f"/proc/{current}/task/{current}/children").read_text().split()
            )
        except (OSError, ValueError):
            # The observation cannot distinguish a raced exit from denied access.
            return {"rss_kib": None, "processes": len(seen), "complete": False}
    return {"rss_kib": total, "processes": len(seen), "complete": True}


def timing_summary(values):
    result = summary(values)
    rng = random.Random(0)
    medians = sorted(statistics.median(rng.choices(values, k=len(values))) for _ in range(2000))
    result["median_bootstrap_95pct_ms"] = [medians[49], medians[1949]]
    result["uncertainty"] = (
        "Empirical warm samples; percentile median interval, not provider/cold-cache or policy equivalence"
    )
    return result

