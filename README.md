# DubStudio v1.5.0

Free desktop dubbing editor for macOS and Windows. Built from the DubStudio v1.0.1 editable source (Oct 23, 2026).

## v1.5 — Complete desktop interface redesign

This update replaces the actual Qt Widgets workspace layout, not only its colors:

- A consistent vector icon family rendered at Retina resolution (\`dubstudio/design.py\`) for the toolbar, navigation, transport and inspector.
- Working desktop toolbar for Open, Close, Import, Save, Export, Help, Appearance and Preferences; actions switch to icon-only mode on narrower windows.
- New two-column player and reference/recording inspector, and a separate full-width timeline editing panel.
- Sidebar navigation with icons and active-state feedback, with the project summary at the bottom.
- Unified light and dark component styles for every major widget, including dialogs, input controls, menus, and scrollbar details. Removed decorative fake macOS window controls.
- Optional motion preference remains available; existing editing commands, shortcuts, media pipeline, project files and translations are preserved.

The three platforms continue using the Python/PySide6 + native media processing stack. No speculative full-language rewrite was attempted.

## v1.4 — Pastel macOS-inspired interface

- New scalable lavender-and-blue microphone icon (`assets/dubstudio.svg`), included in the sidebar. The build process rasterizes it at 1024 px and produces platform-specific `.icns` / `.ico` files.
- Softer light and dark themes with macOS-like spacing and native macOS Qt widget style.
- Optional **Smooth animations** setting in Preferences, enabled by default and saved locally. It controls hover transitions, dialog content fade, animated sidebar scrolling and a subtle recording pulse. Turning it off stops visual animation work without affecting audio or editing.
- Reduced waveform redraw during media playback: the two tracks update only narrow strips around the previous and current playhead.
- The original Python + Qt architecture stays in place. Media decoding/encoding and Whisper inference already use native libraries (FFmpeg/CTranslate2); this release avoids a risky port without measured bottlenecks.
- Intentionally preserves project format, recordings, media pipeline, actions, translations and editable shortcuts.

## Improvements

- Complete localization of the new workspace/sidebar into Portuguese, English and Japanese, including project summaries, navigation, shortcut help, tooltips, recording warnings and live switching without restart.
- The appearance and dubbing workflow are unchanged; language changes also refresh visible saved-project metadata.


- Maintenance: remove unused imports and an unreferenced legacy splitter; reuse silence buffers while exporting and calculate timeline chapter labels in a single pass. All project formats, shortcuts and editing controls remain unchanged.

- Replaced the unsupported fullwidth plus text symbol on the import-video placeholder with a crisp, painter-rendered Qt icon.

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

Qt (PySide6) desktop UI. This update deliberately preserves the existing project storage and core audio rendering. The SVG is the only icon master in the repository; builds generate the PNG, ICO and ICNS resources from it. Running from Python source uses the SVG directly. Keep a backup of important projects before trying a new build.


## DubStudio v1.3.0 — Refined desktop look

Atualização **apenas de interface**: navegação lateral para as áreas existentes, informações passivas do projeto, cartões arredondados, sombras discretas, superfícies claras e acento rosa. Importação de vídeo, editor, gravação, exportação, transcrição e atalhos mantêm os mesmos comandos.
