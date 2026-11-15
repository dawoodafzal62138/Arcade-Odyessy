# Building Arcade Odyssey

Run from the project root:

```bash
.venv/bin/python -m PyInstaller --noconfirm ArcadeOdyssey.spec
```

Requires PyInstaller, pygame-ce and pytmx in the build environment. The spec packages the hub, all eight minigames, their resources, and the shared artwork in `../assets`. If that artwork is elsewhere, set `ARCADE_ASSETS_DIR` to its directory before building.

Output: `dist/ArcadeOdyssey/ArcadeOdyssey` on Linux, or `dist/ArcadeOdyssey/ArcadeOdyssey.exe` when built on Windows. Distribute the **entire ArcadeOdyssey directory**, including `_internal`. The recipient does not need Python installed.

PyInstaller builds for the operating system where it runs. To produce a Windows executable, build this spec using a Windows Python environment with the same dependencies. This Linux build is not a Windows executable.

The runtime hook preserves the project's sibling folders and existing TMX relative artwork references. Source files are included where adapters need their original directories. Existing high-score files are bundled; game adapters currently save scores inside their game folders, so install/extract the distribution somewhere writable by the player.

Start from a graphical desktop with audio available. Headless verification can check imports and resource loading, but cannot replace playing each game on the target machine.
