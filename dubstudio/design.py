"""Crisp, consistent 24px vector icon system for the DubStudio workspace.

These icons are drawn at 3x scale and rasterized by Qt, not by a web view.
All paths use a single stroke family so the interface looks coherent.
"""
from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# Paths are author-created SVG strokes in a common 24x24 coordinate system.
PATHS = {
    'folder': '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    'folder_open': '<path d="M3 7V6a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v3"/><path d="M4 12h17l-3 8H2z"/>',
    'close_project': '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="m9 9 6 6m0-6-6 6"/>',
    'video': '<rect x="3" y="7" width="18" height="14" rx="2"/><path d="m3 12 18-4M7 3l2 5m4-6 2 5m4-6 2 5"/><path d="m10 11 5 3-5 3z"/>',
    'import': '<rect x="3" y="7" width="18" height="14" rx="2"/><path d="m3 12 18-4M7 3l2 5m4-6 2 5m4-6 2 5"/><path d="m10 12 5 3-5 3z"/>',
    'save': '<path d="M4 3h14l3 3v15H3V3h1z"/><path d="M7 3v7h10V3M7 21v-7h10v7"/>',
    'export': '<path d="M11 4h-6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-6"/><path d="M13 3h8v8m0-8-11 11"/>',
    'download': '<path d="M12 3v12m-5-5 5 5 5-5M4 20h16"/>',
    'settings': '<path d="M4 7h16M4 17h16"/><circle cx="9" cy="7" r="2" fill="currentColor"/><circle cx="16" cy="17" r="2" fill="currentColor"/>',
    'help': '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.7 2.7 0 1 1 4.6 2c-1.5 1.1-2.1 1.7-2.1 3"/><path d="M12 17h.01"/>',
    'plus': '<path d="M12 5v14M5 12h14"/>',
    'plus_square': '<rect x="3" y="3" width="18" height="18" rx="4"/><path d="M12 7v10M7 12h10"/>',
    'mic': '<rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0m-7 7v4m-4 0h8"/>',
    'stop': '<rect x="5" y="5" width="14" height="14" rx="3"/>',
    'play': '<path d="m8 5 11 7-11 7z" fill="currentColor" stroke="none"/>',
    'pause': '<rect x="6" y="5" width="4" height="14" rx="1.2" fill="currentColor" stroke="none"/><rect x="14" y="5" width="4" height="14" rx="1.2" fill="currentColor" stroke="none"/>',
    'restart': '<path d="M3 11a9 9 0 1 1 3 7M3 5v6h6"/><path d="m11 9 5 3-5 3z" fill="currentColor" stroke="none"/>',
    'skip_back': '<path d="M5 5v14m14-14L8 12l11 7z"/>',
    'skip_forward': '<path d="M19 5v14M5 5l11 7-11 7z"/>',
    'chevron_left': '<path d="m15 6-6 6 6 6"/>',
    'chevron_right': '<path d="m9 6 6 6-6 6"/>',
    'sun': '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32 1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>',
    'moon': '<path d="M20 15.4A8 8 0 0 1 8.6 4a8.5 8.5 0 1 0 11.4 11.4z"/>',
    'wave': '<path d="M2 10v4M6 5v14M10 9v6m4-11v16m4-13v10m4-7v4"/>',
    'audio': '<path d="M2 9v6m4-11v16m4-13v10m4-13v16m4-11v6m4-8v10"/>',
    'layers': '<path d="m12 2 9 5-9 5-9-5zM3 12l9 5 9-5M3 17l9 5 9-5"/>',
    'file_text': '<path d="M6 2h9l5 5v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z"/><path d="M15 2v5h5M8 12h8m-8 4h8"/>',
    'headphones': '<path d="M4 14v-3a8 8 0 0 1 16 0v3M4 14h3v7H5a2 2 0 0 1-2-2v-3a2 2 0 0 1 1-2zM20 14h-3v7h2a2 2 0 0 0 2-2v-3a2 2 0 0 0-1-2z"/>',
    'edit': '<path d="m4 17 10-10 3 3L7 20H4zM12 9l3 3M14 5l2-2a2 2 0 0 1 3 0l2 2a2 2 0 0 1 0 3l-2 2"/>',
    'scissors': '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M8.5 8.5 20 20M8.5 15.5 20 4"/>',
    'undo': '<path d="M9 14 4 9l5-5M4 9h10a6 6 0 0 1 0 12h-2"/>',
    'redo': '<path d="m15 14 5-5-5-5m5 5H10a6 6 0 0 0 0 12h2"/>',
    'check': '<path d="m4 12 5 5L20 6"/>',
    'volume': '<path d="M4 9h4l5-4v14l-5-4H4zM16 9a5 5 0 0 1 0 6m2-9a9 9 0 0 1 0 12"/>',
    'zoom': '<circle cx="11" cy="11" r="7"/><path d="m16 16 5 5"/>',
}


