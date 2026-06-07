---
name: sn-fields
description: Use when needing to look up ServiceNow table field schema, map form inputs to database columns, verify field names or types, or identify reference fields before creating catalog variables, business rules, or any artifact that maps to a SN table column.
---

# sn-fields — ServiceNow Table Field Lookup

## Overview

Bash script that queries the ServiceNow `sys_dictionary` REST API and prints a formatted field listing for any table. Use this to map human-readable form fields to actual database column names and types.

## Usage

```bash
# All fields on a table
.claude/skills/sn-fields/sn-fields.sh <table_name>

# Filter to fields matching a keyword (element name or label)
.claude/skills/sn-fields/sn-fields.sh <table_name> <keyword>
```

**Examples:**
```bash
.claude/skills/sn-fields/sn-fields.sh dmn_demand
.claude/skills/sn-fields/sn-fields.sh dmn_demand risk
.claude/skills/sn-fields/sn-fields.sh sc_cat_item_producer name
```

## Setup

Reads credentials from `.env` in the project root:

```
SN_INSTANCE=https://yourinstance.service-now.com
SN_USERNAME=admin
SN_PASSWORD=yourpassword
```

See `.env.example` for format.

## Output Columns

| Column | Meaning |
|---|---|
| `ELEMENT` | Database column name (use this in Record data / `map_to_field`) |
| `TYPE` | `string`, `integer`, `reference`, `glide_date_time`, etc. |
| `REQ` | `true` if field is mandatory at the DB level |
| `MAX` | Max character length |
| `LABEL` | Human-readable column label |
| `[ref]` | For reference fields: the referenced table |

## Common Use Cases

- **Catalog variable `field` mapping** — find the `element` name that matches your question label
- **Record Producer `table_name` field check** — confirm column exists before using `map_to_field: 'true'`
- **Business rule field access** — verify exact column names before scripting GlideRecord logic
- **Reference field discovery** — identify `[ref_table]` for lookup fields

## Common Mistakes

- Using the label (`Business Use Case`) instead of the element (`business_case`) in artifact data
- Filtering by label when the column name uses different keywords — run without filter first
- `internal_type: collection` fields are excluded (not real columns); this is intentional
