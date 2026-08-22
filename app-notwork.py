from __future__ import annotations

import base64
import ctypes
import html
import json
import logging
import os
import re
import sys
import urllib.error
import urllib.request
from ctypes import wintypes
from logging.handlers import RotatingFileHandler

from PySide6.QtCore import (
    QAbstractNativeEventFilter,
    QByteArray,
    QBuffer,
    QEvent,
    QIODevice,
    QPoint,
    QRect,
    QSettings,
    QSize,
    QThread,
    QTimer,
    QUrl,
    Signal,
    Qt,
)
from PySide6.QtGui import (
    QAction,
    QColor,
    QCloseEvent,
    QCursor,
    QKeyEvent,
    QKeySequence,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QKeySequenceEdit,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizeGrip,
    QSlider,
    QSizePolicy,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

APP_NAME = "Overlay AI"
ORG_NAME = "LocalTools"
WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
HWND_TOPMOST = -1
DEFAULT_WINDOW_SIZE = QSize(520, 560)
NORMAL_MINIMUM_SIZE = QSize(360, 300)
COMPACT_MINIMUM_SIZE = QSize(120, 90)
HOTKEYS = {
    1: ("Bật/tắt click xuyên", "Ctrl+M"),
    2: ("Ẩn/hiện cửa sổ", "Ctrl+\\"),
    3: ("Giảm độ mờ", "Ctrl+["),
    4: ("Tăng độ mờ", "Ctrl+]"),
    5: ("Bật/tắt chọn vùng", "Ctrl+E"),
    6: ("Gửi nội dung", "Ctrl+Enter"),
    7: ("Mở Cài đặt", "Ctrl+H"),
}
LOG_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.getcwd()), "OverlayAI")
LOG_PATH = os.path.join(LOG_DIR, "overlay-ai.log")
SYSTEM_INSTRUCTION = (
    "Khi trả lời câu hỏi trắc nghiệm, hãy bôi đậm đáp án đúng bằng Markdown, "
    "ví dụ **A. Nội dung đáp án**. Không tự khẳng định đáp án nếu không đủ thông tin."
)
THEME_PALETTES = {
    "black": ("#f1f1f1", "rgba(15,15,15,246)", "rgba(25,25,25,232)", "#343434", "#a6a6a6", "#454545"),
    "gray": ("#f5f5f5", "rgba(52,52,52,246)", "rgba(67,67,67,232)", "#686868", "#c4c4c4", "#777777"),
    "white": ("#171717", "rgba(247,247,247,248)", "rgba(255,255,255,240)", "#c7c7c7", "#555555", "#dedede"),
}

VK_SPECIAL = {
    int(Qt.Key.Key_Return): 0x0D,
    int(Qt.Key.Key_Enter): 0x0D,
    int(Qt.Key.Key_Escape): 0x1B,
    int(Qt.Key.Key_Space): 0x20,
    int(Qt.Key.Key_Tab): 0x09,
    int(Qt.Key.Key_Backspace): 0x08,
    int(Qt.Key.Key_Delete): 0x2E,
    int(Qt.Key.Key_Insert): 0x2D,
    int(Qt.Key.Key_Home): 0x24,
    int(Qt.Key.Key_End): 0x23,
    int(Qt.Key.Key_PageUp): 0x21,
    int(Qt.Key.Key_PageDown): 0x22,
    int(Qt.Key.Key_Left): 0x25,
    int(Qt.Key.Key_Up): 0x26,
    int(Qt.Key.Key_Right): 0x27,
    int(Qt.Key.Key_Down): 0x28,
    int(Qt.Key.Key_BracketLeft): 0xDB,
    int(Qt.Key.Key_Backslash): 0xDC,
    int(Qt.Key.Key_BracketRight): 0xDD,
}


def hotkey_text(settings: QSettings, hotkey_id: int) -> str:
    return settings.value(f"hotkeys/{hotkey_id}", HOTKEYS[hotkey_id][1], str)


def hotkey_to_win(text: str) -> tuple[int, int]:
    sequence = QKeySequence.fromString(text, QKeySequence.SequenceFormat.PortableText)
    if sequence.isEmpty() or sequence.count() != 1:
        raise ValueError(f"Phím tắt không hợp lệ: {text}")
    combination = sequence[0]
    key = int(combination.key())
    modifiers = combination.keyboardModifiers()
    win_modifiers = MOD_NOREPEAT
    if modifiers & Qt.KeyboardModifier.ControlModifier:
        win_modifiers |= MOD_CONTROL
    if modifiers & Qt.KeyboardModifier.AltModifier:
        win_modifiers |= MOD_ALT
    if modifiers & Qt.KeyboardModifier.ShiftModifier:
        win_modifiers |= MOD_SHIFT
    if modifiers & Qt.KeyboardModifier.MetaModifier:
        win_modifiers |= MOD_WIN
    if win_modifiers == MOD_NOREPEAT:
        raise ValueError(f"Phím tắt cần ít nhất một modifier: {text}")
    if ord("A") <= key <= ord("Z") or ord("0") <= key <= ord("9"):
        return win_modifiers, key
    if int(Qt.Key.Key_F1) <= key <= int(Qt.Key.Key_F24):
        return win_modifiers, 0x70 + key - int(Qt.Key.Key_F1)
    if key in VK_SPECIAL:
        return win_modifiers, VK_SPECIAL[key]
    raise ValueError(f"Phím chính chưa được hỗ trợ: {text}")


class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


def enable_dpi_awareness() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()


def protect_secret(value: str) -> str:
    if not value:
        return ""
    raw = value.encode("utf-8")
    source_buffer = ctypes.create_string_buffer(raw)
    source = DATA_BLOB(len(raw), ctypes.cast(source_buffer, ctypes.POINTER(ctypes.c_ubyte)))
    output = DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    if not crypt32.CryptProtectData(
        ctypes.byref(source), "Overlay AI API key", None, None, None, 0, ctypes.byref(output)
    ):
        raise ctypes.WinError()
    try:
        encrypted = ctypes.string_at(output.pbData, output.cbData)
        return base64.b64encode(encrypted).decode("ascii")
    finally:
        ctypes.windll.kernel32.LocalFree(output.pbData)


def unprotect_secret(value: str) -> str:
    if not value:
        return ""
    raw = base64.b64decode(value)
    source_buffer = ctypes.create_string_buffer(raw)
    source = DATA_BLOB(len(raw), ctypes.cast(source_buffer, ctypes.POINTER(ctypes.c_ubyte)))
    output = DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    if not crypt32.CryptUnprotectData(
        ctypes.byref(source), None, None, None, None, 0, ctypes.byref(output)
    ):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(output.pbData, output.cbData).decode("utf-8")
    finally:
        ctypes.windll.kernel32.LocalFree(output.pbData)