@lru_cache(maxsize=256)
def icon(kind: str, color: str = '#5d6688') -> QIcon:
    """Render at retina resolution. Cache prevents rerasterization during theme changes."""
    body = PATHS.get(kind, PATHS['plus']).replace('currentColor', color)
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        f'color="{color}" fill="none" stroke="{color}" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round">'
        + body + '</svg>'
    )
    renderer = QSvgRenderer(QByteArray(svg.encode('utf-8')))
    pixmap = QPixmap(72, 72)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(3)
    return QIcon(pixmap)


def stylesheet(dark: bool) -> str:
    """The whole workspace is styled as one desktop system, not separate widgets."""
    if dark:
        palette = dict(
            bg='#1f2233', foreground='#eeecfa', surface='#2a2d42', sidebar='#24273a',
            raised='#32354c', border='#454962', muted='#b3b5ce',
            hint='#999db9', hover='#3b3c57', selected='#433968',
            accent='#c5a6ff', accent_text='#f8f4ff', soft='#35304c',
            video='#111421', wave='#aab4fb', purple='#b695f0', darkshadow='#161626'
        )
    else:
        palette = dict(
            bg='#f5f5fe', foreground='#343a5d', surface='#ffffff', sidebar='#f0efff',
            raised='#f9f8ff', border='#e5e4f5', muted='#69708f',
            hint='#8c93ab', hover='#f1edff', selected='#e9e0ff',
            accent='#7b55df', accent_text='#ffffff', soft='#f4efff',
            video='#151a29', wave='#7ab7f7', purple='#ab82eb', darkshadow='#eae7f4'
        )
    qss = """
    QWidget {
        color: %(foreground)s;
        font-family: 'SF Pro Text', 'SF Pro Display', 'Segoe UI Variable', 'Segoe UI', sans-serif;
        font-size: 13px;
    }
    QMainWindow, QWidget#centralCanvas { background-color: %(bg)s; }
    QWidget#workspaceCanvas, QWidget#canvasBody, QWidget#dialogBody { background: transparent; }
    QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }
    QFrame#workspaceSidebar {
        background: %(sidebar)s; border: 1px solid %(border)s; border-radius: 25px;
    }
    QFrame#topToolbar, QFrame#videoCard, QFrame#referenceCard, QFrame#timelineCard {
        background: %(surface)s; border: 1px solid %(border)s; border-radius: 23px;
    }
    QLabel#brandLogo { background: transparent; border: none; }
    QLabel#sidebarBrand { font-size: 19px; font-weight: 750; }
    QLabel#sidebarEyebrow {
        color: %(hint)s; font-size: 10px; font-weight: 700; letter-spacing: 1px;
    }
    QLabel#sidebarProjectName {
        background: transparent; color: %(foreground)s; font-size: 13px; font-weight: 650;
    }
    QLabel#sidebarProjectDetails {
        background: transparent; color: %(muted)s; font-size: 11px;
    }
    QFrame#sidebarProject {
        background: %(surface)s; border: 1px solid %(border)s; border-radius: 17px;
    }
    QFrame#sidebarHint { background: %(soft)s; border: none; border-radius: 16px; }
    QLabel#brandTitle {
        background: transparent; font-size: 16px; font-weight: 700; color: %(foreground)s;
    }
    QLabel#projectSubtitle, QLabel#recordHint, QLabel#trackSubheading {
        background: transparent; font-size: 11px; color: %(hint)s;
    }
    QLabel#sectionHeading {
        background: transparent; color: %(muted)s; font-size: 11px;
        font-weight: 700; letter-spacing: 0.4px; padding: 1px 2px;
    }
    QLabel#panelHeading {
        background: transparent; color: %(foreground)s; font-size: 14px; font-weight: 650;
    }
    QLabel#clockLabel {
        color: %(muted)s; font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
        font-size: 11px; background: %(raised)s; border-radius: 9px; padding: 6px 9px;
    }
    QPushButton {
        background: %(surface)s; color: %(foreground)s;
        border: 1px solid %(border)s; border-radius: 12px;
        padding: 8px 13px; min-height: 24px;
    }
    QPushButton:hover { background: %(hover)s; border-color: %(accent)s; }
    QPushButton:pressed { background: %(selected)s; }
    QPushButton:disabled { color: %(hint)s; border-color: %(border)s; }
    QPushButton:focus { border-color: %(accent)s; }
    QPushButton#toolbarButton {
        background: %(raised)s; border: 1px solid %(border)s;
        border-radius: 13px; padding: 10px 11px; font-weight: 550;
    }
    QPushButton#toolbarButton:hover { background: %(hover)s; }
    QPushButton#toolbarIcon {
        background: %(raised)s; border: 1px solid %(border)s;
        border-radius: 13px; padding: 7px; min-height: 28px;
    }
    QPushButton#primaryAction, QPushButton#primaryButton {
        background: %(selected)s; border: 1px solid %(accent)s;
        border-radius: 13px; color: %(foreground)s; font-weight: 700;
    }
    QPushButton#primaryAction:hover, QPushButton#primaryButton:hover { background: %(hover)s; }
    QPushButton#sidebarNav {
        background: transparent; border: 1px solid transparent; border-radius: 13px;
        padding: 12px 12px; color: %(muted)s; font-size: 13px;
        font-weight: 600; text-align: left; min-height: 22px;
    }
    QPushButton#sidebarNav:hover { background: %(hover)s; color: %(foreground)s; }
    QPushButton#sidebarNav[selected="true"] {
        background: %(selected)s; color: %(accent)s; border: 1px solid %(border)s;
    }
    QFrame#recordCard {
        background: %(soft)s; border: 1px solid %(border)s; border-radius: 17px;
    }
    QFrame#videoBox {
        background: %(raised)s; border: 1px solid %(border)s; border-radius: 19px;
    }
    QFrame#videoViewer { background: %(video)s; border: none; border-radius: 17px; }
    QPushButton#emptyState {
        background: %(raised)s; border: 1px dashed %(border)s;
        color: %(muted)s; font-weight: 650; font-size: 15px; border-radius: 17px;
    }
    QPushButton#emptyState:hover { background: %(soft)s; border-color: %(accent)s; color: %(accent)s; }
    QPushButton#transportButton, QPushButton#panelIcon {
        background: %(raised)s; border: 1px solid %(border)s;
        border-radius: 12px; padding: 4px; min-height: 28px;
    }
    QPushButton#playAction {
        background: %(accent)s; border: 1px solid %(accent)s;
        border-radius: 14px; padding: 5px; min-height: 32px;
    }
    QPushButton#playAction:hover { background: %(purple)s; }
    QPushButton#record { background: transparent; border: none; padding: 0; min-height: 0; }
    QPushButton#record:hover, QPushButton#record:disabled { background: transparent; border: none; }
    QPushButton#referenceAction {
        background: %(raised)s; border: 1px solid %(border)s;
        border-radius: 11px; padding: 6px 9px;
    }
    QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QDoubleSpinBox, QKeySequenceEdit {
        background: %(raised)s; color: %(foreground)s;
        border: 1px solid %(border)s; border-radius: 12px;
        padding: 9px 12px; selection-background-color: %(selected)s; min-height: 22px;
    }
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QKeySequenceEdit:focus,
    QDoubleSpinBox:focus { background: %(surface)s; border-color: %(accent)s; }
    QComboBox::drop-down { border: none; width: 26px; }
    QGroupBox {
        background: %(surface)s; border: 1px solid %(border)s;
        margin-top: 17px; border-radius: 16px; padding: 17px 12px 12px;
    }
    QGroupBox::title {
        subcontrol-origin: margin; subcontrol-position: top left;
        left: 14px; padding: 0 8px; background: %(surface)s;
    }
    QFrame#dialogSurface {
        background: %(surface)s; border: 1px solid %(border)s; border-radius: 24px;
    }
    QDialog#modernDialog { background: transparent; }
    QFrame#dialogHeader { background: transparent; border: none; }
    QLabel#dialogTitle { font-size: 18px; font-weight: 700; }
    QPushButton#dialogClose {
        background: %(raised)s; color: %(muted)s; border: none;
        border-radius: 15px; padding: 0; font-size: 18px;
    }
    QPushButton#dialogClose:hover { background: %(selected)s; color: %(foreground)s; }
    QLabel#transcriptionStatus {
        background: %(surface)s; color: %(foreground)s;
        border: 1px solid %(border)s; border-radius: 12px; padding: 10px 14px;
    }
    QLabel#modelInfo { color: %(muted)s; font-size: 12px; }
    QSlider::groove:horizontal {
        background: %(border)s; height: 5px; border-radius: 3px;
    }
    QSlider::handle:horizontal {
        background: %(accent)s; border-radius: 8px; width: 16px; margin: -6px 0;
    }
    QScrollBar:horizontal { background: transparent; height: 8px; }
    QScrollBar:vertical { background: transparent; width: 8px; }
    QScrollBar::handle { background: %(hint)s; border-radius: 4px; min-width: 24px; min-height: 24px; }
    QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
    QMenu { background: %(surface)s; border: 1px solid %(border)s; border-radius: 13px; padding: 7px; }
    QMenu::item { padding: 9px 18px; border-radius: 8px; }
    QMenu::item:selected { background: %(selected)s; color: %(accent)s; }
    QToolTip {
        background: %(surface)s; border: 1px solid %(border)s; color: %(foreground)s;
        padding: 6px; border-radius: 8px;
    }
    QDialogButtonBox QPushButton { padding-left: 18px; padding-right: 18px; }
    """
    return qss % palette
