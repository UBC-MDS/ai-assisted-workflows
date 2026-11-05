"""python -m askdb "what was revenue last quarter?" """

import sys

from .pipeline import ask


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__.strip())
        return 2

    result = ask(" ".join(sys.argv[1:]))
    if result["refusal"]:
        print(result["refusal"])
        return 0
    print(result["sql"])
    print()
    print("  " + " | ".join(result["columns"]))
    for row in result["rows"][:20]:
        print("  " + " | ".join(str(c) for c in row))
    if len(result["rows"]) > 20:
        print(f"  ... {len(result['rows']) - 20} more rows")
    print(f"\ntrace {result['trace_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
