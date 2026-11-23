# main.py — entry point for the 23 Nov 2026 front page.
# Pure standard library: draw.py renders the page and writes the PNG.
# The render is deterministic: the same input bytes come out every run.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import draw


def main():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "output")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "entry.png")
    size = draw.write_png(draw.render(), path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
