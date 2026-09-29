#!/usr/bin/env python3
"""Aggregate Claude Code OpenTelemetry data into plain-text usage tables.

Data source: an OpenTelemetry Collector (otelcol-contrib) `file` exporter with
`format: json`, receiving Claude Code's OTLP metrics and logs. Each line of
`metrics*.jsonl` is one OTLP/JSON ExportMetricsServiceRequest; each line of
`logs*.jsonl` is one ExportLogsServiceRequest. Rotated backups in the same
directory are picked up by the glob.

Point it at the files with `--dir` (default: ~/.claude/otel/):

    python3 eval/usage-report.py                      # last 7 days, all tables
    python3 eval/usage-report.py --days 30 --by skill
    python3 eval/usage-report.py --from 2026-09-01 --to 2026-09-29 --top 20
    python3 eval/usage-report.py --dir eval/fixtures/otel --days 100000

Schema: https://code.claude.com/docs/en/monitoring-usage. Skill, agent, and
plugin names on cost/token metrics are redacted to "custom"/"third-party"
unless Claude Code runs with OTEL_LOG_TOOL_DETAILS=1.
"""

import argparse
import glob
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

# Attribute aliases: the documented key first, then spellings we also accept.
ALIASES = {
    "session": ("session.id", "session_id"),
    "skill": ("skill.name", "skill_name"),
    "agent": ("agent.name", "agent_name", "agent.id"),
    "model": ("model",),
    "type": ("type",),
    "trigger": ("invocation_trigger", "trigger", "invocation_type"),
    "cost": ("cost_usd",),
    "in": ("input_tokens",),
    "out": ("output_tokens",),
    "cache_read": ("cache_read_tokens",),
    "cache_create": ("cache_creation_tokens",),
}

TOKEN_TYPES = {"input": "in", "output": "out", "cacheRead": "cache_read",
               "cacheCreation": "cache_create"}
TOKEN_KEYS = ("in", "out", "cache_read", "cache_create")
NONE = "(none)"

# OTLP AggregationTemporality enum: 1 = DELTA, 2 = CUMULATIVE.
CUMULATIVE = 2


def get(attrs, name, default=None):
    for key in ALIASES.get(name, (name,)):
        if key in attrs and attrs[key] not in (None, ""):
            return attrs[key]
    return default


def any_value(v):
    """Decode an OTLP/JSON AnyValue."""
    if not isinstance(v, dict):
        return v
    if "stringValue" in v:
        return v["stringValue"]
    if "intValue" in v:
        return int(v["intValue"])  # int64 is encoded as a JSON string
    if "doubleValue" in v:
        return float(v["doubleValue"])
    if "boolValue" in v:
        return bool(v["boolValue"])
    if "arrayValue" in v:
        return [any_value(x) for x in v["arrayValue"].get("values", [])]
    if "kvlistValue" in v:
        return attr_dict(v["kvlistValue"].get("values", []))
    return None


def attr_dict(kvs):
    return {kv.get("key"): any_value(kv.get("value")) for kv in kvs or []}


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def local_day(ns):
    return datetime.fromtimestamp(int(ns) / 1e9).date()


class Reader:
    def __init__(self, directory):
        self.dir = directory
        self.bad_lines = Counter()
        self.no_time = 0

    def lines(self, pattern):
        for path in sorted(glob.glob(os.path.join(self.dir, pattern))):
            with open(path, encoding="utf-8", errors="replace") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        if not isinstance(obj, dict):
                            raise ValueError
                    except ValueError:
                        self.bad_lines[os.path.basename(path)] += 1
                        continue
                    yield obj

    def metric_points(self):
        """Yield (metric_name, attrs, value, time_ns) with cumulative series
        converted to deltas."""
        last = {}  # series key -> (start_ns, value) for cumulative sums
        for req in self.lines("metrics*.jsonl"):
            for rm in req.get("resourceMetrics", []) or []:
                res = attr_dict((rm.get("resource") or {}).get("attributes"))
                for sm in rm.get("scopeMetrics", []) or []:
                    for m in sm.get("metrics", []) or []:
                        name = m.get("name")
                        body = m.get("sum") or m.get("gauge") or {}
                        cumulative = body.get("aggregationTemporality") in (CUMULATIVE, "AGGREGATION_TEMPORALITY_CUMULATIVE")
                        for dp in body.get("dataPoints", []) or []:
                            attrs = {**res, **attr_dict(dp.get("attributes"))}
                            ns = dp.get("timeUnixNano")
                            if not ns:
                                self.no_time += 1
                                continue
                            value = num(dp.get("asInt", dp.get("asDouble")))
                            if cumulative:
                                key = (name, tuple(sorted((k, str(v)) for k, v in attrs.items())))
                                start = dp.get("startTimeUnixNano")
                                prev = last.get(key)
                                last[key] = (start, value)
                                if prev and prev[0] == start:
                                    value -= prev[1]
                            yield name, attrs, value, int(ns)

    def events(self):
        """Yield (event_name, attrs, time_ns); event_name has no claude_code. prefix."""
        for req in self.lines("logs*.jsonl"):
            for rl in req.get("resourceLogs", []) or []:
                res = attr_dict((rl.get("resource") or {}).get("attributes"))
                for sl in rl.get("scopeLogs", []) or []:
                    for rec in sl.get("logRecords", []) or []:
                        attrs = {**res, **attr_dict(rec.get("attributes"))}
                        name = attrs.get("event.name") or any_value(rec.get("body")) or ""
                        name = str(name).removeprefix("claude_code.")
                        ns = rec.get("timeUnixNano") or rec.get("observedTimeUnixNano")
                        if not ns or ns == "0":
                            ts = attrs.get("event.timestamp")
                            try:
                                ns = int(datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp() * 1e9)
                            except ValueError:
                                self.no_time += 1
                                continue
                        yield name, attrs, int(ns)


