"""
GuessMaster Pro
Entry point — launches the desktop application.

Usage:
    python main.py
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from ui import GuessMasterApp


def main():
    app = GuessMasterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
