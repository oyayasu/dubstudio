"""Render accurate screenshot previews using the real DubStudio Qt widgets."""
import os
import sys
import tempfile
from pathlib import Path

# Keep the screenshot run independent of real user preferences and microphone.
os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp(prefix="dubstudio-preview-")
os.environ["QT_LOGGING_RULES"] = "*.debug=false"
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageEnhance
from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication
from dubstudio.ui import Window, ModernDialog

OUT = ROOT / "previews"
OUT.mkdir(exist_ok=True, parents=True)
app = QApplication([])
app.setApplicationName("DubStudio")
QSettings("DubStudio", "DubStudio").setValue("onboarding/v2/completed", True)
window = Window()
# Xvfb does not provide a window manager: set an explicit desktop viewport.
window.resize(1500, 880)
window.move(0, 0)
window.show()
for _ in range(25):
    app.processEvents()

main_file = OUT / "inicio.png"
if not window.grab().save(str(main_file), "PNG"):
    raise RuntimeError("Unable to render main window")
print("Saved", main_file, flush=True)

def capture_dialog(destination):
    def perform():
        dialogs = [w for w in app.topLevelWidgets() if isinstance(w, ModernDialog) and w.isVisible()]
        if not dialogs:
            QTimer.singleShot(75, perform)
            return
        dlg = dialogs[-1]
        app.processEvents()
        # Real dialog pixels, composited over a dimmed real main-window screenshot.
        tmp = OUT / "_modal.png"
        dlg.grab().save(str(tmp), "PNG")
        main = Image.open(main_file).convert("RGBA")
        overlay = Image.new("RGBA", main.size, (14, 25, 46, 70))
        main = Image.alpha_composite(main, overlay)
        modal = Image.open(tmp).convert("RGBA")
        x = (main.width - modal.width) // 2
        y = (main.height - modal.height) // 2
        main.alpha_composite(modal, (x, y))
        main.convert("RGB").save(OUT / destination, optimize=True)
        tmp.unlink(missing_ok=True)
        dlg.reject()
    QTimer.singleShot(350, perform)

capture_dialog("tutorial.png")
window.show_tutorial(True)
capture_dialog("preferencias.png")
window.preferences()
capture_dialog("atalhos.png")
window.shortcut_settings()
window.close()
app.quit()
print("Saved all Qt UI previews", flush=True)
