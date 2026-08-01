---
id: coding-04-greenfield-cli
type: greenfield-cli
weight: 1.0
---
## Task Prompt

Create a Python 3.11+ command-line program named `csv2json.py` using only the standard library. It reads a CSV file given as a positional path, with `-` meaning standard input, and writes UTF-8 JSON to standard output. Default output is one JSON array of row objects. Support `--delimiter CHAR`, `--select NAME[,NAME...]` to retain and order named columns, and `--ndjson` to emit one compact object per line instead of an array. Reject a delimiter that is not one character and requested columns absent from the header with exit code 2 and a useful standard-error message. CSV parse or file errors must also return 2 without a traceback. Preserve cell values as strings and header order. Keep the implementation to `csv2json.py`; an optional `test_csv2json.py` is allowed.
