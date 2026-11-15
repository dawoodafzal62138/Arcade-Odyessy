# Build with: .venv/bin/python -m PyInstaller --noconfirm ArcadeOdyssey.spec
from pathlib import Path
import os
root = Path(SPECPATH)
projects = ['Arcade Odyessy', 'Flappy-Bird-Game-main', 'Pixel-Runner-game-main',
            'Platform', 'Pong', 'Tiny titan', 'Vampire survivor', 'ninja_game', 'space shooter']
assets = Path(os.environ.get('ARCADE_ASSETS_DIR', str(root.parent / 'assets')))
if not assets.is_dir():
    raise SystemExit('Missing shared artwork. Set ARCADE_ASSETS_DIR to the assets folder.')
datas = []
for name in projects:
    for path in (root / name).rglob('*'):
        if path.is_file() and not any(part in ('__pycache__', '.git', 'docs', 'tests') for part in path.parts) and path.suffix != '.pyc':
            datas.append((str(path), str(Path('Project') / path.relative_to(root).parent)))
datas.append((str(assets), 'assets'))
hidden = ['scripts.' + '.'.join(path.relative_to(root / 'ninja_game' / 'scripts').with_suffix('').parts)
          for path in (root / 'ninja_game' / 'scripts').rglob('*.py') if path.name != '__init__.py']
a = Analysis([str(root / 'Arcade Odyessy' / 'main.py')],
             pathex=[str(root / 'Arcade Odyessy'), str(root / 'ninja_game')],
             binaries=[], datas=datas, hiddenimports=hidden,
             runtime_hooks=[str(root / 'packaging' / 'runtime_paths.py')],
             excludes=['tkinter', 'pytest', 'unittest'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='ArcadeOdyssey',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='ArcadeOdyssey')
