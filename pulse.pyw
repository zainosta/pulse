"""
AI COMMAND CENTER v8 — zero terminals.
Self-manages Ollama. Live tokens/sec from real log. Built-in chat.
"""

import sys, os, re, json, time, subprocess, shutil
import urllib.request
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QSpinBox, QSlider, QFrame, QGraphicsDropShadowEffect,
    QSizeGrip, QComboBox, QScrollArea, QTextEdit, QLineEdit, QMessageBox,
    QTextEdit
)
from PyQt5.QtCore import (
    Qt, QTimer, QRectF, QThread, pyqtSignal, QFileSystemWatcher
)
from PyQt5.QtGui import (
    QColor, QPainter, QPainterPath, QRadialGradient, QPen, QBrush,
    QTextCursor, QFont
)

# ================================================================
#  CONFIG
# ================================================================
TMP = os.environ.get("TEMP", os.path.expanduser("~"))
LOG_PATH = os.path.join(TMP, "ai_command_center_ollama.log")
LOG_STALE_SECONDS = 12

TG_RE   = re.compile(r"tg\s*=\s*([\d.]+)\s*t/s")
EVAL_RE = re.compile(r"eval time\s*=.*?([\d.]+)\s*tokens\s+per\s+second")

DEFAULT_MODEL = "hermes3:8b"

NO_WINDOW = 0x08000000   # subprocess.CREATE_NO_WINDOW


# ================================================================
#  OLLAMA MANAGER — spawns and controls ollama silently
# ================================================================
def find_ollama():
    """Locate ollama.exe — PATH first, then common install dirs."""
    candidates = []
    p = shutil.which("ollama")
    if p:
        candidates.append(p)
    home = os.path.expanduser("~")
    candidates += [
        os.path.join(home, r"AppData\Local\Programs\Ollama\ollama.exe"),
        r"C:\Program Files\Ollama\ollama.exe",
        r"C:\Program Files (x86)\Ollama\ollama.exe",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def kill_running_ollama():
    """Kill tray app + CLI + any leftover serve process."""
    for image in ("ollama app.exe", "ollama.exe"):
        subprocess.run(
            ["taskkill", "/F", "/IM", image],
            capture_output=True, creationflags=NO_WINDOW
        )


def wait_for_api(timeout=15.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(
                "http://localhost:11434/api/tags", timeout=1
            ) as r:
                r.read()
            return True
        except Exception:
            time.sleep(0.3)
    return False


class OllamaManager:
    """Owns the background ollama serve process."""
    def __init__(self):
        self.proc = None
        self.log_fh = None
        self.ollama_path = None

    def setup(self):
        self.ollama_path = find_ollama()
        if not self.ollama_path:
            return False, ("Ollama not found.\n\nInstall from https://ollama.com "
                           "then run this app again.")

        kill_running_ollama()
        time.sleep(0.8)   # let processes fully die

        try:
            self.log_fh = open(LOG_PATH, "w",
                               encoding="utf-8", errors="ignore", buffering=1)
        except Exception as e:
            return False, f"Cannot open log file: {e}"

        try:
            self.proc = subprocess.Popen(
                [self.ollama_path, "serve"],
                stdout=self.log_fh,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                creationflags=NO_WINDOW,
            )
        except Exception as e:
            return False, f"Cannot start ollama serve: {e}"

        if not wait_for_api(15):
            return False, ("Ollama started but API never responded. "
                           "Try restarting the app.")

        return True, "Ready"

    def shutdown(self):
        if self.proc and self.proc.poll() is None:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(self.proc.pid)],
                    capture_output=True, creationflags=NO_WINDOW
                )
            except Exception:
                try: self.proc.terminate()
                except Exception: pass
        if self.log_fh:
            try: self.log_fh.close()
            except Exception: pass


