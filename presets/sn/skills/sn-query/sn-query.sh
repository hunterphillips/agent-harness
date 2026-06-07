#!/usr/bin/env bash
# sn-query.sh — Generic ServiceNow Table API GET wrapper.
# See SKILL.md for usage.

set -euo pipefail

# shellcheck source=../_sn-common.sh
source "$(dirname "$0")/../_sn-common.sh"

TABLE=""
QUERY=""
FIELDS=""
LIMIT="250"
FORMAT="md"
DISPLAY_VALUE="false"

usage() {
    cat >&2 <<EOF
Usage: $(basename "$0") <table> [--query "<encoded>"] [--fields "f1,f2"] [--limit N] [--format md|json|csv] [--display-value true|false]
EOF
    exit 1
}

[[ $# -lt 1 ]] && usage
TABLE="$1"
shift

while [[ $# -gt 0 ]]; do
    case "$1" in
        --query)         QUERY="$2"; shift 2 ;;
        --fields)        FIELDS="$2"; shift 2 ;;
        --limit)         LIMIT="$2"; shift 2 ;;
        --format)        FORMAT="$2"; shift 2 ;;
        --display-value) DISPLAY_VALUE="$2"; shift 2 ;;
        -h|--help)       usage ;;
        *) echo "Unknown arg: $1" >&2; usage ;;
    esac
done

case "$FORMAT" in md|json|csv) ;; *) echo "Invalid --format: $FORMAT" >&2; exit 1 ;; esac

sn_load_env

ENCODED_QUERY=""
[[ -n "$QUERY" ]] && ENCODED_QUERY=$(sn_url_encode "$QUERY")

TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT
sn_table_get "$TABLE" "$ENCODED_QUERY" "$FIELDS" "$LIMIT" "$DISPLAY_VALUE" > "$TMPFILE"

JSON_FILE="$TMPFILE" FORMAT="$FORMAT" FIELDS="$FIELDS" TABLE="$TABLE" python3 <<'PYEOF'
import json, os, sys, csv

with open(os.environ['JSON_FILE']) as f:
    data = json.load(f)
if 'error' in data:
    print(f"API Error: {data['error']}", file=sys.stderr); sys.exit(1)

rows = data.get('result', [])
fmt = os.environ['FORMAT']
fields_arg = os.environ['FIELDS']
table = os.environ['TABLE']

# Determine column order: explicit --fields wins; else union of keys preserving first-seen order.
if fields_arg:
    cols = [f.strip() for f in fields_arg.split(',') if f.strip()]
else:
    cols = []
    seen = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k); cols.append(k)

def cell(v):
    if isinstance(v, dict):
        return v.get('display_value') or v.get('value') or ''
    return '' if v is None else str(v)

if fmt == 'json':
    print(json.dumps(rows, indent=2))
    sys.exit(0)

if fmt == 'csv':
    w = csv.writer(sys.stdout)
    w.writerow(cols)
    for r in rows:
        w.writerow([cell(r.get(c, '')) for c in cols])
    sys.exit(0)

# md
def trunc(s, n=80):
    s = s.replace('|', '\\|').replace('\n', ' ')
    return s if len(s) <= n else s[:n-1] + '…'

print(f"Table: `{table}`  ({len(rows)} rows)")
print()
print('| ' + ' | '.join(cols) + ' |')
print('|' + '|'.join('---' for _ in cols) + '|')
for r in rows:
    print('| ' + ' | '.join(trunc(cell(r.get(c, ''))) for c in cols) + ' |')
PYEOF
