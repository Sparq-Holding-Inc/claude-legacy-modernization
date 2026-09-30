#!/usr/bin/env python3
"""Stop hook. Blocks the stop when a citation does not resolve. STUB (phase 1)."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                                "skills", "modernization-assessment", "scripts"))
import schema  # noqa: E402,F401


def main():
    try:
        json.load(sys.stdin)
    except ValueError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
