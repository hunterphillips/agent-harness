#!/usr/bin/env bash
# sn-fields.sh — Query ServiceNow sys_dictionary for a table's field schema
#
# Usage:
#   .claude/scripts/sn-fields.sh <table_name> [filter_keyword]
#
# Reads credentials from .env in the project root:
#   SN_INSTANCE=https://yourinstance.service-now.com
#   SN_USERNAME=admin
#   SN_PASSWORD=yourpassword

set -euo pipefail

TABLE="${1:-}"
FILTER="${2:-}"

if [[ -z "$TABLE" ]]; then
    echo "Usage: $0 <table_name> [filter_keyword]" >&2
    exit 1
fi

# Load .env from project root (three levels up from .claude/skills/sn-fields/)
ENV_FILE="$(cd "$(dirname "$0")/../../.." && pwd)/.env"
if [[ -f "$ENV_FILE" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ "$line" =~ ^\s*# ]] && continue
        [[ -z "${line// }" ]] && continue
        export "$line"
    done < "$ENV_FILE"
fi

: "${SN_INSTANCE:?SN_INSTANCE not set. Add it to .env}"
: "${SN_USERNAME:?SN_USERNAME not set. Add it to .env}"
: "${SN_PASSWORD:?SN_PASSWORD not set. Add it to .env}"

SN_INSTANCE="${SN_INSTANCE%/}"

QUERY="name=${TABLE}^elementISNOTEMPTY^internal_type!=collection"
FIELDS="element,column_label,internal_type,mandatory,max_length,reference"
ENCODED_QUERY=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$QUERY")
URL="${SN_INSTANCE}/api/now/table/sys_dictionary?sysparm_query=${ENCODED_QUERY}&sysparm_fields=${FIELDS}&sysparm_display_value=false&sysparm_limit=300"

TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

curl -s -u "${SN_USERNAME}:${SN_PASSWORD}" \
    -H "Accept: application/json" \
    "$URL" > "$TMPFILE"

python3 << PYEOF
import json, sys

with open('$TMPFILE') as f:
    data = json.load(f)

if 'error' in data:
    print(f"API Error: {data['error']}", file=sys.stderr)
    sys.exit(1)

fields = data.get('result', [])
keyword = '${FILTER}'.lower()

def val(f, key):
    v = f.get(key, '')
    return v.get('value', '') if isinstance(v, dict) else str(v or '')

fields.sort(key=lambda f: val(f, 'element'))

print(f"Table: ${TABLE}  ({len(fields)} fields)")
print(f"{'ELEMENT':<40} {'TYPE':<14} {'REQ':<5} {'MAX':<7} LABEL")
print('-' * 90)

for f in fields:
    el  = val(f, 'element')
    typ = val(f, 'internal_type')
    mnd = val(f, 'mandatory')
    lbl = val(f, 'column_label')
    mx  = val(f, 'max_length')
    ref = val(f, 'reference')

    if keyword and keyword not in el.lower() and keyword not in lbl.lower():
        continue

    ref_str = f'  [{ref}]' if ref else ''
    req = 'true' if mnd == 'true' else ''
    print(f'{el:<40} {typ:<14} {req:<5} {mx:<7} {lbl}{ref_str}')
PYEOF
