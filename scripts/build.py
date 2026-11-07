"""PyInstaller: create one macOS .app or Windows portable exe folder."""
from __future__ import annotations
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICON = ROOT / 'assets' / 'dubstudio.png'
SVG_ICON = ROOT / 'assets' / 'dubstudio.svg'


def render_icon_png():
    """Render the vector master at full resolution for .ico/.icns and bundled Qt resources."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer

    renderer = QSvgRenderer(str(SVG_ICON))
    if not renderer.isValid():
        raise RuntimeError(f'Invalid app icon SVG: {SVG_ICON}')
    image = QImage(1024, 1024, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    try:
        renderer.render(painter)
    finally:
        painter.end()
    if not image.save(str(ICON), 'PNG'):
        raise RuntimeError(f'Could not render app icon: {ICON}')


def build_icon():
    render_icon_png()
    system = platform.system()
    if system == 'Windows':
        from PIL import Image
        target = ROOT / 'assets' / 'dubstudio.ico'
        Image.open(ICON).save(target, sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
        return target
    if system == 'Darwin':
        import shutil
        iconset = ROOT / 'assets' / 'DubStudio.iconset'
        if iconset.exists():
            shutil.rmtree(iconset)
        iconset.mkdir()
        from PIL import Image
        img = Image.open(ICON)
        for size in (16, 32, 128, 256, 512):
            img.resize((size, size), Image.Resampling.LANCZOS).save(iconset / f'icon_{size}x{size}.png')
            if size <= 512:
                img.resize((size * 2, size * 2), Image.Resampling.LANCZOS).save(iconset / f'icon_{size}x{size}@2x.png')
        target = ROOT / 'assets' / 'DubStudio.icns'
        subprocess.run(['iconutil', '-c', 'icns', str(iconset), '-o', str(target)], check=True)
        shutil.rmtree(iconset)
        return target
    return ICON


def main():
    os.chdir(ROOT)
    ico = build_icon()
    args = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
        '--windowed', '--onedir', '--noupx', '--name', 'DubStudio', '--icon', str(ico),
        '--add-data', f'{ICON}{os.pathsep}assets',
        '--add-data', f'{SVG_ICON}{os.pathsep}assets',
        '--hidden-import', 'PySide6.QtSvg',
        '--collect-all', 'imageio_ffmpeg', '--collect-all', 'faster_whisper',
        '--collect-all', 'ctranslate2', '--collect-all', 'tokenizers',
        '--collect-all', 'soundfile', '--collect-all', 'sounddevice',
        '--collect-binaries', 'av',
        '--hidden-import', 'av', '--hidden-import', 'numpy',
        '--hidden-import', 'PySide6.QtMultimedia', '--hidden-import', 'PySide6.QtMultimediaWidgets',
        str(ROOT / 'main.py')]
    subprocess.run(args, check=True)
    print('Build complete in dist/')


if __name__ == '__main__':
    main()
