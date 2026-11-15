"""Preserve the source project's sibling-directory layout in a frozen build."""
import sys
from pathlib import Path
import settigns
settigns.CURRENT_DIR = Path(sys._MEIPASS) / 'Project' / 'Arcade Odyessy'