def configure_logging() -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger("overlay_ai")
    if not logger.handlers:
        handler = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def safe_response_log(raw: str) -> str:
    value = re.sub(r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+", "<redacted-image-data-url>", raw)
    value = re.sub(
        r'(?i)("(?:api[_-]?key|access[_-]?token|refresh[_-]?token|authorization)"\s*:\s*")[^"]*(")',
        r"\1<redacted>\2",
        value,
    )
    value = re.sub(r"[A-Za-z0-9+/]{512,}={0,2}", "<redacted-long-base64>", value)
    return value[:16_384]


LOGGER = configure_logging()


def chat_endpoint(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    if not value:
        raise ValueError("Base URL không được để trống.")
    if value.endswith("/chat/completions"):
        return value
    return f"{value}/chat/completions"


def compose_image_prompt(image_prompt: str, question: str) -> str:
    combined = "\n\n".join(part.strip() for part in (image_prompt, question) if part.strip())
    return combined or "Hãy phân tích ảnh này."


def content_text(content) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                value = part.get("text") or part.get("content")
                if isinstance(value, str):
                    parts.append(value)
                elif isinstance(value, dict) and isinstance(value.get("value"), str):
                    parts.append(value["value"])
        return "\n".join(part.strip() for part in parts if part.strip())
    if isinstance(content, dict):
        value = content.get("text") or content.get("value") or content.get("content")
        return content_text(value)
    return ""


def response_schema(payload) -> str:
    if not isinstance(payload, dict):
        return type(payload).__name__
    parts = ["root=" + ",".join(sorted(payload.keys()))]
    choices = payload.get("choices")
    if isinstance(choices, list):
        parts.append(f"choices={len(choices)}")
        if choices and isinstance(choices[0], dict):
            parts.append("choice0=" + ",".join(sorted(choices[0].keys())))
            message = choices[0].get("message")
            if isinstance(message, dict):
                parts.append("message=" + ",".join(sorted(message.keys())))
    output = payload.get("output")
    if isinstance(output, list):
        parts.append(f"output={len(output)}")
    return "; ".join(parts)


def assistant_text(payload: dict) -> str:
    if not isinstance(payload, dict):
        return ""
    choices = payload.get("choices")
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        choice = choices[0]
        message = choice.get("message")
        if isinstance(message, dict):
            for key in ("content", "reasoning_content", "text"):
                text = content_text(message.get(key))
                if text:
                    return text
        for key in ("text", "content"):
            text = content_text(choice.get(key))
            if text:
                return text
        delta = choice.get("delta")
        if isinstance(delta, dict):
            text = content_text(delta.get("content") or delta.get("text"))
            if text:
                return text
    text = content_text(payload.get("output_text"))
    if text:
        return text
    output = payload.get("output")
    if isinstance(output, list):
        text = "\n".join(
            content_text(item.get("content") or item.get("text"))
            for item in output
            if isinstance(item, dict)
        ).strip()
        if text:
            return text
    for key in ("response", "text", "content"):
        text = content_text(payload.get(key))
        if text:
            return text
    return ""


class HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def nativeEventFilter(self, event_type, message):  # noqa: N802 - Qt API
        try:
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY:
                self.callback(int(msg.wParam))
                return True, 0
        except (TypeError, ValueError):
            pass
        return False, 0


class ChatWorker(QThread):
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, endpoint: str, api_key: str, model: str, messages: list[dict]):
        super().__init__()
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.messages = messages

    def run(self) -> None:
        request_id = f"{id(self):x}"
        body = json.dumps(
            {"model": self.model, "messages": self.messages, "stream": False},
            ensure_ascii=False,
        ).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "OverlayAI/1.0 (Windows; OpenAI-compatible API client)",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(self.endpoint, data=body, headers=headers, method="POST")
        LOGGER.info(
            "chat request id=%s endpoint=%s model=%s messages=%d request_bytes=%d",
            request_id,
            self.endpoint,
            self.model,
            len(self.messages),
            len(body),
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = response.read()
                charset = response.headers.get_content_charset() or "utf-8"
                decoded = raw.decode(charset, errors="replace")
                LOGGER.info(
                    "chat response id=%s status=%s content_type=%s response_bytes=%d body=%s",
                    request_id,
                    response.status,
                    response.headers.get("Content-Type", ""),
                    len(raw),
                    safe_response_log(decoded),
                )
                payload = json.loads(decoded)
            text = assistant_text(payload).strip()
            if not text:
                schema = response_schema(payload)
                LOGGER.error(
                    "chat empty content id=%s model=%s schema=%s log=%s",
                    request_id,
                    self.model,
                    schema,
                    LOG_PATH,
                )
                self.failed.emit(
                    f"Provider trả về HTTP 200 nhưng không có nội dung. Model: {self.model}. "
                    f"Request ID: {request_id}. Schema nhận được: {schema}. "
                    f"Chi tiết đã ghi tại: {LOG_PATH}"
                )
                return
            self.succeeded.emit(text)
        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")[:1200]
            LOGGER.error(
                "chat HTTP error id=%s status=%d body=%s",
                request_id,
                error.code,
                safe_response_log(details),
            )
            if error.code == 403 and ("error 1010" in details.lower() or "browser_signature_banned" in details):
                self.failed.emit(
                    "Cloudflare Error 1010: tunnel đang chặn chữ ký HTTP client trước khi request tới API. "
                    "Chủ tunnel cần tạo allow/skip rule cho API route hoặc User-Agent OverlayAI/1.0; "
                    "đổi API key hay thử lại sẽ không sửa được lỗi này."
                )
            else:
                self.failed.emit(f"HTTP {error.code}: {details}")
        except Exception as error:
            LOGGER.exception("chat exception id=%s type=%s", request_id, type(error).__name__)
            self.failed.emit(str(error))


class SubmitLineEdit(QLineEdit):
    submitted = Signal()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.submitted.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class NoWheelComboBox(QComboBox):
    def wheelEvent(self, event) -> None:
        event.ignore()


class NoWheelSlider(QSlider):
    def wheelEvent(self, event) -> None:
        event.ignore()


class SettingsDialog(QDialog):
    def __init__(self, settings: QSettings, parent: QWidget | None = None):
        super().__init__(parent)
        self.settings = settings
        self.overlay = parent
        self.setObjectName("settingsPanel")
        self.setWindowTitle("Cài đặt Overlay AI")
        self.setMinimumWidth(0)
        if parent is not None:
            self.setWindowOpacity(parent.windowOpacity())

        self.base_url = QLineEdit(settings.value("api/base_url", "https://api.openai.com/v1", str))
        self.model = NoWheelComboBox()
        self.model.setEditable(True)
        current_model = settings.value("api/model", "gpt-4o-mini", str).strip()
        model_history = settings.value("api/models", [])
        if isinstance(model_history, str):
            model_history = [model_history]
        models = list(dict.fromkeys(str(item).strip() for item in model_history))
        self.model.addItems([item for item in models if item])
        self.model.setCurrentText(current_model)
        self.model_row = QWidget()
        self.model_layout = QHBoxLayout(self.model_row)
        self.model_layout.setContentsMargins(0, 0, 0, 0)
        self.model_layout.setSpacing(6)
        self.model_action = QPushButton()
        self.model_action.clicked.connect(self.toggle_model_saved)
        self.model_layout.addWidget(self.model, 1)
        self.model_layout.addWidget(self.model_action)
        self.model.currentIndexChanged.connect(self.select_saved_model)
        self.model.editTextChanged.connect(self.update_model_action)
        self.update_model_action()
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.image_prompt = QPlainTextEdit(
            settings.value(
                "capture/image_prompt",
                "Hãy phân tích ảnh chụp màn hình này và hỗ trợ ngắn gọn.",
                str,
            )
        )
        self.image_prompt.setMaximumHeight(72)
        self.image_prompt.setPlaceholderText("Prompt hệ thống thêm vào khi gửi kèm ảnh")
        try:
            self.api_key.setText(unprotect_secret(settings.value("api/key", "", str)))
        except Exception:
            self.api_key.setPlaceholderText("Không đọc được key đã lưu; nhập lại")

        self.always_on_top = QCheckBox("Luôn ở trên cùng")
        self.always_on_top.setChecked(settings.value("window/always_on_top", True, bool))
        self.keep_on_top = QCheckBox("Định kỳ giữ cửa sổ trên cùng")
        self.keep_on_top.setChecked(settings.value("window/keep_on_top", True, bool))
        self.hide_during_capture = QCheckBox("Ẩn cửa sổ Overlay AI khi chụp")
        self.hide_during_capture.setChecked(settings.value("capture/hide_overlay", True, bool))
        self.show_selection_frame = QCheckBox("Hiện khung vùng chọn và kích thước")
        self.show_selection_frame.setChecked(settings.value("capture/show_selection_frame", True, bool))
        self.show_title = QCheckBox("Hiện thanh tiêu đề")
        self.show_title.setChecked(settings.value("window/show_title", True, bool))
        self.auto_scroll = QCheckBox("Tự cuộn xuống khi gửi và nhận tin nhắn")
        self.auto_scroll.setChecked(settings.value("chat/auto_scroll", True, bool))
        self.allow_tiny_resize = QCheckBox("Cho phép resize rất nhỏ (tối thiểu 120 × 90)")
        self.allow_tiny_resize.setChecked(settings.value("window/allow_tiny_resize", False, bool))
        self.use_dxcam = QCheckBox("Sử dụng DXGI để chụp màn hình")
        self.use_dxcam.setChecked(settings.value("capture/use_dxcam", False, bool))
        self.use_dxcam.setToolTip("Dùng dxcam cho capture DXGI nhanh hơn; không bảo đảm chụp nội dung được hệ điều hành bảo vệ.")
        self.opacity = NoWheelSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(5, 100)
        self.opacity.setValue(round(float(settings.value("window/opacity", 0.94)) * 100))
        self.opacity.setToolTip("Độ hiển thị 5–100%; 5% là trong suốt nhất")
        self.opacity_value = QLabel(f"{self.opacity.value()}%")
        self.opacity.valueChanged.connect(lambda value: self.opacity_value.setText(f"{value}%"))
        opacity_row = QWidget()
        opacity_layout = QHBoxLayout(opacity_row)
        opacity_layout.setContentsMargins(0, 0, 0, 0)
        opacity_layout.addWidget(self.opacity, 1)
        opacity_layout.addWidget(self.opacity_value)
        self.theme = NoWheelComboBox()
        self.theme.addItem("Đen", "black")
        self.theme.addItem("Xám", "gray")
        self.theme.addItem("Trắng", "white")
        theme_index = self.theme.findData(settings.value("window/theme", "black", str))
        self.theme.setCurrentIndex(max(0, theme_index))
        self.theme.currentIndexChanged.connect(self.apply_appearance)

        self.form = QFormLayout()
        self.form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.form.addRow("Base URL", self.base_url)
        self.form.addRow("Model", self.model_row)
        self.form.addRow("API key", self.api_key)
        self.form.addRow("Prompt khi gửi ảnh", self.image_prompt)
        self.form.addRow("", self.always_on_top)
        self.form.addRow("", self.keep_on_top)
        self.form.addRow("", self.hide_during_capture)
        self.form.addRow("", self.show_selection_frame)
        self.form.addRow("", self.show_title)
        self.form.addRow("", self.auto_scroll)
        self.form.addRow("", self.allow_tiny_resize)
        self.form.addRow("", self.use_dxcam)
        self.form.addRow("Độ hiển thị", opacity_row)
        self.form.addRow("Giao diện", self.theme)

        shortcut_title = QLabel("Phím tắt toàn cục")
        shortcut_title.setStyleSheet("font-size: 15px; font-weight: 700; margin-top: 8px;")
        self.shortcut_form = QFormLayout()
        self.shortcut_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.hotkey_edits: dict[int, QKeySequenceEdit] = {}
        for hotkey_id, (label, _) in HOTKEYS.items():
            edit = QKeySequenceEdit(QKeySequence.fromString(hotkey_text(settings, hotkey_id)))
            edit.setClearButtonEnabled(True)
            edit.setMaximumSequenceLength(1)
            self.hotkey_edits[hotkey_id] = edit
            self.shortcut_form.addRow(label, edit)

        failures = getattr(parent, "hotkey_failures", [])
        shortcut_status = QLabel(
            "Đang hoạt động: tất cả phím tắt."
            if not failures
            else "Không đăng ký được: " + ", ".join(failures)
        )
        shortcut_status.setWordWrap(True)
        shortcut_status.setStyleSheet("color: #79d9a6;" if not failures else "color: #ff8d9e;")

        note = QLabel(
            "Tự động lưu. Base URL ví dụ: https://api.openai.com/v1. API key được mã hóa "
            "bằng Windows DPAPI cho tài khoản Windows hiện tại."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #93a4bd;")
        close_button = QPushButton("Đóng")
        close_button.clicked.connect(self.close_with_save)

        layout = QVBoxLayout(self)
        layout.addLayout(self.form)
        layout.addWidget(note)
        layout.addWidget(shortcut_title)
        layout.addLayout(self.shortcut_form)
        layout.addWidget(shortcut_status)
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.setInterval(350)
        self.autosave_timer.timeout.connect(self.save_settings)
        for edit in (self.base_url, self.api_key):
            edit.textChanged.connect(self.schedule_auto_save)
        self.model.editTextChanged.connect(self.schedule_auto_save)
        self.image_prompt.textChanged.connect(self.schedule_auto_save)
        for checkbox in (
            self.always_on_top,
            self.keep_on_top,
            self.hide_during_capture,
            self.show_selection_frame,
            self.show_title,
            self.auto_scroll,
        ):
            checkbox.toggled.connect(self.schedule_auto_save)
        self.allow_tiny_resize.toggled.connect(self.change_resize_mode)
        self.opacity.valueChanged.connect(self.schedule_auto_save)
        self.use_dxcam.toggled.connect(self.schedule_auto_save)
        self.theme.currentIndexChanged.connect(self.schedule_auto_save)
        for edit in self.hotkey_edits.values():
            edit.editingFinished.connect(self.schedule_auto_save)

        self.apply_responsive_layout()
        self.apply_appearance()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.apply_responsive_layout()

    def apply_responsive_layout(self) -> None:
        parent_width = self.parentWidget().width() - 40 if self.parentWidget() else self.width()
        available_width = min(self.width(), parent_width)
        narrow = available_width < 470
        policy = (
            QFormLayout.RowWrapPolicy.WrapAllRows
            if narrow
            else QFormLayout.RowWrapPolicy.DontWrapRows
        )
        self.form.setRowWrapPolicy(policy)
        self.shortcut_form.setRowWrapPolicy(policy)
        self.model_layout.setDirection(
            QHBoxLayout.Direction.TopToBottom
            if available_width < 390
            else QHBoxLayout.Direction.LeftToRight
        )

    def saved_models(self) -> list[str]:
        return [
            self.model.itemText(index).strip()
            for index in range(self.model.count())
            if self.model.itemText(index).strip()
        ]

    def update_model_action(self) -> None:
        model = self.model.currentText().strip()
        saved = bool(model) and self.model.findText(model) >= 0
        self.model_action.setText("Xóa" if saved else "Lưu model")
        self.model_action.setEnabled(bool(model))

    def select_saved_model(self, index: int) -> None:
        if index < 0:
            return
        model = self.model.itemText(index).strip()
        if model:
            self.settings.setValue("api/model", model)
            self.settings.sync()
        self.update_model_action()

    def toggle_model_saved(self) -> None:
        model = self.model.currentText().strip()
        if not model:
            return
        index = self.model.findText(model)
        if index >= 0:
            self.model.removeItem(index)
            next_model = self.model.itemText(0).strip() if self.model.count() else ""
            self.model.setCurrentText(next_model)
        else:
            self.model.insertItem(0, model)
            self.model.setCurrentIndex(0)
        self.settings.setValue("api/models", self.saved_models()[:20])
        self.settings.setValue("api/model", self.model.currentText().strip())
        self.settings.sync()
        self.update_model_action()

    def apply_appearance(self) -> None:
        theme = self.theme.currentData()
        text, panel, field, border, muted, _ = THEME_PALETTES.get(
            theme, THEME_PALETTES["black"]
        )
        solid_panel = {"black": "#0f0f0f", "gray": "#343434", "white": "#f7f7f7"}.get(
            theme, "#0f0f0f"
        )
        self.setStyleSheet(
            f"""
            QWidget#settingsPanel {{ background: {solid_panel}; color: {text}; }}
            QWidget {{ color: {text}; font-family: "Segoe UI"; font-size: 14px; }}
            QLineEdit, QPlainTextEdit, QComboBox, QKeySequenceEdit {{
                background: {field}; border: 1px solid {border}; border-radius: 7px; padding: 6px;
            }}
            QComboBox QAbstractItemView {{ background: {field}; color: {text}; selection-background-color: {border}; }}
            QCheckBox {{ spacing: 7px; }}
            QPushButton {{ background: {field}; border: 1px solid {border}; border-radius: 7px; padding: 7px 12px; }}
            QPushButton:hover {{ background: {border}; }}
            QLabel {{ color: {text}; }}
            """
        )

    def schedule_auto_save(self, *_args) -> None:
        self.autosave_timer.start()

    def change_resize_mode(self, allow_tiny: bool) -> None:
        self.settings.setValue("window/allow_tiny_resize", allow_tiny)
        if self.overlay is not None:
            self.overlay.apply_size_settings(reset_to_default=not allow_tiny)
        self.schedule_auto_save()

    def save_settings(self, show_errors: bool = False) -> bool:
        errors = []
        try:
            base_url = self.base_url.text().strip()
            chat_endpoint(base_url)
            self.settings.setValue("api/base_url", base_url)
        except Exception as error:
            errors.append(str(error))

        model = self.model.currentText().strip()
        if model:
            self.settings.setValue("api/model", model)
        else:
            errors.append("Model không được để trống.")

        try:
            self.settings.setValue("api/key", protect_secret(self.api_key.text().strip()))
        except Exception as error:
            errors.append(str(error))
        self.settings.setValue("api/models", list(dict.fromkeys(self.saved_models()))[:20])
        self.settings.setValue("capture/image_prompt", self.image_prompt.toPlainText().strip())
        self.settings.setValue("window/always_on_top", self.always_on_top.isChecked())
        self.settings.setValue("window/keep_on_top", self.keep_on_top.isChecked())
        self.settings.setValue("capture/hide_overlay", self.hide_during_capture.isChecked())
        self.settings.setValue("capture/show_selection_frame", self.show_selection_frame.isChecked())
        self.settings.setValue("window/show_title", self.show_title.isChecked())
        self.settings.setValue("chat/auto_scroll", self.auto_scroll.isChecked())
        self.settings.setValue("window/allow_tiny_resize", self.allow_tiny_resize.isChecked())
        self.settings.setValue("capture/use_dxcam", self.use_dxcam.isChecked())
        self.settings.setValue("window/opacity", self.opacity.value() / 100)
        self.settings.setValue("window/theme", self.theme.currentData())

        try:
            hotkeys = []
            for edit in self.hotkey_edits.values():
                text = edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText)
                hotkey_to_win(text)
                hotkeys.append(text)
            if len(set(hotkeys)) != len(hotkeys):
                raise ValueError("Các phím tắt không được trùng nhau.")
            for hotkey_id, text in zip(self.hotkey_edits, hotkeys):
                self.settings.setValue(f"hotkeys/{hotkey_id}", text)
        except Exception as error:
            errors.append(str(error))

        self.settings.sync()
        if self.overlay is not None:
            self.overlay.apply_size_settings()
            self.overlay.apply_top_settings()
            self.overlay.apply_appearance_settings()
            self.overlay.setWindowOpacity(self.opacity.value() / 100)
        if show_errors and errors:
            QMessageBox.warning(self, "Một số cài đặt chưa hợp lệ", "\n".join(errors))
        return not errors

    def close_with_save(self) -> None:
        self.autosave_timer.stop()
        self.save_settings(True)
        super().accept()


class DragBar(QFrame):
    def __init__(self, window: QWidget):
        super().__init__()
        self.window = window
        self.drag_origin: QPoint | None = None
        self.setObjectName("dragBar")
        self.setFixedHeight(48)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_origin = event.globalPosition().toPoint() - self.window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window.move(event.globalPosition().toPoint() - self.drag_origin)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.drag_origin = None
        event.accept()


class SelectionOverlay(QWidget):
    selected = Signal(QRect)
    cancelled = Signal()

    def __init__(self, show_selection_frame: bool):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.show_selection_frame = show_selection_frame
        if show_selection_frame:
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.start: QPoint | None = None
        self.current: QPoint | None = None
        virtual = QRect()
        for screen in QApplication.screens():
            virtual = virtual.united(screen.geometry())
        self.setGeometry(virtual)

    def begin(self) -> None:
        self.start = None
        self.current = None
        self.show()
        self.raise_()
        self.activateWindow()
        self.grabKeyboard()

    def cancel(self) -> None:
        self.releaseKeyboard()
        self.hide()
        self.cancelled.emit()

    def selection_rect(self) -> QRect:
        if self.start is None or self.current is None:
            return QRect()
        return QRect(self.start, self.current).normalized()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        # ponytail: alpha 1 keeps Win32 hit-testing without freezing a screenshot; use native region windows for zero-alpha overlays.
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))
        if not self.show_selection_frame:
            return
        selection = self.selection_rect()
        if not selection.isValid() or selection.isEmpty():
            return
        painter.setPen(QPen(QColor("#51c8ff"), 2))
        painter.drawRect(selection.adjusted(0, 0, -1, -1))
        label = f"{selection.width()} × {selection.height()}"
        label_rect = QRect(selection.left() + 2, selection.top() + 2, 92, 24)
        painter.fillRect(label_rect, QColor(8, 20, 38, 210))
        painter.setPen(QColor("white"))
        painter.drawText(label_rect.adjusted(7, 0, 0, 0), Qt.AlignmentFlag.AlignVCenter, label)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.start = event.position().toPoint()
            self.current = self.start
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.start is not None:
            self.current = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton or self.start is None:
            return
        self.current = event.position().toPoint()
        local_rect = self.selection_rect()
        self.releaseKeyboard()
        self.hide()
        if local_rect.width() < 4 or local_rect.height() < 4:
            self.cancelled.emit()
            return
        global_rect = QRect(self.mapToGlobal(local_rect.topLeft()), local_rect.size())
        self.selected.emit(global_rect)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.cancel()
            return
        super().keyPressEvent(event)


