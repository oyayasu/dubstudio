"""Smoke test Qt widget wiring without sound devices, video files or network access."""
import os
import sys
from pathlib import Path
# Running scripts/smoke_ui.py directly does not automatically put the project root on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from dubstudio.ui import Window, ModernDialog

app = QApplication([])
app.setApplicationName('DubStudio')
w = Window()
w.showMaximized()
app.processEvents()
assert not w.dark, 'The redesigned app should launch in light mode on a clean profile'
assert w.original.handle_at is not None
assert w.empty.objectName() == 'emptyState'
d = ModernDialog(w)
d.setWindowTitle('Keyboard shortcuts')
assert d.heading.text() == 'Keyboard shortcuts'
assert w.video_box.height() >= 300
assert w.sidebar.objectName() == 'workspaceSidebar'
assert len(w.sidebar_nav) == 3
assert w.sidebar_project_name.text() == 'Nenhum vídeo aberto'
w.close()
print('Qt UI smoke test passed')
