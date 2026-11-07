"""Smoke test Qt widget wiring without sound devices, video files or network access."""
import os
import sys
from pathlib import Path
# Running scripts/smoke_ui.py directly does not automatically put the project root on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from dubstudio.ui import Window, ModernDialog, RoundRecordButton, MotionButton

# Never open a modal first-run tutorial during unattended CI testing.
QSettings('DubStudio', 'DubStudio').setValue('onboarding/v2/completed', True)
QSettings('DubStudio', 'DubStudio').setValue('appearance/motion_enabled', True)
app = QApplication([])
app.setApplicationName('DubStudio')
w = Window()
w.showMaximized()
app.processEvents()
assert not w.dark, 'The redesigned app should launch in light mode on a clean profile'
assert w.original.handle_at is not None
assert w.empty.objectName() == 'emptyState'
assert isinstance(w.record_btn, RoundRecordButton), 'Recording control must use the circular painted widget'
assert min(w.record_btn.width(), w.record_btn.height()) >= 40, 'Record control must have adequate clickable size'
image = w.record_btn.grab().toImage()
assert image.pixelColor(image.width() // 2, image.height() // 2) != image.pixelColor(0, 0), 'Circle must be visibly different from its corners'
assert not w.empty.icon().isNull(), 'The import action must have a vector plus icon'
assert not any(g in w.empty.text() for g in ('＋', '□', '�')), 'No missing-glyph-prone symbols in import placeholder'
assert 'Importar vídeo' in w.empty.text()
d = ModernDialog(w)
d.setWindowTitle('Keyboard shortcuts')
assert d.heading.text() == 'Keyboard shortcuts'
assert w.video_box.height() >= 300
assert w.sidebar.objectName() == 'workspaceSidebar'
assert len(w.sidebar_nav) == 3
# Regression guard: this is a real layout rewrite, not a palette-only change.
assert w.top_toolbar.objectName() == 'topToolbar'
assert w.video_card.objectName() == 'videoCard'
assert w.reference_card.objectName() == 'referenceCard'
assert w.timeline_card.objectName() == 'timelineCard'
assert w.media_row.count() == 2
assert w.video_card_layout.count() >= 4
assert w.timeline_layout.indexOf(w.track_scroll[0]) >= 0
assert w.timeline_layout.indexOf(w.track_scroll[1]) >= 0
assert w.open_btn.text() == ('' if w.width() < 1310 else w.tr('open_project'))
assert w.save_btn.text() == ('' if w.width() < 1310 else w.tr('toolbar_save'))
assert w.import_btn.icon().isNull() is False
assert w.ref_btn.icon().isNull() is False
assert len({b.property('icon_kind') for b in w.sidebar_nav}) == 3
assert all(not b.icon().isNull() for b in w.sidebar_nav)
assert w.close_project_btn.text() == ''  # icon-only, labelled for accessibility
assert all(isinstance(button, MotionButton) for button in w.sidebar_nav)
assert not w.brand_logo.pixmap().isNull(), 'The new pastel app icon must render in the sidebar'
assert w.animations_enabled, 'Smooth motion should be enabled by default'
w.set_motion_enabled(False)
assert not w.animations_enabled
assert all(not button._motion_enabled for button in w.findChildren(MotionButton))
w.scroll_to_workspace(w.video_box)
assert w._scroll_animation is None or w._scroll_animation.state() == w._scroll_animation.Stopped
w.set_motion_enabled(True)
assert all(button._motion_enabled for button in w.findChildren(MotionButton))
assert w.animations_enabled
assert w.sidebar_project_name.text() == 'Nenhum vídeo aberto'
# A language change must translate every visible sidebar label immediately.
from types import SimpleNamespace
from dubstudio.ui import WORKSPACE_I18N
expected = {
    'pt': ('SEU PROJETO', 'Nenhum vídeo aberto', 'Vídeo original', 'Marcar trecho', 'Seu estúdio de dublagem'),
    'en': ('YOUR PROJECT', 'No video open', 'Source video', 'Mark segment', 'Your dubbing studio'),
    'ja': ('プロジェクト', '動画が開かれていません', '元の動画', '区間をマーク', 'ダビングスタジオ'),
}
assert set(WORKSPACE_I18N) == {'pt', 'en', 'ja'}
assert all(set(WORKSPACE_I18N['pt']) == set(WORKSPACE_I18N[l]) for l in ('en', 'ja'))
for lang, (caption, empty, first_nav, mark_label, title) in expected.items():
    w.ui_language = lang
    w.apply_language()
    app.processEvents()
    assert w.sidebar_project_caption.text() == caption, (lang, 'project caption')
    assert w.sidebar_project_name.text() == empty, (lang, 'project empty state')
    assert w.sidebar_nav[0].text().strip() == first_nav, (lang, 'navigation')
    assert mark_label in w.sidebar_shortcuts.text(), (lang, 'shortcut hints')
    assert w.workspace_title.text() == title, (lang, 'window heading')
    assert w.sidebar_guide_title.text() == w.tr('sidebar_shortcuts_title')
    assert w.sidebar_project_details.text() == w.tr('sidebar_import_hint')
    assert w.help_btn.toolTip() == w.tr('tutorial_button')
    # Loaded project metadata must also be retranslated, without writing to disk.
    w.project = SimpleNamespace(video='', segments=[object(), object()], duration=125.0)
    w.refresh_sidebar_project_info()
    assert w.sidebar_project_name.text() == w.tr('sidebar_project_without_video')
    assert w.sidebar_project_details.text().startswith(w.tr('sidebar_segment_count', count=2))
    w.project = None
    w.apply_language()
w.ui_language = 'pt'
w.apply_language()

w.close()
print('Qt UI smoke test passed')
