# DubStudio v1.3.0

Free desktop dubbing editor for macOS and Windows. Built from the DubStudio v1.0.1 editable source (Oct 23, 2026).

## Improvements

- Editable keyboard shortcuts under **Preferences > Keyboard shortcuts > Customize**.
- Original presets retained, restore button, duplicate checking, and persistent custom combinations.
- Cleaner native Qt look, refined dark and light palettes, system typography, subtle borders, and restrained accent colors.
- Automated GitHub Actions builds for **Windows x64**, **macOS Apple Silicon**, and **macOS Intel**.
- Keeps existing `.dubstudio` project file format and original recording / subtitle / export pipeline.

## Downloading compiled applications

Open **Actions > Build DubStudio** in GitHub. Select a successful run and download one of the three artifacts. Each artifact is a ZIP containing a portable Windows application or a macOS DMG. The macOS builds are **not notarized or Developer ID signed**. If Gatekeeper prevents launching, follow Apple's instructions for explicitly opening software from an unidentified developer after verifying its origin.

> GitHub Actions execution and actual macOS/Windows packaging require verification on GitHub-hosted runners. Local Python tests do not prove binary success.

## Building locally

Requires Python 3.11 and OS-specific media libraries.

```shell
python -m pip install -r requirements-build.txt pillow
python -m unittest discover -s tests -v
python scripts/build.py
```

Run from source: `python main.py`.

## Shortcuts

Default project operations use `Ctrl+O`, `Ctrl+S`, `Ctrl+Shift+S`, `Ctrl+W`; platform-native Command combinations are displayed on macOS. Playback defaults: `Space`, `R`, `D`; chapter editing: `M`, `Shift+M`, arrow keys, Enter, Escape; undo/redo: `Ctrl+Z` and `Ctrl+Shift+Z`. Custom shortcuts are stored in Qt's user-local app preferences (`DubStudio/DubStudio`) rather than project files. Entering text in fields takes priority over letter and editing commands.

## Media / transcription

Imports video, supports SRT/VTT/ASS/SSA structures, manual chapter markers, microphone recording, playback, reference notes, multi-part sessions, and output export inherited from v1.0.1. Uses FFmpeg supplied by `imageio-ffmpeg` and optional locally run faster-whisper transcription; the selected language model may be downloaded on first use. No account required.

## Source and compatibility

Qt (PySide6) desktop UI. This update deliberately preserves the existing project storage and core audio rendering. Keep a backup of important projects before trying a new build.


## DubStudio v1.3.0 — Refined desktop look

Atualização **apenas de interface**: navegação lateral para as áreas existentes, informações passivas do projeto, cartões arredondados, sombras discretas, superfícies claras e acento rosa. Importação de vídeo, editor, gravação, exportação, transcrição e atalhos mantêm os mesmos comandos.
