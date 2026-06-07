---
name: sn-query
description: Use when querying ANY ServiceNow table via the Table API. Generic read-only GET wrapper that handles auth, encoding, and formatting. Use this for ad-hoc investigation queries (custom apps, business rules, properties, ACLs, integrations, etc.). For sys_dictionary field schemas, prefer the more specific sn-fields skill.
---

# sn-query — Generic ServiceNow Table API Query

## Overview

Bash wrapper around `GET /api/now/table/<table>`. Handles auth, query encoding, and output formatting. Read-only: never sends POST/PATCH/DELETE.

## Usage

```bash
.claude/skills/sn-query/sn-query.sh <table> [options]
```

**Options:**
| Flag | Meaning | Default |
|---|---|---|
| `--query "<encoded_query>"` | ServiceNow encoded query string | (none — return all) |
| `--fields "f1,f2,f3"` | Comma-separated fields to return | (all fields) |
| `--limit N` | Max rows | `250` |
| `--format md\|json\|csv` | Output format | `md` |
| `--display-value true\|false` | Resolve reference fields to display values | `false` |

## Examples

```bash
# Active custom apps
.claude/skills/sn-query/sn-query.sh sys_app \
  --query "active=true^scope!=global" \
  --fields "name,scope,version,active"

# Business rules touching the incident table
.claude/skills/sn-query/sn-query.sh sys_script \
  --query "active=true^collection=incident" \
  --fields "name,when,order,advanced" --limit 500

# Security properties as JSON for piping
.claude/skills/sn-query/sn-query.sh sys_property \
  --query "nameSTARTSWITHglide.security" \
  --fields "name,value,description" --format json

# Integration inventory as CSV
.claude/skills/sn-query/sn-query.sh sys_rest_message \
  --query "active=true" --fields "name,rest_endpoint" --format csv
```

## Output formats

- **`md`** — pipe-delimited markdown table; cells truncated to 80 chars with `…`
- **`json`** — raw `result` array from the Table API response
- **`csv`** — RFC 4180 CSV with header row

## Setup

Reads credentials from `.env` in the project root (same as `sn-fields`):

```
SN_INSTANCE=https://yourinstance.service-now.com
SN_USERNAME=admin
SN_PASSWORD=yourpassword
```

## Common encoded-query operators

| Operator | Meaning | Example |
|---|---|---|
| `=` | equals | `active=true` |
| `!=` | not equals | `scope!=global` |
| `^` | AND | `active=true^scope!=global` |
| `^OR` | OR | `state=1^ORstate=2` |
| `STARTSWITH` | string prefix | `nameSTARTSWITHglide.security` |
| `LIKE` | substring | `nameLIKEintegration` |
| `ISNOTEMPTY` | non-null | `collectionISNOTEMPTY` |
| `>=javascript:gs.daysAgo(30)` | date relative | `sys_updated_on>=javascript:gs.daysAgoStart(30)` |

## Common Mistakes

- Forgetting `--fields` returns *every* column — slow and noisy. Always specify.
- Using human-readable values without `--display-value true` (e.g., `state=Active` won't match — use `state=1` or enable display values).
- `--limit` defaults to 250; for full-table sweeps pass `--limit 10000` (instance-side cap may still apply).
