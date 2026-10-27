"""Smoke test Qt widget wiring without sound devices, video files or network access."""
import os
import sys
from pathlib import Path
# Running scripts/smoke_ui.py directly does not automatically put the project root on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from dubstudio.ui import Window, ModernDialog, RoundRecordButton

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