def bucket():
    return {"cost": 0.0, "in": 0.0, "out": 0.0, "cache_read": 0.0,
            "cache_create": 0.0, "sessions": set()}


def aggregate(reader, start, end):
    """Collect usage rows in [start, end] (local dates, inclusive)."""
    usage_metrics = []  # (attrs, day, cost, token_key, amount)
    usage_events = []
    session_counts = 0.0
    activations = defaultdict(Counter)  # skill -> trigger -> n
    sessions_seen = defaultdict(set)    # day -> session ids

    for name, attrs, value, ns in reader.metric_points():
        day = local_day(ns)
        if not start <= day <= end:
            continue
        if sid := get(attrs, "session"):
            sessions_seen[day].add(sid)
        if name == "claude_code.cost.usage":
            usage_metrics.append((attrs, day, value, None, 0))
        elif name == "claude_code.token.usage":
            key = TOKEN_TYPES.get(get(attrs, "type"))
            if key:
                usage_metrics.append((attrs, day, 0.0, key, value))
        elif name == "claude_code.session.count":
            session_counts += value

    for name, attrs, ns in reader.events():
        day = local_day(ns)
        if not start <= day <= end:
            continue
        if sid := get(attrs, "session"):
            sessions_seen[day].add(sid)
        if name == "api_request":
            usage_events.append((attrs, day, num(get(attrs, "cost")), None, 0))
            for key in TOKEN_KEYS:
                usage_events.append((attrs, day, 0.0, key, num(get(attrs, key))))
        elif name == "skill_activated":
            activations[get(attrs, "skill", NONE)][get(attrs, "trigger", "(unknown)")] += 1

    # Cost source: prefer the metrics (delta temporality is Claude Code's
    # default, OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=delta, so
    # data points are summed; cumulative series were converted to deltas in
    # metric_points). Fall back to api_request events when no cost metric
    # exists in range.
    has_cost_metric = any(r[3] is None for r in usage_metrics)
    rows = usage_metrics if has_cost_metric else usage_events
    source = "claude_code.cost.usage / token.usage metrics" if has_cost_metric else "api_request events"

    dims = {d: defaultdict(bucket) for d in ("day", "skill", "agent", "model", "session")}
    totals = bucket()
    session_day = {}
    session_skill_cost = defaultdict(Counter)
    for attrs, day, cost, key, amount in rows:
        sid = get(attrs, "session", NONE)
        keys = {"day": day, "skill": get(attrs, "skill", NONE),
                "agent": get(attrs, "agent", NONE),
                "model": get(attrs, "model", NONE), "session": sid}
        for b in [totals] + [dims[d][k] for d, k in keys.items()]:
            b["cost"] += cost
            if key:
                b[key] += amount
            if sid != NONE:
                b["sessions"].add(sid)
        session_day[sid] = min(day, session_day.get(sid, day))
        session_skill_cost[sid][keys["skill"]] += cost

    for day, sids in sessions_seen.items():
        dims["day"][day]["sessions"] |= sids
        totals["sessions"] |= sids
    for skill in activations:
        dims["skill"][skill]  # ensure activated-but-unbilled skills appear

    return {"totals": totals, "dims": dims, "activations": activations,
            "session_day": session_day, "session_skill_cost": session_skill_cost,
            "session_counts": session_counts, "source": source,
            "empty": not rows and not activations and not sessions_seen}


def table(title, headers, rows):
    print(f"\n{title}")
    if not rows:
        print("  (no rows)")
        return
    cells = [[str(c) for c in r] for r in rows]
    widths = [max(len(h), *(len(r[i]) for r in cells)) for i, h in enumerate(headers)]
    fmt = "  " + "  ".join(f"{{:{'<' if i == 0 else '>'}{w}}}" for i, w in enumerate(widths))
    print(fmt.format(*headers))
    print("  " + "  ".join("-" * w for w in widths))
    for r in cells:
        print(fmt.format(*r))