class OverlayWindow(QWidget):
    def __init__(self, settings: QSettings):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if settings.value("window/always_on_top", True, bool):
            flags |= Qt.WindowType.WindowStaysOnTopHint
        super().__init__(None, flags)
        self.settings = settings
        self.worker: ChatWorker | None = None
        self.messages: list[dict] = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
        self.click_through = False
        self.exiting = False
        self.was_visible_before_capture = True
        self.selector: SelectionOverlay | None = None
        self.pending_image: bytes | None = None
        self.hotkey_failures: list[str] = []
        self.dxcam_cameras: dict[int, any] = {}
        self.settings_panel: SettingsDialog | None = None
        self.drag_origin: QPoint | None = None

        self.setObjectName("overlayWindow")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(settings.value("window/size", DEFAULT_WINDOW_SIZE, QSize))
        self.apply_size_settings(initial=True)
        self.setWindowOpacity(float(settings.value("window/opacity", 0.94)))
        self._build_ui()
        self._build_tray()

        self.top_timer = QTimer(self)
        self.top_timer.setInterval(1200)
        self.top_timer.timeout.connect(self.ensure_topmost)
        self.apply_top_settings()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.panel = QFrame()
        self.panel.setObjectName("panel")
        root.addWidget(self.panel)
        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(14, 10, 14, 14)
        layout.setSpacing(10)

        self.drag_bar = DragBar(self)
        header = QHBoxLayout(self.drag_bar)
        header.setContentsMargins(10, 0, 4, 0)
        title = QLabel("Overlay AI")
        title.setObjectName("title")
        shortcuts = QLabel("Ctrl+E chọn vùng  •  Ctrl+M click xuyên")
        shortcuts.setObjectName("hint")
        settings_button = QPushButton("⚙")
        settings_button.setObjectName("iconButton")
        settings_button.setFixedSize(36, 32)
        settings_button.clicked.connect(self.open_settings)
        hide_button = QPushButton("—")
        hide_button.setObjectName("iconButton")
        hide_button.setFixedSize(36, 32)
        hide_button.clicked.connect(self.hide)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(shortcuts)
        header.addWidget(settings_button)
        header.addWidget(hide_button)
        layout.addWidget(self.drag_bar)

        self.compact_settings_button = QPushButton("⚙", self)
        self.compact_settings_button.setObjectName("compactSettingsButton")
        self.compact_settings_button.setToolTip("Cài đặt")
        self.compact_settings_button.setFixedSize(26, 26)
        self.compact_settings_button.clicked.connect(self.open_settings)
        self.compact_settings_button.hide()

        self.chat = QScrollArea()
        self.chat.setObjectName("chat")
        self.chat.setWidgetResizable(True)
        self.chat.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_content = QWidget()
        self.chat_content.setObjectName("chatContent")
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(4, 4, 4, 4)
        self.chat_layout.setSpacing(7)
        self.chat_layout.addStretch(1)
        self.chat.setWidget(self.chat_content)
        self.chat.verticalScrollBar().rangeChanged.connect(self.on_chat_range_changed)
        layout.addWidget(self.chat, 1)

        self.attachment = QFrame()
        self.attachment.setObjectName("attachment")
        attachment_layout = QHBoxLayout(self.attachment)
        attachment_layout.setContentsMargins(8, 6, 8, 6)
        self.attachment_preview = QLabel()
        self.attachment_preview.setFixedSize(48, 32)
        self.attachment_preview.setScaledContents(False)
        self.attachment_text = QLabel("Ảnh chụp đã đính kèm • Ctrl+Enter để gửi")
        remove_attachment = QPushButton("×")
        remove_attachment.setObjectName("iconButton")
        remove_attachment.setFixedSize(30, 30)
        remove_attachment.clicked.connect(self.clear_pending_image)
        attachment_layout.addWidget(self.attachment_preview)
        attachment_layout.addWidget(self.attachment_text, 1)
        attachment_layout.addWidget(remove_attachment)
        self.attachment.hide()
        layout.addWidget(self.attachment)

        self.input_frame = QFrame()
        self.input_frame.setObjectName("inputFrame")
        input_row = QHBoxLayout(self.input_frame)
        input_row.setContentsMargins(14, 4, 5, 4)
        input_row.setSpacing(6)
        self.input = SubmitLineEdit()
        self.input.setObjectName("input")
        self.input.setPlaceholderText("Bạn cần giúp gì?")
        self.input.setFixedHeight(34)
        self.input.submitted.connect(self.submit)
        send_button = QPushButton("➤")
        send_button.setObjectName("sendButton")
        send_button.setToolTip("Gửi • Ctrl+Enter")
        send_button.setFixedSize(34, 34)
        send_button.clicked.connect(lambda: self.submit())
        input_row.addWidget(self.input, 1)
        input_row.addWidget(send_button)
        layout.addWidget(self.input_frame)

        self.settings_scroll = QScrollArea()
        self.settings_scroll.setObjectName("settingsScroll")
        self.settings_scroll.setWidgetResizable(True)
        self.settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.settings_scroll.hide()
        layout.addWidget(self.settings_scroll, 1)

        self.footer_frame = QFrame()
        footer = QHBoxLayout(self.footer_frame)
        footer.setContentsMargins(0, 0, 0, 0)
        self.status = QLabel("Sẵn sàng")
        self.status.setObjectName("status")
        self.size_grip = QSizeGrip(self)
        self.size_grip.setFixedSize(18, 18)
        footer.addWidget(self.status, 1)
        footer.addWidget(self.size_grip, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.footer_frame)

        for draggable in (
            self.panel,
            self.chat.viewport(),
            self.chat_content,
            self.attachment,
            self.attachment_text,
            self.input_frame,
            self.footer_frame,
            self.status,
        ):
            draggable.installEventFilter(self)
        self.apply_appearance_settings()

    def _build_tray(self) -> None:
        icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.setWindowIcon(icon)
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip(APP_NAME)
        menu = QMenu()
        show_action = QAction("Ẩn/hiện cửa sổ", menu)
        show_action.triggered.connect(self.toggle_visible)
        capture_action = QAction("Chụp vùng màn hình", menu)
        capture_action.triggered.connect(self.start_capture)
        click_action = QAction("Bật/tắt click xuyên", menu)
        click_action.triggered.connect(self.toggle_click_through)
        settings_action = QAction("Cài đặt", menu)
        settings_action.triggered.connect(self.open_settings)
        exit_action = QAction("Thoát", menu)
        exit_action.triggered.connect(self.quit_app)
        menu.addAction(show_action)
        menu.addAction(capture_action)
        menu.addAction(click_action)
        menu.addSeparator()
        menu.addAction(settings_action)
        menu.addAction(exit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda reason: self.toggle_visible()
            if reason == QSystemTrayIcon.ActivationReason.Trigger
            else None
        )
        self.tray.show()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self.ensure_topmost)
        QTimer.singleShot(0, self.apply_click_through)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.exiting:
            event.accept()
        else:
            event.ignore()
            self.hide()
            self.tray.showMessage(APP_NAME, "Ứng dụng vẫn chạy dưới khay hệ thống.", msecs=1800)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.settings.setValue("window/size", self.size())
        if hasattr(self, "compact_settings_button"):
            self.compact_settings_button.move(self.width() - 34, 8)
            self.compact_settings_button.raise_()

    def apply_size_settings(self, initial: bool = False, reset_to_default: bool = False) -> None:
        allow_tiny = self.settings.value("window/allow_tiny_resize", False, bool)
        self.setMinimumSize(COMPACT_MINIMUM_SIZE if allow_tiny else NORMAL_MINIMUM_SIZE)
        too_small = self.width() < NORMAL_MINIMUM_SIZE.width() or self.height() < NORMAL_MINIMUM_SIZE.height()
        if not allow_tiny and (reset_to_default or too_small):
            self.resize(DEFAULT_WINDOW_SIZE)

    def ensure_topmost(self) -> None:
        if not self.isVisible() or not self.settings.value("window/always_on_top", True, bool):
            return
        ctypes.windll.user32.SetWindowPos(
            int(self.winId()), HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
        )

    def apply_top_settings(self) -> None:
        opacity = float(self.settings.value("window/opacity", self.windowOpacity()))
        if self.settings.value("window/keep_on_top", True, bool):
            self.top_timer.start()
        else:
            self.top_timer.stop()
        desired = self.settings.value("window/always_on_top", True, bool)
        if bool(self.windowFlags() & Qt.WindowType.WindowStaysOnTopHint) != desired:
            visible = self.isVisible()
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, desired)
            if visible:
                self.show()
        self.setWindowOpacity(opacity)
        self.ensure_topmost()

    def apply_click_through(self) -> None:
        hwnd = int(self.winId())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style |= WS_EX_LAYERED | WS_EX_TOOLWINDOW
        if self.click_through:
            style |= WS_EX_TRANSPARENT
        else:
            style &= ~WS_EX_TRANSPARENT
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        self.status.setText("Click xuyên: bật" if self.click_through else "Sẵn sàng")

    def toggle_click_through(self) -> None:
        self.click_through = not self.click_through
        self.apply_click_through()

    def toggle_visible(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def adjust_opacity(self, delta: float) -> None:
        value = min(1.0, max(0.05, self.windowOpacity() + delta))
        self.setWindowOpacity(value)
        self.settings.setValue("window/opacity", round(value, 2))
        self.status.setText(f"Độ mờ: {round(value * 100)}%")

    def eventFilter(self, watched, event) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            self.drag_origin = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return True
        if event.type() == QEvent.Type.MouseMove and self.drag_origin is not None:
            if event.buttons() & Qt.MouseButton.LeftButton:
                self.move(event.globalPosition().toPoint() - self.drag_origin)
                event.accept()
                return True
        if event.type() == QEvent.Type.MouseButtonRelease and self.drag_origin is not None:
            self.drag_origin = None
            event.accept()
            return True
        return super().eventFilter(watched, event)

    def apply_appearance_settings(self) -> None:
        theme = self.settings.value("window/theme", "black", str)
        text, panel, field, border, muted, user_bubble = THEME_PALETTES.get(
            theme, THEME_PALETTES["black"]
        )
        show_title = self.settings.value("window/show_title", True, bool)
        self.drag_bar.setVisible(show_title)
        self.compact_settings_button.setVisible(not show_title)
        self.compact_settings_button.move(self.width() - 34, 8)
        self.compact_settings_button.raise_()
        self.setStyleSheet(
            f"""
            QWidget {{ color: {text}; font-family: "Segoe UI"; font-size: 14px; }}
            #panel {{ background: {panel}; border: 1px solid {border}; border-radius: 14px; }}
            #dragBar {{ background: {field}; border-radius: 10px; }}
            #title {{ font-size: 16px; font-weight: 700; }}
            #hint, #status {{ color: {muted}; font-size: 12px; }}
            #chat, #settingsScroll {{ background: transparent; border: none; }}
            #chatContent {{ background: transparent; }}
            #inputFrame {{ background: {field}; border: 1px solid {border}; border-radius: 22px; }}
            #input {{ background: transparent; border: none; padding: 0px; }}
            #attachment {{ background: {field}; border: 1px solid #2388b7; border-radius: 9px; }}
            #userBubble {{ background: {user_bubble}; border-radius: 12px; }}
            #assistantMessage {{ background: transparent; border: none; }}
            #errorBubble {{ background: #5a2730; border-radius: 10px; }}
            QPushButton {{ background: #12668d; color: white; border: 1px solid #2388b7; border-radius: 9px; padding: 7px; }}
            QPushButton:hover {{ background: #177ba5; }}
            #sendButton {{ background: {field}; color: {muted}; border: 1px solid {border}; border-radius: 17px; font-size: 17px; padding: 0px; }}
            #sendButton:hover {{ color: white; background: #12668d; }}
            #iconButton, #compactSettingsButton {{ background: transparent; color: {text}; border: none; font-size: 17px; padding: 0px; }}
            #compactSettingsButton {{ background: {field}; border: 1px solid {border}; border-radius: 13px; }}
            QScrollBar:vertical {{ background: transparent; width: 7px; }}
            QScrollBar::handle:vertical {{ background: {border}; border-radius: 3px; min-height: 26px; }}
            """
        )

    def open_settings(self) -> None:
        if not self.isVisible():
            self.show()
            self.raise_()
            self.activateWindow()
        if self.settings_scroll.isVisible():
            self.close_settings(False)
            return
        if self.settings_panel is not None:
            return
        self.settings_panel = SettingsDialog(self.settings, self)
        self.settings_panel.setWindowFlags(Qt.WindowType.Widget)
        self.settings_panel.setMinimumWidth(0)
        self.settings_panel.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.settings_panel.accepted.connect(lambda: self.close_settings(True))
        self.settings_panel.rejected.connect(lambda: self.close_settings(False))
        self.settings_scroll.setWidget(self.settings_panel)
        for widget in (self.chat, self.attachment, self.input_frame):
            widget.hide()
        self.status.setText("Cài đặt • kéo góc dưới phải để resize")
        self.settings_scroll.show()
        self.size_grip.raise_()
        self.compact_settings_button.raise_()

    def close_settings(self, accepted: bool) -> None:
        if self.settings_panel is not None:
            self.settings_panel.autosave_timer.stop()
            self.settings_panel.save_settings(False)
        self.settings_scroll.hide()
        self.chat.show()
        if self.pending_image is not None:
            self.attachment.show()
        self.input_frame.show()
        self.footer_frame.show()
        self.apply_top_settings()
        self.apply_appearance_settings()
        self.setWindowOpacity(float(self.settings.value("window/opacity", self.windowOpacity())))
        self.hotkey_failures = register_hotkeys(self.settings)
        self.status.setText(
            ("Đã tự động lưu" if accepted else "Sẵn sàng")
            if not self.hotkey_failures
            else "Phím tắt lỗi: " + ", ".join(self.hotkey_failures)
        )
        self.settings_panel = None

    def append_bubble(self, role: str, text: str, image: bytes | None = None) -> None:
        row = QWidget()
        row.installEventFilter(self)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(2, 0, 2, 0)
        bubble = QFrame()
        bubble.setObjectName(
            "userBubble" if role == "user" else "assistantMessage" if role == "assistant" else "errorBubble"
        )
        bubble.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        content_layout = QVBoxLayout(bubble)
        content_layout.setContentsMargins(10 if role != "assistant" else 2, 7, 10 if role != "assistant" else 2, 7)
        content_layout.setSpacing(5)
        message = QLabel(text if role != "error" else f"Lỗi\n{text}")
        if role == "assistant":
            message.setTextFormat(Qt.TextFormat.MarkdownText)
        message.setWordWrap(True)
        message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        message.setMaximumWidth(max(80, int(self.chat.viewport().width() * 0.72)))
        content_layout.addWidget(message)
        if image:
            pixmap = QPixmap()
            pixmap.loadFromData(image, "PNG")
            preview = QLabel()
            preview.setFixedSize(96, 64)
            preview.setPixmap(
                pixmap.scaled(
                    preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            content_layout.addWidget(preview, 0, Qt.AlignmentFlag.AlignLeft)
        if role == "user":
            row_layout.addStretch(1)
            row_layout.addWidget(bubble)
        else:
            row_layout.addWidget(bubble)
            row_layout.addStretch(1)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, row)
        if self.settings.value("chat/auto_scroll", True, bool):
            self.chat_layout.activate()
            QTimer.singleShot(0, self.scroll_chat_to_bottom)
            QTimer.singleShot(80, self.scroll_chat_to_bottom)

    def on_chat_range_changed(self, _minimum: int, maximum: int) -> None:
        if self.settings.value("chat/auto_scroll", True, bool):
            self.chat.verticalScrollBar().setValue(maximum)

    def scroll_chat_to_bottom(self) -> None:
        bar = self.chat.verticalScrollBar()
        bar.setValue(bar.maximum())

    def submit(self) -> None:
        if self.worker and self.worker.isRunning():
            self.status.setText("Đang chờ AI trả lời")
            return
        image = self.pending_image
        question = self.input.text().strip()
        if not question and image is None:
            return
        image_prompt = self.settings.value(
            "capture/image_prompt",
            "Hãy phân tích ảnh chụp màn hình này và hỗ trợ ngắn gọn.",
            str,
        ).strip()
        text = compose_image_prompt(image_prompt, question) if image is not None else question
        try:
            endpoint = chat_endpoint(self.settings.value("api/base_url", "https://api.openai.com/v1", str))
            api_key = unprotect_secret(self.settings.value("api/key", "", str))
            model = self.settings.value("api/model", "gpt-4o-mini", str).strip()
            if not model:
                raise ValueError("Chưa cấu hình model.")
        except Exception as error:
            self.append_bubble("error", str(error))
            self.open_settings()
            return

        self.input.clear()
        self.clear_pending_image()
        self.append_bubble("user", question or image_prompt or "Ảnh đính kèm", image)
        if image:
            encoded = base64.b64encode(image).decode("ascii")
            content = [
                {"type": "text", "text": text},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded}"}},
            ]
        else:
            content = text
        self.messages.append({"role": "user", "content": content})
        self.status.setText("AI đang trả lời…")
        self.worker = ChatWorker(endpoint, api_key, model, list(self.messages))
        self.worker.succeeded.connect(self.on_chat_success)
        self.worker.failed.connect(self.on_chat_error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def on_chat_success(self, text: str) -> None:
        self.messages.append({"role": "assistant", "content": text})
        self.append_bubble("assistant", text)
        self.status.setText("Sẵn sàng")
        self.worker = None

    def on_chat_error(self, text: str) -> None:
        self.append_bubble("error", text)
        self.status.setText("Gửi thất bại")
        self.worker = None

    def start_capture(self) -> None:
        if self.selector and self.selector.isVisible():
            self.selector.cancel()
            return
        self.was_visible_before_capture = self.isVisible()
        if self.settings.value("capture/hide_overlay", True, bool):
            self.hide()
        self.selector = SelectionOverlay(
            self.settings.value("capture/show_selection_frame", True, bool)
        )
        self.selector.selected.connect(self.capture_selected)
        self.selector.cancelled.connect(self.capture_cancelled)
        QTimer.singleShot(100, self.selector.begin)

    def capture_cancelled(self) -> None:
        self.selector = None
        if self.was_visible_before_capture:
            self.show()

    def capture_selected(self, rect: QRect) -> None:
        self.selector = None
        QTimer.singleShot(140, lambda: self.finish_capture(rect))

    def grab_virtual_rect(self, rect: QRect) -> QPixmap:
        use_dxcam = self.settings.value("capture/use_dxcam", False, bool)
        if use_dxcam:
            try:
                import dxcam
            except ImportError as error:
                self.settings.setValue("capture/use_dxcam", False)
                LOGGER.exception("DXcam import error: %s", error)
                QMessageBox.warning(
                    self,
                    "Thiếu thành phần DXGI",
                    f"Không thể nạp dxcam: {error}. Quay lại phương thức chụp mặc định.",
                )
            else:
                try:
                    screens = QApplication.screens()
                    containing = None
                    for screen in screens:
                        if rect.intersects(screen.geometry()):
                            if containing is not None:
                                containing = None
                                break
                            containing = screen
                    if containing is not None:
                        screen_idx = screens.index(containing)
                        camera = self.dxcam_cameras.get(screen_idx)
                        if camera is None:
                            camera = dxcam.create(
                                output_idx=screen_idx,
                                output_color="RGB",
                                processor_backend="numpy",
                            )
                            self.dxcam_cameras[screen_idx] = camera
                        local_rect = rect.translated(-containing.geometry().topLeft())
                        # ponytail: dxcam 0.3 can terminate the process on some
                        # drivers when grabbing a small region. Grab once, then crop.
                        frame = camera.grab()
                        if frame is not None:
                            left = max(0, local_rect.left())
                            top = max(0, local_rect.top())
                            right = min(frame.shape[1], local_rect.right() + 1)
                            bottom = min(frame.shape[0], local_rect.bottom() + 1)
                            frame = frame[top:bottom, left:right]
                            if frame.size:
                                frame = frame.copy()
                                h, w, c = frame.shape
                                qimage = QImage(
                                    frame.data,
                                    w,
                                    h,
                                    w * c,
                                    QImage.Format_RGB888,
                                ).copy()
                                return QPixmap.fromImage(qimage)
                except Exception as error:
                    LOGGER.exception("DXGI capture error: %s", error)
                    self.status.setText(f"DXGI lỗi: {error}. Đã dùng chụp mặc định")

        # --- Phương thức cũ (GDI) ---
        result = QPixmap(rect.size())
        result.fill(Qt.GlobalColor.transparent)
        painter = QPainter(result)
        for screen in QApplication.screens():
            intersection = rect.intersected(screen.geometry())
            if intersection.isEmpty():
                continue
            local = intersection.translated(-screen.geometry().topLeft())
            shot = screen.grabWindow(0, local.x(), local.y(), local.width(), local.height())
            destination = intersection.topLeft() - rect.topLeft()
            painter.drawPixmap(destination, shot)
        painter.end()
        return result

    def finish_capture(self, rect: QRect) -> None:
        pixmap = self.grab_virtual_rect(rect)
        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        pixmap.save(buffer, "PNG")
        self.pending_image = bytes(data)
        preview = pixmap.scaled(
            self.attachment_preview.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.attachment_preview.setPixmap(preview)
        self.attachment.show()
        if self.was_visible_before_capture:
            self.show()
            self.raise_()
            self.activateWindow()
        self.input.setFocus()
        self.status.setText("Ảnh đã đính kèm • Ctrl+Enter để gửi")

    def clear_pending_image(self) -> None:
        self.pending_image = None
        self.attachment_preview.clear()
        self.attachment.hide()

    def handle_hotkey(self, hotkey_id: int) -> None:
        if self.settings_scroll.isVisible() and hotkey_id in (5, 6):
            self.status.setText("Chọn vùng và gửi nội dung chỉ dùng trong Chat")
            return
        actions = {
            1: self.toggle_click_through,
            2: self.toggle_visible,
            3: lambda: self.adjust_opacity(-0.05),
            4: lambda: self.adjust_opacity(0.05),
            5: self.start_capture,
            6: self.submit,
            7: self.open_settings,
        }
        action = actions.get(hotkey_id)
        if action:
            action()

    def quit_app(self) -> None:
        self.exiting = True
        self.tray.hide()
        for cam in self.dxcam_cameras.values():
            try:
                cam.stop()
                cam.release()
            except Exception:
                pass
        self.dxcam_cameras.clear()
        QApplication.quit()


def register_hotkeys(settings: QSettings) -> list[str]:
    unregister_hotkeys()
    failures = []
    user32 = ctypes.windll.user32
    for hotkey_id, (label, _) in HOTKEYS.items():
        text = hotkey_text(settings, hotkey_id)
        try:
            modifiers, virtual_key = hotkey_to_win(text)
            if not user32.RegisterHotKey(None, hotkey_id, modifiers, virtual_key):
                failures.append(f"{label} ({text})")
        except ValueError:
            failures.append(f"{label} ({text})")
    return failures


def unregister_hotkeys() -> None:
    for hotkey_id in HOTKEYS:
        ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)


def self_check() -> None:
    assert chat_endpoint("https://api.example.test/v1/") == "https://api.example.test/v1/chat/completions"
    assert chat_endpoint("https://api.example.test/v1/chat/completions") == "https://api.example.test/v1/chat/completions"
    assert compose_image_prompt("Phân tích ảnh", "Giải câu 2") == "Phân tích ảnh\n\nGiải câu 2"
    assert compose_image_prompt("", "") == "Hãy phân tích ảnh này."
    assert assistant_text({"choices": [{"message": {"content": "ok"}}]}) == "ok"
    assert assistant_text({"choices": [{"message": {"content": [{"type": "text", "text": "ok"}]}}]}) == "ok"
    assert assistant_text({"choices": [{"message": {"content": "", "reasoning_content": "reason"}}]}) == "reason"
    assert assistant_text({"choices": [{"text": "legacy"}]}) == "legacy"
    assert assistant_text({"choices": [{"delta": {"content": "delta"}}]}) == "delta"
    assert assistant_text({"output_text": "responses"}) == "responses"
    assert assistant_text({"output": [{"content": [{"type": "output_text", "text": "nested"}]}]}) == "nested"
    assert assistant_text({"response": "ollama-style"}) == "ollama-style"
    assert assistant_text({"choices": []}) == ""
    assert "choices=0" in response_schema({"choices": []})
    print("self-check: ok")


def dxcam_self_check() -> None:
    try:
        import dxcam

        camera = dxcam.create(output_color="RGB", processor_backend="numpy")
        frame = camera.grab()
        if frame is None or frame.ndim != 3 or frame.shape[2] != 3:
            raise RuntimeError("DXcam không trả về khung hình RGB hợp lệ.")
    except Exception as error:
        LOGGER.exception("DXcam frozen self-check failed: %s", error)
        os._exit(2)
    # comtypes/dxcam 0.3 can access freed COM pointers during interpreter teardown.
    os._exit(0)


def main() -> int:
    if "--self-check" in sys.argv:
        self_check()
        return 0
    if "--dxcam-self-check" in sys.argv:
        dxcam_self_check()
    if sys.platform != "win32":
        print("Ứng dụng này chỉ hỗ trợ Windows.", file=sys.stderr)
        return 1

    enable_dpi_awareness()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setQuitOnLastWindowClosed(False)
    settings = QSettings()

    window = OverlayWindow(settings)
    native_filter = HotkeyFilter(window.handle_hotkey)
    app.installNativeEventFilter(native_filter)
    failures = register_hotkeys(settings)
    window.hotkey_failures = failures
    app.aboutToQuit.connect(unregister_hotkeys)

    screen = QApplication.primaryScreen().availableGeometry()
    window.move(screen.right() - window.width() - 28, screen.top() + 70)
    window.show()
    if failures:
        window.tray.showMessage(
            APP_NAME,
            "Không đăng ký được phím tắt: " + ", ".join(failures),
            QSystemTrayIcon.MessageIcon.Warning,
            5000,
        )
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
