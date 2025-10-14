import sys

# Read signals_raw.jsonl and output to stdout
with open('data/signals_raw.jsonl', 'rb') as f:
    sys.stdout.buffer.write(f.read())