# ================================================================
#  LOG READER  (real tokens/sec)
# ================================================================
def read_log_tokens():
    if not os.path.exists(LOG_PATH):
        return None, 999
    try:
        age = time.time() - os.path.getmtime(LOG_PATH)
        with open(LOG_PATH, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            if size == 0:
                return None, age
            block = min(size, 40000)
            f.seek(-block, os.SEEK_END)
            tail = f.read().decode("utf-8", errors="ignore")

        for line in reversed(tail.splitlines()):
            m = TG_RE.search(line)
            if m:
                return float(m.group(1)), age
        for line in reversed(tail.splitlines()):
            m = EVAL_RE.search(line)
            if m:
                return float(m.group(1)), age
        return None, age
    except Exception:
        return None, 999


def count_loaded_models():
    try:
        with urllib.request.urlopen(
            "http://localhost:11434/api/ps", timeout=1
        ) as r:
            return len(json.loads(r.read().decode()).get("models", []))
    except Exception:
        return 0


def list_installed_models():
    try:
        with urllib.request.urlopen(
            "http://localhost:11434/api/tags", timeout=1
        ) as r:
            data = json.loads(r.read().decode())
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


class LogReader(QThread):
    got = pyqtSignal(object, float)
    def run(self):
        v, age = read_log_tokens()
        self.got.emit(v, age)


class ModelsReader(QThread):
    got = pyqtSignal(int, list)
    def run(self):
        self.got.emit(count_loaded_models(), list_installed_models())


# ================================================================
#  CHAT WORKER — streams from Ollama API
# ================================================================
class ChatWorker(QThread):
    chunk = pyqtSignal(str)
    finished_ok = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, model, messages):
        super().__init__()
        self.model = model
        self.messages = messages
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        payload = json.dumps({
            "model": self.model,
            "messages": self.messages,
            "stream": True,
        }).encode()

        try:
            req = urllib.request.Request(
                "http://localhost:11434/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                for raw in resp:
                    if self._stop:
                        break
                    if not raw.strip():
                        continue
                    try:
                        data = json.loads(raw.decode("utf-8"))
                    except Exception:
                        continue
                    if data.get("done"):
                        self.finished_ok.emit()
                        return
                    content = data.get("message", {}).get("content", "")
                    if content:
                        self.chunk.emit(content)
            self.finished_ok.emit()
        except Exception as e:
            self.error.emit(str(e))


# ================================================================
#  COLORS
# ================================================================
CYAN      = "#00ffc3"
BLUE      = "#0088ff"
SOFT_GLOW = "#4db8ff"
RED_GLOW  = "#ff5577"
DIM       = "#2a3d4a"
OK_GREEN  = "#00ff88"
TEXT_MAIN = "#dff9f0"


# ================================================================
#  CHAT WINDOW
# ================================================================
class ChatWindow(QWidget):
    def __init__(self, initial_model=DEFAULT_MODEL):
        super().__init__(None)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(440, 520)
        self.resize(480, 620)

        self.drag_pos = None
        self.messages = []   # list of {role, content}
        self.worker = None

        self._build()

    # ----------------------------------------------
    def _build(self):
        wrap = QVBoxLayout(self); wrap.setContentsMargins(0, 0, 0, 0)
        frame = QFrame(self); frame.setObjectName("cf")
        frame.setStyleSheet(f"""
            #cf {{ background: rgba(5,18,24,248);
                   border: 1px solid {CYAN}; border-radius: 18px; }}
            QLabel {{ color:#a0f0e0; font-size:11px; background:transparent; }}
            QComboBox {{ background: rgba(0,30,40,220);
                         border:1px solid {CYAN}; border-radius:12px;
                         padding:5px 10px; color:#d0fff0;
                         font-weight:600; font-size:11px; min-width:180px; }}
            QTextEdit {{ background: rgba(2,10,15,200);
                         border:1px solid #123; border-radius:10px;
                         color:{TEXT_MAIN}; font-size:13px;
                         padding:8px; }}
            QLineEdit {{ background: rgba(0,30,40,220);
                         border:1px solid {CYAN}; border-radius:12px;
                         padding:8px 12px; color:#e0fff0; font-size:13px; }}
            QPushButton#send {{ background: rgba(0,255,200,40);
                                border:1px solid {CYAN}; border-radius:12px;
                                color:#e0fff0; padding:8px 16px;
                                font-weight:600; font-size:12px; }}
            QPushButton#send:hover {{ background: rgba(0,255,200,90); color:#fff; }}
            QPushButton#x {{ background: rgba(255,80,100,30);
                             border:1px solid {RED_GLOW}; border-radius:10px;
                             color:{RED_GLOW}; font-size:12px; font-weight:bold; }}
            QPushButton#x:hover {{ background: rgba(255,80,100,80); color:#fff; }}
            QPushButton#clear {{ background: rgba(0,255,200,10);
                                 border:1px solid #2a9d8f; border-radius:10px;
                                 color:#a0f0e0; font-size:10px; padding:5px 10px; }}
            QPushButton#clear:hover {{ background: rgba(0,255,200,50); color:#fff; }}
        """)
        wrap.addWidget(frame)

        v = QVBoxLayout(frame)
        v.setContentsMargins(16, 14, 16, 14); v.setSpacing(10)

        # header
        header = QHBoxLayout()
        title = QLabel("◉ HERMES CHAT")
        title.setStyleSheet(f"color:{CYAN}; letter-spacing:3px; font-size:12px;")
        header.addWidget(title)
        header.addStretch(1)

        self.model_combo = QComboBox()
        installed = list_installed_models()
        if not installed:
            installed = [DEFAULT_MODEL]
        self.model_combo.addItems(installed)
        # prefer hermes3:8b
        for i, m in enumerate(installed):
            if "hermes" in m.lower():
                self.model_combo.setCurrentIndex(i); break
        header.addWidget(self.model_combo)

        btn_clear = QPushButton("clear"); btn_clear.setObjectName("clear")
        btn_clear.clicked.connect(self._clear)
        header.addWidget(btn_clear)

        btn_x = QPushButton("✕"); btn_x.setObjectName("x"); btn_x.setFixedSize(28, 28)
        btn_x.clicked.connect(self.hide)
        header.addWidget(btn_x)
        v.addLayout(header)

        # chat area
        self.view = QTextEdit(); self.view.setReadOnly(True)
        self.view.setStyleSheet(
            f"QTextEdit {{ background: rgba(2,10,15,220); border:1px solid #0a5c55; "
            f"border-radius:12px; color:{TEXT_MAIN}; font-size:13px; padding:10px; }}"
        )
        v.addWidget(self.view, 1)

        # input row
        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask Hermes anything…  (Enter to send)")
        self.input.returnPressed.connect(self._send)
        row.addWidget(self.input, 1)

        self.btn_send = QPushButton("SEND"); self.btn_send.setObjectName("send")
        self.btn_send.clicked.connect(self._send)
        row.addWidget(self.btn_send)
        v.addLayout(row)

        self._append_system("Connected. Type a message below to chat with your model.")

    # ----------------------------------------------
    def _append_system(self, text):
        self.view.append(f'<span style="color:#4a7f7a; font-style:italic">▸ {text}</span>')
        self.view.moveCursor(QTextCursor.End)

    def _append_user(self, text):
        self.view.append(
            f'<div style="margin-top:8px; color:{CYAN}; font-weight:700; '
            f'letter-spacing:1px">YOU</div>'
        )
        esc = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.view.append(f'<div style="color:#e0fff0; margin-bottom:6px">{esc}</div>')
        self.view.moveCursor(QTextCursor.End)

    def _append_ai_header(self):
        self.view.append(
            f'<div style="margin-top:8px; color:{BLUE}; font-weight:700; '
            f'letter-spacing:1px">HERMES</div>'
        )
        self.view.moveCursor(QTextCursor.End)

    def _append_ai_chunk(self, chunk):
        esc = chunk.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.view.moveCursor(QTextCursor.End)
        self.view.insertHtml(
            f'<span style="color:#dff9f0; white-space:pre-wrap">{esc}</span>'
        )
        self.view.moveCursor(QTextCursor.End)

    # ----------------------------------------------
    def _clear(self):
        self.messages = []
        self.view.clear()
        self._append_system("Conversation cleared.")

    def _send(self):
        text = self.input.text().strip()
        if not text:
            return
        if self.worker and self.worker.isRunning():
            return

        self.input.clear()
        self._append_user(text)
        self.messages.append({"role": "user", "content": text})
        self._append_ai_header()

        model = self.model_combo.currentText()
        self.worker = ChatWorker(model, list(self.messages))
        self.worker.chunk.connect(self._append_ai_chunk)
        self.worker.finished_ok.connect(self._on_done)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_done(self):
        # capture final AI text from current buffer
        # (we keep it simple; the streamed text is already in the view)
        if self.messages and self.messages[-1]["role"] == "assistant":
            pass
        # we don't track exactly; append a subtle end marker
        self.view.append('<div style="height:4px"></div>')
        self.view.moveCursor(QTextCursor.End)

    def _on_error(self, msg):
        self._append_system(f"ERROR: {msg}")

    # ----------------------------------------------
    # window drag
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.drag_pos = e.globalPos() - self.frameGeometry().topLeft()
            e.accept()
    def mouseMoveEvent(self, e):
        if self.drag_pos and e.buttons() & Qt.LeftButton:
            self.move(e.globalPos() - self.drag_pos); e.accept()
    def mouseReleaseEvent(self, e):
        self.drag_pos = None

    def closeEvent(self, e):
        e.ignore(); self.hide()


# ================================================================
#  SETTINGS WINDOW
# ================================================================
class SettingsWindow(QWidget):
    def __init__(self, dash):
        super().__init__(None)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.dash = dash
        self.drag_pos = None
        self._placed_once = False
        self._build()
        self.adjustSize()

    def _build(self):
        frame = QFrame(self); frame.setObjectName("sf")
        frame.setStyleSheet(f"""
            #sf {{ background: rgba(5,18,24,245);
                   border: 1px solid {CYAN}; border-radius: 16px; }}
            QLabel {{ color:#a0f0e0; font-size:11px; background:transparent; }}
            QPushButton {{ background: rgba(0,255,200,15);
                           border: 1px solid #2a9d8f; color:#a0f0e0;
                           border-radius:10px; padding:5px 10px; font-size:11px; }}
            QPushButton:hover {{ background: rgba(0,255,200,60);
                                 border-color:{CYAN}; color:#fff; }}
            QSpinBox, QComboBox {{ background: rgba(0,30,40,220);
                                   border:1px solid {CYAN}; border-radius:12px;
                                   padding:4px 8px; color:#d0fff0;
                                   font-weight:600; font-size:11px; min-width:80px; }}
            QSlider::groove:horizontal {{ height:4px;
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {CYAN}, stop:1 {BLUE}); border-radius:2px; }}
            QSlider::handle:horizontal {{ background:#fff; width:14px; height:14px;
                margin:-6px 0; border-radius:7px; }}
        """)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.addWidget(frame)
        inner = QVBoxLayout(frame); inner.setContentsMargins(16, 14, 16, 14); inner.setSpacing(10)

        tr = QHBoxLayout()
        t = QLabel("⌁ SETTINGS ⌁")
        t.setStyleSheet(f"color:{CYAN}; letter-spacing:3px; font-size:12px;")
        tr.addWidget(t); tr.addStretch(1)
        bx = QPushButton("✕"); bx.setFixedSize(24, 24); bx.clicked.connect(self.hide)
        tr.addWidget(bx); inner.addLayout(tr)

        r1 = QHBoxLayout(); r1.addWidget(QLabel("refresh (ms)"))
        self.spin = QSpinBox(); self.spin.setRange(100, 10000); self.spin.setSingleStep(100)
        self.spin.setValue(self.dash.refresh_ms); self.spin.valueChanged.connect(self._on_r)
        r1.addWidget(self.spin); inner.addLayout(r1)

        r2 = QHBoxLayout(); r2.addWidget(QLabel("shape"))
        self.combo = QComboBox(); self.combo.addItems(["circle", "squircle", "hex", "diamond"])
        self.combo.setCurrentText(self.dash.shape); self.combo.currentTextChanged.connect(self._on_s)
        r2.addWidget(self.combo); inner.addLayout(r2)

        r3 = QHBoxLayout(); r3.addWidget(QLabel("size"))
        self.slider = QSlider(Qt.Horizontal); self.slider.setRange(200, 600)
        self.slider.setValue(self.dash.size_px)
        self.slider.valueChanged.connect(self._on_z)
        r3.addWidget(self.slider)
        self.sz = QLabel(f"{self.dash.size_px}px"); self.sz.setFixedWidth(50)
        self.sz.setAlignment(Qt.AlignRight); r3.addWidget(self.sz); inner.addLayout(r3)

        info = QLabel("log: " + os.path.basename(LOG_PATH))
        info.setStyleSheet("color:#4a7f7a; font-size:9px; padding-top:4px;")
        inner.addWidget(info)

        bq = QPushButton("quit app"); bq.clicked.connect(self.dash.close)
        inner.addWidget(bq)

    def _on_r(self, v): self.dash.refresh_ms = v; self.dash.data_timer.setInterval(v)
    def _on_s(self, s): self.dash.shape = s; self.dash.update()
    def _on_z(self, v):
        self.dash.size_px = v
        self.dash._set_size_no_move(v)
        self.sz.setText(f"{v}px")

    def showEvent(self, e):
        if not self._placed_once:
            g = self.dash.frameGeometry()
            self.adjustSize()
            self.move(g.right() + 20, g.top() + 40)
            self._placed_once = True
        super().showEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.drag_pos = e.globalPos() - self.frameGeometry().topLeft(); e.accept()
    def mouseMoveEvent(self, e):
        if self.drag_pos and e.buttons() & Qt.LeftButton:
            self.move(e.globalPos() - self.drag_pos); e.accept()
    def mouseReleaseEvent(self, e): self.drag_pos = None
    def closeEvent(self, e): e.ignore(); self.hide()


# ================================================================
#  MAIN DASHBOARD
# ================================================================
class FloatingDashboard(QWidget):
    def __init__(self, ollama_mgr):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.ollama_mgr = ollama_mgr
        self.shape = "circle"
        self.size_px = 380
        self.refresh_ms = 400
        self.drag_pos = None
        self.models = 0
        self.tokens = None
        self.log_age = 999
        self._log_reader = None
        self._models_reader = None

        self.resize(self.size_px, self.size_px)
        self.settings_window = SettingsWindow(self)
        self.chat_window = ChatWindow()
        self._build_ui()

        # data poll
        self.data_timer = QTimer(self)
        self.data_timer.timeout.connect(self.refresh_data)
        self.data_timer.start(self.refresh_ms)

        # file watcher — instant updates
        self.watcher = QFileSystemWatcher(self)
        self._attach_watcher()
        self.watcher.fileChanged.connect(self._on_log_changed)

        # debounce for resize style updates
        self._resize_debounce = QTimer(self)
        self._resize_debounce.setSingleShot(True)
        self._resize_debounce.timeout.connect(self._apply_styles)

        # pulse
        self.pulse_phase = 0
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._pulse)
        self.pulse_timer.start(60)

        QTimer.singleShot(200, self.refresh_data)
        self._center()

    def _attach_watcher(self):
        if os.path.exists(LOG_PATH) and LOG_PATH not in self.watcher.files():
            self.watcher.addPath(LOG_PATH)

    def _on_log_changed(self, path):
        QTimer.singleShot(80, self._attach_watcher)
        self.refresh_data()

    # ----------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 42, 30, 30); root.setSpacing(0)

        top = QHBoxLayout()

        # chat button
        self.btn_chat = QPushButton("💬", self); self.btn_chat.setFixedSize(28, 28)
        self.btn_chat.setCursor(Qt.PointingHandCursor)
        self.btn_chat.clicked.connect(self._toggle_chat)
        self.btn_chat.setStyleSheet(f"""
            QPushButton {{ background: rgba(0,255,200,25); border: 1px solid {CYAN};
                           border-radius: 14px; color: {CYAN};
                           font-size: 13px; }}
            QPushButton:hover {{ background: rgba(0,255,200,70); color: #fff; }}
        """)
        self._glow(self.btn_chat, CYAN, 12)

        self.btn_gear = QPushButton("⚙", self); self.btn_gear.setFixedSize(28, 28)
        self.btn_gear.setCursor(Qt.PointingHandCursor)
        self.btn_gear.clicked.connect(self._toggle_settings)
        self.btn_gear.setStyleSheet(f"""
            QPushButton {{ background: rgba(0,255,200,25); border: 1px solid {CYAN};
                           border-radius: 14px; color: {CYAN};
                           font-size: 14px; font-weight: bold; }}
            QPushButton:hover {{ background: rgba(0,255,200,70); color: #fff; }}
        """)

        self.btn_close = QPushButton("✕", self); self.btn_close.setFixedSize(28, 28)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self.close)
        self.btn_close.setStyleSheet(f"""
            QPushButton {{ background: rgba(255,80,100,30); border: 1px solid {RED_GLOW};
                           border-radius: 14px; color: {RED_GLOW};
                           font-size: 13px; font-weight: bold; }}
            QPushButton:hover {{ background: rgba(255,80,100,80); color:#fff; }}
        """)

        top.addWidget(self.btn_chat)
        top.addWidget(self.btn_gear)
        top.addStretch(1)
        top.addWidget(self.btn_close)

        self.lbl_models_title = QLabel("AI MODELS"); self.lbl_models_title.setAlignment(Qt.AlignCenter)
        self.lbl_models_value = QLabel("0"); self.lbl_models_value.setAlignment(Qt.AlignCenter)
        self._glow(self.lbl_models_value, CYAN, 30)

        self.lbl_tokens_title = QLabel("TOKENS / SEC"); self.lbl_tokens_title.setAlignment(Qt.AlignCenter)
        self.lbl_tokens_value = QLabel("—"); self.lbl_tokens_value.setAlignment(Qt.AlignCenter)
        self._glow(self.lbl_tokens_value, DIM, 8)

        self.lbl_status = QLabel("starting…")
        self.lbl_status.setAlignment(Qt.AlignCenter)

        self.pulse_row = QHBoxLayout(); self.pulse_row.setSpacing(6)
        self.pulse_row.setAlignment(Qt.AlignCenter); self.dot_widgets = []
        for _ in range(4):
            d = QLabel("●"); self._glow(d, CYAN, 12); self.dot_widgets.append(d)
            self.pulse_row.addWidget(d)

        root.addLayout(top); root.addStretch(1)
        root.addWidget(self.lbl_models_title); root.addWidget(self.lbl_models_value)
        root.addSpacing(10)
        root.addWidget(self.lbl_tokens_title); root.addWidget(self.lbl_tokens_value)
        root.addSpacing(6)
        root.addWidget(self.lbl_status)
        root.addSpacing(4)
        root.addLayout(self.pulse_row); root.addStretch(1)

        self.grip = QSizeGrip(self)
        self.grip.setStyleSheet("background:transparent;")
        self.grip.setFixedSize(20, 20)
        self._apply_styles()

    # ----------------------------------------------
    def _apply_styles(self):
        base = self.size_px
        ft = max(9, int(base / 38)); fv = max(28, int(base / 6))
        fs = max(8, int(base / 55))
        self.lbl_models_title.setStyleSheet(
            f"color:{CYAN}; letter-spacing:4px; font-weight:300; "
            f"font-size:{ft}px; background:transparent;")
        self.lbl_tokens_title.setStyleSheet(
            f"color:{CYAN}; letter-spacing:4px; font-weight:300; "
            f"font-size:{ft}px; background:transparent;")
        self.lbl_models_value.setStyleSheet(
            f"color:#e0fff0; font-weight:800; letter-spacing:-1px; "
            f"font-size:{fv}px; background:transparent;")
        self.lbl_status.setStyleSheet(
            f"color:#4a7f7a; letter-spacing:1px; "
            f"font-size:{fs}px; background:transparent;")

    def _glow(self, w, c, r):
        e = QGraphicsDropShadowEffect(self); e.setBlurRadius(r)
        e.setColor(QColor(c)); e.setOffset(0, 0); w.setGraphicsEffect(e)

    def _set_size_no_move(self, v):
        self.size_px = v
        self.setFixedSize(v, v)
        self._resize_debounce.start(120)

    # ----------------------------------------------
    def _toggle_settings(self):
        if self.settings_window.isVisible(): self.settings_window.hide()
        else:
            self.settings_window.show(); self.settings_window.raise_()

    def _toggle_chat(self):
        if self.chat_window.isVisible():
            self.chat_window.hide()
        else:
            g = self.frameGeometry()
            self.chat_window.move(g.right() + 20, g.top())
            self.chat_window.show(); self.chat_window.raise_()

    # ----------------------------------------------
    def refresh_data(self):
        if self._log_reader is None or not self._log_reader.isRunning():
            self._log_reader = LogReader(self)
            self._log_reader.got.connect(self._on_log_data)
            self._log_reader.start()
        if self._models_reader is None or not self._models_reader.isRunning():
            self._models_reader = ModelsReader(self)
            self._models_reader.got.connect(self._on_models_data)
            self._models_reader.start()

    def _on_log_data(self, tokens, age):
        self.tokens = tokens; self.log_age = age
        self._paint_tokens()

    def _on_models_data(self, count, installed):
        self.models = count
        self.lbl_models_value.setText(str(count))

    def _paint_tokens(self):
        fv = max(28, int(self.size_px / 6))
        fs = max(8, int(self.size_px / 55))
        if self.tokens is None or self.log_age > LOG_STALE_SECONDS:
            self.lbl_tokens_value.setText("—")
            self.lbl_tokens_value.setStyleSheet(
                f"color:{DIM}; font-weight:800; letter-spacing:-1px; "
                f"font-size:{fv}px; background:transparent;")
            self._glow(self.lbl_tokens_value, DIM, 8)
            self.lbl_status.setText("idle — send a chat to see live rate")
            self.lbl_status.setStyleSheet(
                f"color:#4a7f7a; letter-spacing:1px; font-size:{fs}px; background:transparent;")
            for d in self.dot_widgets: d.setVisible(False)
        else:
            self.lbl_tokens_value.setText(f"{self.tokens:.1f}")
            self.lbl_tokens_value.setStyleSheet(
                f"color:#e0fff0; font-weight:800; letter-spacing:-1px; "
                f"font-size:{fv}px; background:transparent;")
            self._glow(self.lbl_tokens_value, BLUE, 30)
            self.lbl_status.setText(f"LIVE · log updated {self.log_age:.1f}s ago")
            self.lbl_status.setStyleSheet(
                f"color:{OK_GREEN}; letter-spacing:1px; font-size:{fs}px; background:transparent;")
            for d in self.dot_widgets: d.setVisible(True)

    def _pulse(self):
        if self.tokens is None or self.log_age > LOG_STALE_SECONDS:
            return
        self.pulse_phase = (self.pulse_phase + 1) % 20
        cols = [CYAN, SOFT_GLOW, BLUE, CYAN]
        for i, d in enumerate(self.dot_widgets):
            ph = (self.pulse_phase + i * 5) % 20
            a = 80 + int(175 * abs(ph - 10) / 10)
            c = QColor(cols[i])
            d.setStyleSheet(
                f"color: rgba({c.red()},{c.green()},{c.blue()},{a}); "
                f"font-size:12px; background:transparent;")
            self._glow(d, cols[i], 15)

    # ----------------------------------------------
    def _shape_path(self, rect):
        p = QPainterPath()
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        if self.shape == "circle": p.addEllipse(rect)
        elif self.shape == "squircle": p.addRoundedRect(QRectF(x, y, w, h), w * 0.28, h * 0.28)
        elif self.shape == "hex":
            import math
            cx, cy = x + w / 2, y + h / 2; rad = min(w, h) / 2
            pts = []
            for i in range(6):
                a = math.pi / 3 * i - math.pi / 2
                pts.append((cx + rad * 0.92 * math.cos(a), cy + rad * 0.92 * math.sin(a)))
            p.moveTo(*pts[0])
            for q in pts[1:]: p.lineTo(*q)
            p.closeSubpath()
        elif self.shape == "diamond":
            cx, cy = x + w / 2, y + h / 2
            p.moveTo(cx, y + 10); p.lineTo(x + w - 10, cy)
            p.lineTo(cx, y + h - 10); p.lineTo(x + 10, cy); p.closeSubpath()
        return p

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(4, 4, self.width() - 8, self.height() - 8)
        path = self._shape_path(rect)
        for i, (col, al, wd) in enumerate([(CYAN, 40, 6), (BLUE, 25, 12), (CYAN, 12, 20)]):
            c = QColor(col); c.setAlpha(al)
            p.setPen(QPen(c, wd)); p.setBrush(Qt.NoBrush)
            ex = i * 2
            r2 = QRectF(rect.x() - ex, rect.y() - ex, rect.width() + ex * 2, rect.height() + ex * 2)
            p.drawPath(self._shape_path(r2))
        g = QRadialGradient(rect.center(), rect.width() * 0.7)
        g.setColorAt(0.0, QColor(0, 255, 195, 30))
        g.setColorAt(0.6, QColor(0, 100, 150, 25))
        g.setColorAt(1.0, QColor(3, 5, 12, 220))
        p.setBrush(QBrush(g)); p.setPen(QPen(QColor(CYAN), 2)); p.drawPath(path)
        super().paintEvent(e)

    # ----------------------------------------------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            for b in (self.btn_chat, self.btn_gear, self.btn_close):
                if b.geometry().contains(e.pos()):
                    return
            self.drag_pos = e.globalPos() - self.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):
        if self.drag_pos and e.buttons() & Qt.LeftButton:
            self.move(e.globalPos() - self.drag_pos); e.accept()

    def mouseReleaseEvent(self, e): self.drag_pos = None

    def _center(self):
        s = QApplication.primaryScreen().availableGeometry()
        self.move(s.center().x() - self.width() // 2,
                  s.center().y() - self.height() // 2)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.grip.move(self.width() - 24, self.height() - 24)
        self._resize_debounce.start(120)

    def closeEvent(self, e):
        for t in (self._log_reader, self._models_reader):
            if t and t.isRunning():
                t.wait(1200)
        self.settings_window.close(); self.settings_window.deleteLater()
        self.chat_window.close(); self.chat_window.deleteLater()
        try: self.ollama_mgr.shutdown()
        except Exception: pass
        super().closeEvent(e)


# ================================================================
#  ENTRY POINT
# ================================================================
def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    # ---- boot Ollama silently ----
    mgr = OllamaManager()
    ok, msg = mgr.setup()
    if not ok:
        QMessageBox.critical(None, "AI Command Center", msg)
        return 1

    w = FloatingDashboard(mgr)
    w.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