def usd(x):
    return f"${x:,.4f}" if x < 1 else f"${x:,.2f}"


def tok(x):
    return f"{int(x):,}"


def token_cols(b):
    return [tok(b[k]) for k in TOKEN_KEYS]


TOKEN_HEADERS = ["Input", "Output", "CacheRead", "CacheCreate"]


def by_cost(d):
    return sorted(d.items(), key=lambda kv: (-kv[1]["cost"], str(kv[0])))


def report(agg, which, top):
    t = agg["totals"]
    table("Totals", ["Metric", "Value"], [
        ["Sessions", len(t["sessions"]) or int(agg["session_counts"])],
        ["Cost (USD)", usd(t["cost"])],
        ["Input tokens", tok(t["in"])],
        ["Output tokens", tok(t["out"])],
        ["Cache-read tokens", tok(t["cache_read"])],
        ["Cache-create tokens", tok(t["cache_create"])],
    ])
    d = agg["dims"]
    if which in (None, "day"):
        table("By day", ["Day", "Sessions", "Cost"] + TOKEN_HEADERS,
              [[k.isoformat(), len(b["sessions"]), usd(b["cost"])] + token_cols(b)
               for k, b in sorted(d["day"].items())])
    if which in (None, "skill"):
        acts = agg["activations"]
        rows = []
        for k, b in by_cost(d["skill"]):
            c = acts.get(k, Counter())
            triggers = ", ".join(f"{tr}={n}" for tr, n in c.most_common()) or "-"
            rows.append([k, usd(b["cost"])] + token_cols(b) + [sum(c.values()), triggers])
        table("By skill", ["Skill", "Cost"] + TOKEN_HEADERS + ["Activations", "Triggers"], rows)
    if which in (None, "agent"):
        table("By agent", ["Agent", "Cost"] + TOKEN_HEADERS,
              [[k, usd(b["cost"])] + token_cols(b) for k, b in by_cost(d["agent"])])
    if which in (None, "model"):
        table("By model", ["Model", "Cost"] + TOKEN_HEADERS,
              [[k, usd(b["cost"])] + token_cols(b) for k, b in by_cost(d["model"])])
    if which in (None, "session"):
        rows = []
        for sid, b in by_cost(d["session"])[:top]:
            named = [(s, c) for s, c in agg["session_skill_cost"][sid].most_common() if s != NONE]
            total_tokens = sum(b[k] for k in TOKEN_KEYS)
            rows.append([sid, agg["session_day"].get(sid, ""), usd(b["cost"]),
                         tok(total_tokens), named[0][0] if named else NONE])
        table(f"Top {top} sessions by cost", ["Session", "Date", "Cost", "Tokens", "Top skill"], rows)


def parse_date(s):
    return date.fromisoformat(s)


def main():
    p = argparse.ArgumentParser(description="Claude Code usage report from OTel collector JSONL files.")
    p.add_argument("--dir", default=os.path.expanduser("~/.claude/otel"),
                   help="directory holding metrics*.jsonl and logs*.jsonl (default: ~/.claude/otel)")
    p.add_argument("--days", type=int, help="last N days including today (default 7)")
    p.add_argument("--from", dest="start", type=parse_date, help="start date YYYY-MM-DD (local, inclusive)")
    p.add_argument("--to", dest="end", type=parse_date, help="end date YYYY-MM-DD (local, inclusive)")
    p.add_argument("--by", choices=["day", "skill", "agent", "model", "session"],
                   help="print only this breakdown (default: all)")
    p.add_argument("--top", type=int, default=10, help="sessions to list in the top-sessions table")
    args = p.parse_args()

    today = date.today()
    if args.days is not None and (args.start or args.end):
        p.error("use either --days or --from/--to, not both")
    if args.start or args.end:
        start, end = args.start or date.min, args.end or today
    else:
        days = args.days if args.days is not None else 7
        if days < 1:
            p.error("--days must be at least 1")
        try:
            start = today - timedelta(days=days - 1)
        except OverflowError:
            start = date.min
        end = today
    if start > end:
        p.error("--from is after --to")

    reader = Reader(os.path.expanduser(args.dir))
    agg = aggregate(reader, start, end)

    print(f"Claude Code usage {start.isoformat()} .. {end.isoformat()}  (dir: {reader.dir})")
    if agg["empty"]:
        print("No data for this range.")
    else:
        print(f"Cost/token source: {agg['source']}")
        report(agg, args.by, args.top)

    if reader.bad_lines or reader.no_time:
        print()
        for fname, n in sorted(reader.bad_lines.items()):
            print(f"Skipped {n} malformed line(s) in {fname}")
        if reader.no_time:
            print(f"Skipped {reader.no_time} record(s) without a timestamp")
    return 0


if __name__ == "__main__":
    sys.exit(main())
