from __future__ import annotations

import base64
import ctypes
import hashlib
import html
import http.server
import json
import logging
import os
import re
import secrets
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from ctypes import wintypes
from datetime import datetime
from logging.handlers import RotatingFileHandler

from PySide6.QtCore import (
    QAbstractNativeEventFilter,
    QByteArray,
    QBuffer,
    QEasingCurve,
    QEvent,
    QIODevice,
    QPoint,
    QObject,
    Property,
    QPropertyAnimation,
    QRect,
    QRectF,
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
    QFileDialog,
    QFormLayout,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
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
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

APP_NAME = "Overlay AI"
APP_VERSION = "1.1"
ORG_NAME = "LocalTools"
CODEX_AUTH_URL = "https://auth.openai.com/oauth/authorize"
CODEX_TOKEN_URL = "https://auth.openai.com/oauth/token"
CODEX_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
CODEX_REDIRECT_URI = "http://localhost:1455/auth/callback"
CODEX_CALLBACK_HOST = "127.0.0.1"
CODEX_CALLBACK_PORT = 1455
CODEX_API_URL = "https://chatgpt.com/backend-api/codex/responses"
CODEX_SCOPE = "openid email profile offline_access"
CODEX_REFRESH_LOCK = threading.Lock()
GEMINI_KEY_LOCK = threading.Lock()
GEMINI_KEY_INDEX = 0
PROVIDER_MODELS = {
    "gemini": [
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-pro-preview",
        "gemini-3.1-flash-lite-preview",
        "gemini-3-flash-preview",
        "gemma-4-31b-it",
    ],
    "codex": [
        "gpt-5.6-sol",
        "gpt-5.6-sol-review",
        "gpt-5.6-terra",
        "gpt-5.6-terra-review",
        "gpt-5.6-luna",
        "gpt-5.6-luna-review",
        "gpt-5.5",
        "gpt-5.5-review",
        "gpt-5.4",
        "gpt-5.4-review",
        "gpt-5.4-mini",
        "gpt-5.3-codex-spark",
    ],
}
WM_NCHITTEST = 0x0084
WM_HOTKEY = 0x0312
HTLEFT = 10
HTRIGHT = 11
HTTOP = 12
HTTOPLEFT = 13
HTTOPRIGHT = 14
HTBOTTOM = 15
HTBOTTOMLEFT = 16
HTBOTTOMRIGHT = 17
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
    8: ("Tạo session mới", "Ctrl+N"),
}
WH_MOUSE_LL = 14
WM_XBUTTONDOWN = 0x020B
XBUTTON1 = 0x0001
XBUTTON2 = 0x0002
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_LWIN = 0x5B
VK_RWIN = 0x5C
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


def mouse_hotkey_parts(text: str) -> tuple[int, str] | None:
    parts = [part.strip() for part in text.split("+") if part.strip()]
    if not parts or parts[-1].lower() not in ("mouse4", "mouse5"):
        return None
    modifier_map = {
        "ctrl": MOD_CONTROL,
        "control": MOD_CONTROL,
        "alt": MOD_ALT,
        "shift": MOD_SHIFT,
        "win": MOD_WIN,
        "meta": MOD_WIN,
    }
    modifiers = 0
    for part in parts[:-1]:
        flag = modifier_map.get(part.lower())
        if flag is None or modifiers & flag:
            raise ValueError(f"Phím tắt chuột không hợp lệ: {text}")
        modifiers |= flag
    return modifiers, parts[-1].title()


def format_mouse_hotkey(modifiers: Qt.KeyboardModifier, button: str) -> str:
    parts = []
    if modifiers & Qt.KeyboardModifier.ControlModifier:
        parts.append("Ctrl")
    if modifiers & Qt.KeyboardModifier.AltModifier:
        parts.append("Alt")
    if modifiers & Qt.KeyboardModifier.ShiftModifier:
        parts.append("Shift")
    if modifiers & Qt.KeyboardModifier.MetaModifier:
        parts.append("Win")
    return "+".join(parts + [button])


def normalize_gemini_keys(keys) -> list[str]:
    return list(dict.fromkeys(str(key).strip() for key in keys if str(key).strip()))


def normalize_openai_profiles(profiles) -> list[dict]:
    normalized: dict[str, dict] = {}
    if not isinstance(profiles, list):
        return []
    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        base_url = str(profile.get("base_url", "")).strip().rstrip("/")
        model = str(profile.get("model", "")).strip()
        if not base_url:
            continue
        stored_models = profile.get("models", [])
        if isinstance(stored_models, str):
            stored_models = [stored_models]
        models = list(
            dict.fromkeys(
                [str(item).strip() for item in stored_models if str(item).strip()]
                + ([model] if model else [])
            )
        )[:20]
        normalized[base_url] = {
            "base_url": base_url,
            "model": model,
            "models": models,
            "api_key": str(profile.get("api_key", "")).strip(),
            "gemini_web2api": bool(profile.get("gemini_web2api", False)),
        }
    return list(normalized.values())[-20:]


def rotated_gemini_keys(keys: list[str]) -> list[str]:
    global GEMINI_KEY_INDEX
    if not keys:
        return []
    with GEMINI_KEY_LOCK:
        start = GEMINI_KEY_INDEX % len(keys)
        GEMINI_KEY_INDEX = (GEMINI_KEY_INDEX + 1) % len(keys)
    return keys[start:] + keys[:start]


def hotkey_to_win(text: str, allow_repeat: bool = False) -> tuple[int, int]:
    if mouse_hotkey_parts(text) is not None:
        raise ValueError(f"Phím tắt chuột không thể đăng ký bằng RegisterHotKey: {text}")
    sequence = QKeySequence.fromString(text, QKeySequence.SequenceFormat.PortableText)
    if sequence.isEmpty() or sequence.count() != 1:
        raise ValueError(f"Phím tắt không hợp lệ: {text}")
    combination = sequence[0]
    key = int(combination.key())
    modifiers = combination.keyboardModifiers()
    win_modifiers = 0
    if modifiers & Qt.KeyboardModifier.ControlModifier:
        win_modifiers |= MOD_CONTROL
    if modifiers & Qt.KeyboardModifier.AltModifier:
        win_modifiers |= MOD_ALT
    if modifiers & Qt.KeyboardModifier.ShiftModifier:
        win_modifiers |= MOD_SHIFT
    if modifiers & Qt.KeyboardModifier.MetaModifier:
        win_modifiers |= MOD_WIN
    if not win_modifiers:
        raise ValueError(f"Phím tắt cần ít nhất một modifier: {text}")
    if not allow_repeat:
        win_modifiers |= MOD_NOREPEAT
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


def load_gemini_keys(settings: QSettings) -> list[str]:
    encrypted = settings.value("gemini/keys", "", str)
    if not encrypted:
        return []
    payload = json.loads(unprotect_secret(encrypted))
    if not isinstance(payload, list):
        raise ValueError("Danh sách Gemini API key đã lưu không hợp lệ.")
    return normalize_gemini_keys(payload)


def save_gemini_keys(settings: QSettings, keys) -> None:
    normalized = normalize_gemini_keys(keys)
    settings.setValue("gemini/keys", protect_secret(json.dumps(normalized)))


def load_openai_profiles(settings: QSettings) -> list[dict]:
    encrypted = settings.value("openai/profiles", "", str)
    if not encrypted:
        return []
    payload = json.loads(unprotect_secret(encrypted))
    if not isinstance(payload, list):
        raise ValueError("Danh sách OpenAI-compatible profile đã lưu không hợp lệ.")
    return normalize_openai_profiles(payload)


def save_openai_profiles(settings: QSettings, profiles) -> None:
    normalized = normalize_openai_profiles(profiles)
    settings.setValue("openai/profiles", protect_secret(json.dumps(normalized)))


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
        r'(?i)("(?:api[_-]?key|access[_-]?token|refresh[_-]?token|id[_-]?token|authorization|code|account[_-]?id|chatgpt[_-]?account[_-]?id)"\s*:\s*")[^"]*(")',
        r"\1<redacted>\2",
        value,
    )
    value = re.sub(r"(?i)Bearer\s+[^\s,;]+", "Bearer <redacted>", value)
    value = re.sub(
        r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*\b",
        "<redacted-jwt>",
        value,
    )
    value = re.sub(r"[A-Za-z0-9+/]{512,}={0,2}", "<redacted-long-base64>", value)
    return value[:16_384]


LOGGER = configure_logging()


def unique_image_path(folder: str, timestamp: str | None = None) -> str:
    if not os.path.isdir(folder):
        raise ValueError("Folder lưu ảnh không tồn tại.")
    stamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    base = os.path.join(folder, f"OverlayAI_{stamp}")
    candidate = base + ".png"
    suffix = 1
    while os.path.exists(candidate):
        candidate = f"{base}_{suffix}.png"
        suffix += 1
    return candidate


def save_chat_image(folder: str, image: bytes, timestamp: str | None = None) -> str:
    for _attempt in range(10_000):
        path = unique_image_path(folder, timestamp)
        try:
            with open(path, "xb") as output:
                output.write(image)
            return path
        except FileExistsError:
            continue
    raise OSError("Không thể tạo tên file ảnh duy nhất.")


def resize_hit_test(x: int, y: int, rect: tuple[int, int, int, int], border: int) -> int:
    left, top, right, bottom = rect
    near_left = left <= x < left + border
    near_right = right - border <= x < right
    near_top = top <= y < top + border
    near_bottom = bottom - border <= y < bottom
    if near_top and near_left:
        return HTTOPLEFT
    if near_top and near_right:
        return HTTOPRIGHT
    if near_bottom and near_left:
        return HTBOTTOMLEFT
    if near_bottom and near_right:
        return HTBOTTOMRIGHT
    if near_left:
        return HTLEFT
    if near_right:
        return HTRIGHT
    if near_top:
        return HTTOP
    if near_bottom:
        return HTBOTTOM
    return 0


def migrate_provider_settings(settings: QSettings) -> None:
    if not settings.value("provider/migrated", False, bool):
        mappings = {
            "api/base_url": "openai/base_url",
            "api/model": "openai/model",
            "api/models": "openai/models",
            "api/key": "openai/key",
        }
        for old_key, new_key in mappings.items():
            if settings.contains(old_key) and not settings.contains(new_key):
                settings.setValue(new_key, settings.value(old_key))
        settings.setValue("provider/current", "openai")
        settings.setValue("provider/migrated", True)

    if not settings.value("provider/editable_model_lists", False, bool):
        retired = {
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
        }
        for provider, presets in PROVIDER_MODELS.items():
            stored = settings.value(f"{provider}/models", [])
            if isinstance(stored, str):
                stored = [stored]
            current = settings.value(f"{provider}/model", "", str).strip()
            models = list(
                dict.fromkeys(
                    model
                    for model in presets
                    + [str(item).strip() for item in stored]
                    + ([current] if current else [])
                    if model and model not in retired
                )
            )
            settings.setValue(f"{provider}/models", models[:20])
            if current in retired:
                settings.setValue(f"{provider}/model", presets[0] if presets else "")
        settings.setValue("provider/editable_model_lists", True)

    if not settings.value("provider/gemini_3_5_flash_added", False, bool):
        models = settings.value("gemini/models", [])
        if isinstance(models, str):
            models = [models]
        models = [str(item).strip() for item in models if str(item).strip()]
        if "gemini-3.5-flash" not in models:
            models.insert(0, "gemini-3.5-flash")
        settings.setValue("gemini/models", models[:20])
        settings.setValue("provider/gemini_3_5_flash_added", True)

    if not settings.contains("gemini/keys") and settings.contains("gemini/key"):
        try:
            legacy_key = unprotect_secret(settings.value("gemini/key", "", str)).strip()
            save_gemini_keys(settings, [legacy_key] if legacy_key else [])
            settings.remove("gemini/key")
        except Exception as error:
            LOGGER.warning("Gemini legacy key migration failed type=%s", type(error).__name__)

    if not settings.contains("openai/profiles") and any(
        settings.contains(key) for key in ("openai/base_url", "openai/model", "openai/key")
    ):
        try:
            base_url = settings.value("openai/base_url", "https://api.openai.com/v1", str).strip()
            model = settings.value("openai/model", "gpt-4o-mini", str).strip()
            api_key = unprotect_secret(settings.value("openai/key", "", str))
            save_openai_profiles(
                settings,
                [{"base_url": base_url, "model": model, "models": [model], "api_key": api_key}],
            )
        except Exception as error:
            LOGGER.warning("OpenAI profile migration failed type=%s", type(error).__name__)
    settings.sync()


def base64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def pkce_challenge(verifier: str) -> str:
    return base64url(hashlib.sha256(verifier.encode("ascii")).digest())


def create_pkce() -> tuple[str, str]:
    verifier = base64url(secrets.token_bytes(64))
    return verifier, pkce_challenge(verifier)


def codex_authorization_url(state: str, challenge: str) -> str:
    return CODEX_AUTH_URL + "?" + urllib.parse.urlencode(
        {
            "client_id": CODEX_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": CODEX_REDIRECT_URI,
            "scope": CODEX_SCOPE,
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "prompt": "login",
            "id_token_add_organizations": "true",
            "codex_cli_simplified_flow": "true",
        }
    )


def oauth_callback_code(target: str, expected_state: str) -> str:
    parsed = urllib.parse.urlparse(target)
    query = urllib.parse.parse_qs(parsed.query)
    if parsed.path != "/auth/callback":
        raise ValueError("Callback path không hợp lệ.")
    if not secrets.compare_digest(query.get("state", [""])[0], expected_state):
        raise ValueError("OAuth state không khớp; yêu cầu đã bị từ chối.")
    if query.get("error"):
        raise ValueError(query.get("error_description", query["error"])[0])
    code = query.get("code", [""])[0]
    if not code:
        raise ValueError("Callback không có authorization code.")
    return code


def jwt_payload(token: str) -> dict:
    try:
        part = token.split(".")[1]
        part += "=" * (-len(part) % 4)
        payload = json.loads(base64.urlsafe_b64decode(part).decode("utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (IndexError, ValueError, TypeError, json.JSONDecodeError):
        return {}


def token_identity(*tokens: str) -> tuple[str, str]:
    account_id = ""
    email = ""
    for token in tokens:
        claims = jwt_payload(token)
        email = email or str(claims.get("email", ""))
        candidates = [claims]
        candidates.extend(value for value in claims.values() if isinstance(value, dict))
        for candidate in candidates:
            account_id = account_id or str(
                candidate.get("chatgpt_account_id") or candidate.get("account_id") or ""
            )
    return account_id, email


def oauth_token_request(fields: dict[str, str]) -> dict:
    request = urllib.request.Request(
        CODEX_TOKEN_URL,
        data=urllib.parse.urlencode(fields).encode("ascii"),
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": f"OverlayAI/{APP_VERSION} (Windows; experimental Codex OAuth)",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        error.read()
        raise RuntimeError(f"OAuth HTTP {error.code}. Hãy thử đăng nhập lại.") from error
    if not isinstance(payload, dict) or not payload.get("access_token"):
        raise RuntimeError("OAuth không trả về access token hợp lệ.")
    return payload


def make_token_bundle(payload: dict, previous: dict | None = None) -> dict:
    previous = previous or {}
    access_token = str(payload.get("access_token", ""))
    refresh_token = str(payload.get("refresh_token") or previous.get("refresh_token") or "")
    id_token = str(payload.get("id_token") or previous.get("id_token") or "")
    account_id, email = token_identity(access_token, id_token)
    expires_in = max(0, int(payload.get("expires_in", 3600)))
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "id_token": id_token,
        "account_id": account_id or str(previous.get("account_id", "")),
        "email": email or str(previous.get("email", "")),
        "expires_at": int(time.time()) + expires_in,
        "updated_at": int(time.time()),
    }


def load_codex_bundle(settings: QSettings) -> dict:
    encrypted = settings.value("codex/token_bundle", "", str)
    if not encrypted:
        return {}
    payload = json.loads(unprotect_secret(encrypted))
    return payload if isinstance(payload, dict) else {}


def save_codex_bundle(settings: QSettings, bundle: dict) -> None:
    encrypted = protect_secret(json.dumps(bundle, separators=(",", ":")))
    settings.setValue("codex/token_bundle", encrypted)
    settings.sync()


def refresh_codex_bundle(bundle: dict, force: bool = False) -> dict:
    with CODEX_REFRESH_LOCK:
        try:
            current = load_codex_bundle(QSettings())
        except Exception:
            current = {}
        if (
            current.get("access_token")
            and int(current.get("updated_at", 0)) > int(bundle.get("updated_at", 0))
            and (not force or current.get("access_token") != bundle.get("access_token"))
        ):
            return current
        refresh_token = str(bundle.get("refresh_token", ""))
        if not refresh_token:
            raise RuntimeError("Phiên Codex đã hết hạn và không có refresh token. Hãy đăng nhập lại.")
        payload = oauth_token_request(
            {
                "grant_type": "refresh_token",
                "client_id": CODEX_CLIENT_ID,
                "refresh_token": refresh_token,
                "scope": "openid profile email",
            }
        )
        refreshed = make_token_bundle(payload, bundle)
        save_codex_bundle(QSettings(), refreshed)
        return refreshed


def canonical_parts(content) -> tuple[str, str]:
    if isinstance(content, str):
        return content, ""
    texts = []
    image_url = ""
    if isinstance(content, list):
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") in ("text", "input_text", "output_text"):
                texts.append(str(part.get("text", "")))
            elif part.get("type") in ("image_url", "input_image"):
                value = part.get("image_url", "")
                image_url = str(value.get("url", "") if isinstance(value, dict) else value)
    return "\n".join(value for value in texts if value), image_url


def codex_payload(model: str, messages: list[dict]) -> dict:
    instructions = "\n\n".join(
        canonical_parts(message.get("content"))[0]
        for message in messages
        if message.get("role") == "system"
    ).strip()
    items = []
    for message in messages:
        role = message.get("role")
        if role not in ("user", "assistant"):
            continue
        text, image_url = canonical_parts(message.get("content"))
        content = []
        if text:
            content.append({"type": "output_text" if role == "assistant" else "input_text", "text": text})
        if image_url and role == "user":
            content.append({"type": "input_image", "image_url": image_url})
        if content:
            items.append({"role": role, "content": content})
    return {"model": model, "instructions": instructions, "input": items, "stream": True, "store": False}


def gemini_payload(messages: list[dict]) -> dict:
    system = "\n\n".join(
        canonical_parts(message.get("content"))[0]
        for message in messages
        if message.get("role") == "system"
    ).strip()
    contents = []
    for message in messages:
        role = message.get("role")
        if role not in ("user", "assistant"):
            continue
        text, image_url = canonical_parts(message.get("content"))
        parts = []
        if text:
            parts.append({"text": text})
        if image_url.startswith("data:") and "," in image_url:
            metadata, data = image_url.split(",", 1)
            mime_type = metadata[5:].split(";", 1)[0]
            parts.append({"inlineData": {"mimeType": mime_type, "data": data}})
        if parts:
            contents.append({"role": "model" if role == "assistant" else "user", "parts": parts})
    payload = {"contents": contents}
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    return payload


def gemini_text(payload: dict) -> str:
    candidates = payload.get("candidates", []) if isinstance(payload, dict) else []
    if not candidates or not isinstance(candidates[0], dict):
        return ""
    content = candidates[0].get("content", {})
    parts = content.get("parts", []) if isinstance(content, dict) else []
    return "\n".join(
        str(part.get("text", "")) for part in parts if isinstance(part, dict) and part.get("text")
    ).strip()


def codex_sse_text(raw: str) -> tuple[str, bool]:
    deltas = []
    final_payload = None
    for line in raw.splitlines():
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if not data or data == "[DONE]":
            continue
        try:
            event = json.loads(data)
        except json.JSONDecodeError:
            continue
        event_type = event.get("type", "") if isinstance(event, dict) else ""
        if event_type == "response.output_text.delta":
            delta = event.get("delta", "")
            if isinstance(delta, str):
                deltas.append(delta)
        elif event_type == "response.completed":
            final_payload = event.get("response")
    if deltas:
        return "".join(deltas).strip(), True
    if isinstance(final_payload, dict):
        return assistant_text(final_payload).strip(), False
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return "", False
    return assistant_text(payload).strip(), False


def chat_endpoint(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    if not value:
        raise ValueError("Base URL không được để trống.")
    if value.endswith("/chat/completions"):
        return value
    return f"{value}/chat/completions"


def conversations_endpoint(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    if not value:
        raise ValueError("Base URL không được để trống.")
    suffix = "/chat/completions"
    if value.endswith(suffix):
        value = value[: -len(suffix)]
    return f"{value}/conversations"


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


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class MouseHotkeyHook(QObject):
    triggered = Signal(int)

    def __init__(self, callback):
        super().__init__()
        self.triggered.connect(callback)
        self.bindings: dict[tuple[int, str], int] = {}
        self.handle = None
        self._proc = None

    @staticmethod
    def current_modifiers() -> int:
        user32 = ctypes.windll.user32
        modifiers = 0
        if user32.GetAsyncKeyState(VK_CONTROL) & 0x8000:
            modifiers |= MOD_CONTROL
        if user32.GetAsyncKeyState(VK_MENU) & 0x8000:
            modifiers |= MOD_ALT
        if user32.GetAsyncKeyState(VK_SHIFT) & 0x8000:
            modifiers |= MOD_SHIFT
        if (user32.GetAsyncKeyState(VK_LWIN) | user32.GetAsyncKeyState(VK_RWIN)) & 0x8000:
            modifiers |= MOD_WIN
        return modifiers

    def update_bindings(self, settings: QSettings) -> list[str]:
        bindings: dict[tuple[int, str], int] = {}
        failures = []
        for hotkey_id, (label, _) in HOTKEYS.items():
            text = hotkey_text(settings, hotkey_id)
            try:
                parts = mouse_hotkey_parts(text)
            except ValueError:
                failures.append(f"{label} ({text})")
                continue
            if parts is None:
                continue
            if parts in bindings:
                failures.append(f"{label} ({text})")
                continue
            bindings[parts] = hotkey_id
        self.bindings = bindings
        if not bindings:
            self.uninstall()
            return failures
        if self.handle is None:
            try:
                self.install()
            except OSError as error:
                LOGGER.error("mouse hotkey hook install failed: %s", error)
                failures.extend(
                    f"{HOTKEYS[hotkey_id][0]} ({hotkey_text(settings, hotkey_id)})"
                    for hotkey_id in bindings.values()
                )
        return failures

    def install(self) -> None:
        if self.handle is not None:
            return
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        procedure_type = ctypes.WINFUNCTYPE(
            ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
        )
        user32.SetWindowsHookExW.argtypes = [
            ctypes.c_int,
            procedure_type,
            wintypes.HINSTANCE,
            wintypes.DWORD,
        ]
        user32.SetWindowsHookExW.restype = ctypes.c_void_p
        user32.CallNextHookEx.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        user32.CallNextHookEx.restype = ctypes.c_ssize_t
        user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
        user32.UnhookWindowsHookEx.restype = wintypes.BOOL
        kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        kernel32.GetModuleHandleW.restype = wintypes.HINSTANCE

        def procedure(code, message, data):
            if code >= 0 and message == WM_XBUTTONDOWN:
                event = ctypes.cast(data, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                xbutton = (event.mouseData >> 16) & 0xFFFF
                button = {XBUTTON1: "Mouse4", XBUTTON2: "Mouse5"}.get(xbutton)
                if button is not None:
                    hotkey_id = self.bindings.get((self.current_modifiers(), button))
                    if hotkey_id is not None:
                        self.triggered.emit(hotkey_id)
            return user32.CallNextHookEx(self.handle, code, message, data)

        self._proc = procedure_type(procedure)
        self.handle = user32.SetWindowsHookExW(
            WH_MOUSE_LL, self._proc, kernel32.GetModuleHandleW(None), 0
        )
        if not self.handle:
            self._proc = None
            raise ctypes.WinError()

    def uninstall(self) -> None:
        if self.handle is not None:
            ctypes.windll.user32.UnhookWindowsHookEx(self.handle)
        self.handle = None
        self._proc = None


class CodexOAuthWorker(QThread):
    succeeded = Signal(dict)
    failed = Signal(str)

    def run(self) -> None:
        state = base64url(secrets.token_bytes(32))
        verifier, challenge = create_pkce()
        result: dict[str, str] = {}

        class CallbackHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 - stdlib API
                try:
                    result["code"] = oauth_callback_code(self.path, state)
                    status = 200
                except ValueError as error:
                    result["error"] = str(error)
                    status = 400
                message = (
                    "Đăng nhập thành công. Bạn có thể đóng tab này."
                    if status == 200
                    else "Đăng nhập thất bại. Hãy quay lại Overlay AI."
                )
                body = f"<!doctype html><meta charset='utf-8'><title>Overlay AI</title><p>{html.escape(message)}</p>".encode()
                self.send_response(status)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, _format: str, *_args) -> None:
                return

        try:
            server = http.server.HTTPServer((CODEX_CALLBACK_HOST, CODEX_CALLBACK_PORT), CallbackHandler)
            server.timeout = 180
            try:
                if not webbrowser.open(codex_authorization_url(state, challenge)):
                    raise RuntimeError("Không mở được trình duyệt hệ thống.")
                server.handle_request()
            finally:
                server.server_close()
            if not result:
                raise TimeoutError("Đăng nhập Codex quá thời gian 3 phút.")
            if result.get("error"):
                raise RuntimeError(result["error"])
            payload = oauth_token_request(
                {
                    "grant_type": "authorization_code",
                    "client_id": CODEX_CLIENT_ID,
                    "code": result["code"],
                    "redirect_uri": CODEX_REDIRECT_URI,
                    "code_verifier": verifier,
                }
            )
            bundle = make_token_bundle(payload)
            if not bundle["account_id"]:
                raise RuntimeError("Token không chứa ChatGPT account ID cần cho Codex backend.")
            save_codex_bundle(QSettings(), bundle)
            self.succeeded.emit(bundle)
        except Exception as error:
            LOGGER.error("Codex OAuth failed: %s", type(error).__name__)
            self.failed.emit(str(error))


class ConversationCreateWorker(QThread):
    succeeded = Signal()
    failed = Signal(str)

    def __init__(self, endpoint: str, api_key: str):
        super().__init__()
        self.endpoint = endpoint
        self.api_key = api_key

    def run(self) -> None:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"OverlayAI/{APP_VERSION} (Gemini Web2API client)",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            self.endpoint, data=b"{}", headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                status = response.getcode()
                details = response.read(1200).decode("utf-8", errors="replace")
            if status != 201:
                raise RuntimeError(
                    f"Gemini Web2API trả HTTP {status}, cần HTTP 201. "
                    + safe_response_log(details)
                )
            self.succeeded.emit()
        except urllib.error.HTTPError as error:
            details = error.read(1200).decode("utf-8", errors="replace")
            LOGGER.error(
                "Gemini Web2API conversation create failed status=%d body=%s",
                error.code,
                safe_response_log(details),
            )
            self.failed.emit(
                f"Gemini Web2API HTTP {error.code}: " + safe_response_log(details)
            )
        except Exception as error:
            LOGGER.error(
                "Gemini Web2API conversation create failed type=%s", type(error).__name__
            )
            self.failed.emit(str(error))


class ChatWorker(QThread):
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, provider: str, model: str, messages: list[dict], config: dict):
        super().__init__()
        self.provider = provider
        self.model = model
        self.messages = messages
        self.config = config
        self._response = None
        self._response_lock = threading.Lock()

    def cancel(self) -> None:
        self.requestInterruption()
        with self._response_lock:
            response = self._response
        if response is not None:
            response.close()

    def _request(self, endpoint: str, payload: dict, headers: dict) -> tuple[str, str]:
        if self.isInterruptionRequested():
            raise InterruptedError("Request đã bị hủy.")
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
        response = urllib.request.urlopen(request, timeout=120)
        with self._response_lock:
            self._response = response
        try:
            chunks = []
            while True:
                if self.isInterruptionRequested():
                    raise InterruptedError("Request đã bị hủy.")
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            raw = b"".join(chunks)
            charset = response.headers.get_content_charset() or "utf-8"
            return raw.decode(charset, errors="replace"), response.headers.get("Content-Type", "")
        finally:
            response.close()
            with self._response_lock:
                if self._response is response:
                    self._response = None

    def _gemini_request(self) -> tuple[str, dict]:
        keys = rotated_gemini_keys(self.config["api_keys"])
        if not keys:
            raise ValueError("Chưa cấu hình Gemini API key.")
        last_error = None
        for index, api_key in enumerate(keys):
            endpoint = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                + urllib.parse.quote(self.model, safe="")
                + ":generateContent?key="
                + urllib.parse.quote(api_key, safe="")
            )
            try:
                raw, _content_type = self._request(
                    endpoint,
                    gemini_payload(self.messages),
                    {
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "User-Agent": f"OverlayAI/{APP_VERSION} (Windows; Gemini API client)",
                    },
                )
                payload = json.loads(raw)
                return gemini_text(payload), payload
            except urllib.error.HTTPError as error:
                last_error = error
                if error.code not in (401, 403, 429) or index == len(keys) - 1:
                    raise
                LOGGER.warning(
                    "Gemini key rejected; trying next key status=%d key_index=%d",
                    error.code,
                    index,
                )
                error.close()
        raise last_error or RuntimeError("Không có Gemini API key khả dụng.")

    def _codex_request(self) -> str:
        bundle = dict(self.config["token_bundle"])
        if int(bundle.get("expires_at", 0)) <= int(time.time()) + 60:
            bundle = refresh_codex_bundle(bundle)
        for attempt in range(2):
            headers = {
                "Authorization": f"Bearer {bundle['access_token']}",
                "ChatGPT-Account-ID": bundle["account_id"],
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                "OpenAI-Beta": "responses=experimental",
                "originator": "OverlayAI",
                "User-Agent": f"OverlayAI/{APP_VERSION} (Windows)",
            }
            try:
                raw, _content_type = self._request(
                    CODEX_API_URL, codex_payload(self.model, self.messages), headers
                )
                text, _partial = codex_sse_text(raw)
                return text
            except urllib.error.HTTPError as error:
                if error.code == 401 and attempt == 0:
                    bundle = refresh_codex_bundle(bundle, force=True)
                    continue
                raise
        return ""

    def run(self) -> None:
        request_id = f"{id(self):x}"
        LOGGER.info(
            "chat request id=%s provider=%s model=%s messages=%d",
            request_id,
            self.provider,
            self.model,
            len(self.messages),
        )
        try:
            if self.provider == "openai":
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": f"OverlayAI/{APP_VERSION} (Windows; OpenAI-compatible API client)",
                }
                if self.config.get("api_key"):
                    headers["Authorization"] = f"Bearer {self.config['api_key']}"
                raw, _content_type = self._request(
                    self.config["endpoint"],
                    {"model": self.model, "messages": self.messages, "stream": False},
                    headers,
                )
                payload = json.loads(raw)
                text = assistant_text(payload).strip()
            elif self.provider == "gemini":
                text, payload = self._gemini_request()
            elif self.provider == "codex":
                text = self._codex_request()
                payload = {}
            else:
                raise ValueError(f"Provider không hợp lệ: {self.provider}")
            if self.isInterruptionRequested():
                return
            if not text:
                schema = response_schema(payload)
                raise RuntimeError(
                    f"Provider trả về HTTP 200 nhưng không có nội dung. Model: {self.model}. "
                    f"Request ID: {request_id}. Schema: {schema}. Log: {LOG_PATH}"
                )
            self.succeeded.emit(text)
        except urllib.error.HTTPError as error:
            if self.isInterruptionRequested():
                return
            details = error.read().decode("utf-8", errors="replace")[:1200]
            LOGGER.error(
                "chat HTTP error id=%s provider=%s status=%d body=%s",
                request_id,
                self.provider,
                error.code,
                safe_response_log(details),
            )
            if self.provider == "codex" and error.code == 403:
                self.failed.emit(
                    "Codex HTTP 403: backend nội bộ từ chối tài khoản, model hoặc danh tính Overlay AI; "
                    "ứng dụng không giả danh phiên bản Codex CLI. " + safe_response_log(details)
                )
            elif error.code == 429:
                self.failed.emit("HTTP 429: provider đang giới hạn tần suất. Hãy chờ rồi gửi lại.")
            elif error.code == 401 and self.provider == "codex":
                self.failed.emit("Phiên Codex không còn hợp lệ. Hãy đăng nhập lại trong Cài đặt.")
            elif error.code == 403 and (
                "error 1010" in details.lower() or "browser_signature_banned" in details
            ):
                self.failed.emit("Cloudflare Error 1010: dịch vụ đang chặn chữ ký HTTP của Overlay AI.")
            else:
                self.failed.emit(f"HTTP {error.code}: {safe_response_log(details)}")
        except Exception as error:
            if self.isInterruptionRequested():
                LOGGER.info("chat request canceled id=%s provider=%s", request_id, self.provider)
                return
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


class HotkeyEdit(QLineEdit):
    def __init__(self, value: str = ""):
        super().__init__(value)
        self.setReadOnly(True)
        self.setClearButtonEnabled(True)
        self.setPlaceholderText("Nhấn phím hoặc Mouse4/Mouse5")

    def hotkeyText(self) -> str:  # noqa: N802 - Qt-style API
        return self.text().strip()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            self.clear()
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Shift, Qt.Key.Key_Meta):
            event.accept()
            return
        value = QKeySequence(event.keyCombination()).toString(
            QKeySequence.SequenceFormat.PortableText
        )
        if value:
            self.setText(value)
        event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        button = {
            Qt.MouseButton.BackButton: "Mouse4",
            Qt.MouseButton.ForwardButton: "Mouse5",
        }.get(event.button())
        if button:
            self.setText(format_mouse_hotkey(event.modifiers(), button))
            event.accept()
            return
        super().mousePressEvent(event)


class NoWheelComboBox(QComboBox):
    def wheelEvent(self, event) -> None:
        event.ignore()

    def showPopup(self) -> None:  # noqa: N802 - Qt API
        super().showPopup()
        self.view().window().setWindowOpacity(self.window().windowOpacity())


class NoWheelSlider(QSlider):
    def wheelEvent(self, event) -> None:
        event.ignore()


class AnimatedToggle(QCheckBox):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._knob_position = 0.0
        self.setFixedSize(56, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName("Bật hoặc tắt lưu ảnh đã gửi")
        self.animation = QPropertyAnimation(self, b"knobPosition", self)
        self.animation.setDuration(180)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self.animate_toggle)

    def hitButton(self, position: QPoint) -> bool:  # noqa: N802 - Qt API
        return self.rect().contains(position)

    def knob_position(self) -> float:
        return self._knob_position

    def set_knob_position(self, position: float) -> None:
        self._knob_position = position
        self.update()

    knobPosition = Property(float, knob_position, set_knob_position)

    def animate_toggle(self, checked: bool) -> None:
        self.animation.stop()
        self.animation.setStartValue(self._knob_position)
        self.animation.setEndValue(1.0 if checked else 0.0)
        self.animation.start()
        self.setAccessibleDescription("Bật" if checked else "Tắt")

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = QRectF(0, 1, self.width(), self.height() - 2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#249b62" if self.isChecked() else "#555b66"))
        painter.drawRoundedRect(track, 12, 12)
        painter.setPen(QColor("white"))
        text_rect = QRectF(3, 1, 31, 24) if self.isChecked() else QRectF(22, 1, 31, 24)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "Bật" if self.isChecked() else "Tắt")
        knob_size = 18
        knob_x = 4 + self._knob_position * (self.width() - knob_size - 8)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("white"))
        painter.drawEllipse(QRectF(knob_x, 4, knob_size, knob_size))


class SettingsDialog(QDialog):
    def __init__(self, settings: QSettings, parent: QWidget | None = None):
        super().__init__(parent)
        self.settings = settings
        self.overlay = parent
        migrate_provider_settings(settings)
        self.loading_provider = True
        self.oauth_worker: CodexOAuthWorker | None = None
        self.test_worker: ChatWorker | None = None
        self.current_provider = settings.value("provider/current", "openai", str)
        self.setObjectName("settingsPanel")
        self.setWindowTitle("Cài đặt Overlay AI")
        self.setMinimumWidth(0)
        if parent is not None:
            self.setWindowOpacity(parent.windowOpacity())

        self.provider = NoWheelComboBox()
        self.provider.addItem("OpenAI-compatible", "openai")
        self.provider.addItem("Gemini API", "gemini")
        self.provider.addItem("Codex OAuth", "codex")
        provider_index = self.provider.findData(self.current_provider)
        self.provider.setCurrentIndex(max(0, provider_index))
        self.current_provider = self.provider.currentData()
        self.base_url = NoWheelComboBox()
        self.base_url.setEditable(True)
        self.base_url.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.base_url_save = QPushButton("Lưu profile")
        self.base_url_save.setToolTip("Lưu Base URL, API key và model hiện tại")
        self.base_url_save.clicked.connect(self.save_openai_profile)
        self.base_url_delete = QPushButton("Xóa")
        self.base_url_delete.setToolTip("Xóa profile có Base URL đang chọn")
        self.base_url_delete.clicked.connect(self.delete_openai_profile)
        self.base_url_row = QWidget()
        self.base_url_layout = QHBoxLayout(self.base_url_row)
        self.base_url_layout.setContentsMargins(0, 0, 0, 0)
        self.base_url_layout.setSpacing(6)
        self.base_url_layout.addWidget(self.base_url, 1)
        self.base_url_layout.addWidget(self.base_url_save)
        self.base_url_layout.addWidget(self.base_url_delete)
        self.model = NoWheelComboBox()
        self.model.setEditable(True)
        self.model_row = QWidget()
        self.model_layout = QHBoxLayout(self.model_row)
        self.model_layout.setContentsMargins(0, 0, 0, 0)
        self.model_layout.setSpacing(6)
        self.model_action = QPushButton()
        self.model_action.clicked.connect(self.toggle_model_saved)
        self.model_test = QPushButton("Test")
        self.model_test.setToolTip("Gửi một prompt tối thiểu để kiểm tra model đang chọn")
        self.model_test.clicked.connect(self.test_current_model)
        self.model_layout.addWidget(self.model, 1)
        self.model_layout.addWidget(self.model_action)
        self.model_layout.addWidget(self.model_test)
        self.model.currentIndexChanged.connect(self.select_saved_model)
        self.model.editTextChanged.connect(self.update_model_action)
        self.update_model_action()
        self.model_test_status = QLabel("Chưa test model")
        self.model_test_status.setWordWrap(True)
        self.model_test_effect = QGraphicsOpacityEffect(self.model_test_status)
        self.model_test_effect.setOpacity(1.0)
        self.model_test_status.setGraphicsEffect(self.model_test_effect)
        self.model_test_animation = QPropertyAnimation(
            self.model_test_effect, b"opacity", self
        )
        self.model_test_animation.setDuration(450)
        self.model_test_animation.setStartValue(0.0)
        self.model_test_animation.setEndValue(1.0)
        self.model_test_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.model.editTextChanged.connect(self.model_changed)
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_web2api = QCheckBox(
            "Gemini Web2API: Ctrl+N tạo conversation mới trên server"
        )
        self.gemini_web2api.setToolTip(
            "Gọi POST /v1/conversations và chỉ xóa chat cục bộ khi server trả HTTP 201"
        )
        self.gemini_key_tabs = QTabWidget()
        self.gemini_key_tabs.setDocumentMode(True)
        self.gemini_key_tabs.setTabsClosable(True)
        self.gemini_key_tabs.setMinimumHeight(72)
        self.gemini_key_tabs.tabBar().setExpanding(False)
        self.gemini_key_tabs.tabCloseRequested.connect(self.remove_gemini_key_tab)
        self.gemini_key_tabs.tabBarClicked.connect(self.gemini_tab_clicked)
        add_page = QWidget()
        add_index = self.gemini_key_tabs.addTab(add_page, "+")
        self.gemini_key_tabs.setTabToolTip(add_index, "Thêm Gemini API key")
        self.gemini_key_tabs.tabBar().setTabButton(
            add_index, QTabBar.ButtonPosition.RightSide, None
        )
        self.gemini_key_tabs.tabBar().setTabButton(
            add_index, QTabBar.ButtonPosition.LeftSide, None
        )
        self.add_gemini_key_tab()
        self.codex_status = QLabel()
        self.codex_status.setWordWrap(True)
        self.codex_action = QPushButton("Đăng nhập")
        self.codex_action.clicked.connect(self.toggle_codex_session)
        self.image_prompt = QPlainTextEdit(
            settings.value(
                "capture/image_prompt",
                "Hãy phân tích ảnh chụp màn hình này và hỗ trợ ngắn gọn.",
                str,
            )
        )
        self.image_prompt.setMaximumHeight(72)
        self.image_prompt.setPlaceholderText("Prompt hệ thống thêm vào khi gửi kèm ảnh")
        self.image_folder = QLineEdit(settings.value("capture/save_folder", "", str))
        self.image_folder.setReadOnly(True)
        self.image_folder.setPlaceholderText("Chưa chọn folder lưu ảnh")
        self.choose_image_folder_button = QPushButton()
        self.choose_image_folder_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon)
        )
        self.choose_image_folder_button.setFixedSize(34, 34)
        self.choose_image_folder_button.setToolTip("Chọn folder lưu ảnh")
        self.choose_image_folder_button.setAccessibleName("Chọn folder lưu ảnh")
        self.open_image_folder_button = QPushButton("Mở")
        self.image_save_toggle = AnimatedToggle()
        self.image_save_toggle.setChecked(
            settings.value(
                "capture/save_enabled", bool(self.image_folder.text().strip()), bool
            )
        )
        self.image_save_toggle.set_knob_position(1.0 if self.image_save_toggle.isChecked() else 0.0)
        self.choose_image_folder_button.clicked.connect(self.choose_image_folder)
        self.open_image_folder_button.clicked.connect(self.open_image_folder)
        self.image_save_toggle.toggled.connect(self.image_save_toggled)
        self.image_folder_row = QWidget()
        image_folder_layout = QHBoxLayout(self.image_folder_row)
        image_folder_layout.setContentsMargins(0, 0, 0, 0)
        image_folder_layout.setSpacing(6)
        image_folder_layout.addWidget(self.image_folder, 1)
        image_folder_layout.addWidget(self.choose_image_folder_button)
        image_folder_layout.addWidget(self.open_image_folder_button)
        image_folder_layout.addWidget(self.image_save_toggle)
        self.update_image_folder_buttons()
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
        self.opacity = NoWheelSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(5, 100)
        self.opacity.setValue(round(float(settings.value("window/opacity", 0.94)) * 100))
        self.opacity.setToolTip("Độ hiển thị 5–100%; 5% là trong suốt nhất")
        self.opacity_value = QLabel(f"{self.opacity.value()}%")
        self.opacity.valueChanged.connect(self.change_opacity)
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
        self.form.addRow("Provider", self.provider)
        self.form.addRow("Base URL", self.base_url_row)
        self.form.addRow("Model", self.model_row)
        self.form.addRow("Trạng thái model", self.model_test_status)
        self.form.addRow("API key", self.api_key)
        self.form.addRow("", self.gemini_web2api)
        self.form.addRow("Gemini API keys", self.gemini_key_tabs)
        self.form.addRow("Tài khoản Codex", self.codex_status)
        self.form.addRow("", self.codex_action)
        self.form.addRow("Prompt khi gửi ảnh", self.image_prompt)
        self.form.addRow("Folder lưu ảnh đã gửi", self.image_folder_row)
        self.form.addRow("", self.always_on_top)
        self.form.addRow("", self.keep_on_top)
        self.form.addRow("", self.hide_during_capture)
        self.form.addRow("", self.show_selection_frame)
        self.form.addRow("", self.show_title)
        self.form.addRow("", self.auto_scroll)
        self.form.addRow("", self.allow_tiny_resize)
        self.form.addRow("Độ hiển thị", opacity_row)
        self.form.addRow("Giao diện", self.theme)

        shortcut_title = QLabel("Phím tắt toàn cục")
        shortcut_title.setStyleSheet("font-size: 15px; font-weight: 700; margin-top: 8px;")
        self.shortcut_form = QFormLayout()
        self.shortcut_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.hotkey_edits: dict[int, HotkeyEdit] = {}
        for hotkey_id, (label, _) in HOTKEYS.items():
            edit = HotkeyEdit(hotkey_text(settings, hotkey_id))
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
            "Tự động lưu. OpenAI-compatible profiles, Gemini API keys và phiên Codex "
            "được mã hóa bằng Windows DPAPI cho tài khoản Windows hiện tại."
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
        self.base_url.currentIndexChanged.connect(self.select_openai_profile)
        self.base_url.editTextChanged.connect(self.update_openai_profile_actions)
        self.base_url.editTextChanged.connect(self.schedule_auto_save)
        self.api_key.textChanged.connect(self.schedule_auto_save)
        self.gemini_web2api.toggled.connect(self.sync_active_openai_profile_models)
        self.gemini_web2api.toggled.connect(self.schedule_auto_save)
        self.provider.currentIndexChanged.connect(self.change_provider)
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
        self.theme.currentIndexChanged.connect(self.schedule_auto_save)
        for edit in self.hotkey_edits.values():
            edit.textChanged.connect(self.schedule_auto_save)

        self.load_provider_fields(self.current_provider)
        self.loading_provider = False
        self.update_provider_visibility()
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
        direction = (
            QHBoxLayout.Direction.TopToBottom
            if available_width < 390
            else QHBoxLayout.Direction.LeftToRight
        )
        self.base_url_layout.setDirection(direction)
        self.model_layout.setDirection(direction)

    def provider_default_model(self, provider: str) -> str:
        presets = PROVIDER_MODELS.get(provider, [])
        return presets[0] if presets else "gpt-4o-mini" if provider == "openai" else ""

    def gemini_key_tab_count(self) -> int:
        return self.gemini_key_tabs.count() - 1

    def gemini_tab_clicked(self, index: int) -> None:
        if index == self.gemini_key_tab_count():
            self.add_gemini_key_tab(focus=True)

    def add_gemini_key_tab(self, value: str = "", focus: bool = False) -> None:
        index = self.gemini_key_tab_count()
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(4, 6, 4, 4)
        edit = QLineEdit(value)
        edit.setEchoMode(QLineEdit.EchoMode.Password)
        edit.setPlaceholderText("Nhập một Gemini API key")
        edit.setAccessibleName(f"Gemini API key {index + 1}")
        edit.textChanged.connect(self.schedule_auto_save)
        layout.addWidget(edit)
        self.gemini_key_tabs.insertTab(index, page, str(index + 1))
        self.gemini_key_tabs.setCurrentIndex(index)
        if focus:
            edit.setFocus()

    def remove_gemini_key_tab(self, index: int) -> None:
        key_count = self.gemini_key_tab_count()
        if index < 0 or index >= key_count:
            return
        if key_count == 1:
            edit = self.gemini_key_tabs.widget(0).findChild(QLineEdit)
            if edit is not None:
                edit.clear()
            return
        page = self.gemini_key_tabs.widget(index)
        self.gemini_key_tabs.removeTab(index)
        page.deleteLater()
        for tab_index in range(self.gemini_key_tab_count()):
            self.gemini_key_tabs.setTabText(tab_index, str(tab_index + 1))
            edit = self.gemini_key_tabs.widget(tab_index).findChild(QLineEdit)
            if edit is not None:
                edit.setAccessibleName(f"Gemini API key {tab_index + 1}")
        self.schedule_auto_save()

    def gemini_keys(self) -> list[str]:
        return normalize_gemini_keys(
            edit.text()
            for index in range(self.gemini_key_tab_count())
            if (edit := self.gemini_key_tabs.widget(index).findChild(QLineEdit)) is not None
        )

    def set_gemini_keys(self, keys) -> None:
        while self.gemini_key_tab_count():
            page = self.gemini_key_tabs.widget(0)
            self.gemini_key_tabs.removeTab(0)
            page.deleteLater()
        for key in normalize_gemini_keys(keys) or [""]:
            self.add_gemini_key_tab(key)
        self.gemini_key_tabs.setCurrentIndex(0)

    def base_url_text(self) -> str:
        return self.base_url.currentText().strip()

    def refresh_openai_profiles(self, profiles, current_url: str = "") -> None:
        self.openai_profiles = normalize_openai_profiles(profiles)
        current_url = current_url.strip().rstrip("/")
        self.base_url.blockSignals(True)
        self.base_url.clear()
        for profile in self.openai_profiles:
            self.base_url.addItem(profile["base_url"], profile)
        index = self.base_url.findText(current_url)
        self.base_url.setCurrentIndex(index)
        if index < 0:
            self.base_url.setEditText(current_url)
        self.base_url.blockSignals(False)
        self.update_openai_profile_actions()

    def update_openai_profile_actions(self, *_args) -> None:
        base_url = self.base_url_text().rstrip("/")
        profile = next(
            (profile for profile in self.openai_profiles if profile["base_url"] == base_url),
            None,
        )
        saved = profile is not None
        enabled = self.current_provider == "openai" and self.test_worker is None
        self.base_url_save.setVisible(not saved)
        self.base_url_save.setEnabled(enabled and bool(base_url) and not saved)
        self.base_url_delete.setVisible(saved)
        self.base_url_delete.setEnabled(enabled and saved)
        self.gemini_web2api.blockSignals(True)
        self.gemini_web2api.setChecked(bool(profile and profile["gemini_web2api"]))
        self.gemini_web2api.blockSignals(False)

    def set_model_choices(self, models, current_model: str) -> None:
        choices = list(
            dict.fromkeys(
                [str(item).strip() for item in models if str(item).strip()]
                + ([current_model.strip()] if current_model.strip() else [])
            )
        )[:20]
        self.model.blockSignals(True)
        self.model.clear()
        self.model.addItems(choices)
        self.model.setCurrentText(current_model.strip())
        self.model.blockSignals(False)

    def sync_active_openai_profile_models(self) -> None:
        if self.loading_provider or self.current_provider != "openai":
            return
        base_url = self.base_url_text().rstrip("/")
        model = self.model.currentText().strip()
        models = list(dict.fromkeys(self.saved_models() + ([model] if model else [])))[:20]
        changed = False
        profiles = []
        for profile in self.openai_profiles:
            if profile["base_url"] == base_url:
                profile = dict(profile)
                profile["model"] = model
                profile["models"] = models
                profile["api_key"] = self.api_key.text().strip()
                profile["gemini_web2api"] = self.gemini_web2api.isChecked()
                changed = True
            profiles.append(profile)
        if changed:
            save_openai_profiles(self.settings, profiles)
            self.openai_profiles = normalize_openai_profiles(profiles)
            index = self.base_url.findText(base_url)
            if index >= 0:
                active = next(
                    profile for profile in self.openai_profiles if profile["base_url"] == base_url
                )
                self.base_url.setItemData(index, active)

    def select_openai_profile(self, index: int) -> None:
        if self.loading_provider or self.current_provider != "openai" or index < 0:
            return
        profile = self.base_url.itemData(index)
        if not isinstance(profile, dict):
            return
        self.loading_provider = True
        self.api_key.setText(profile["api_key"])
        self.gemini_web2api.setChecked(profile["gemini_web2api"])
        self.set_model_choices(profile["models"], profile["model"])
        self.loading_provider = False
        self.settings.setValue("openai/base_url", profile["base_url"])
        self.settings.setValue("openai/model", profile["model"])
        self.settings.setValue("openai/models", profile["models"])
        self.settings.setValue("openai/key", protect_secret(profile["api_key"]))
        self.settings.sync()
        self.set_model_test_status("Chưa test model")
        self.update_model_action()
        self.update_openai_profile_actions()

    def save_openai_profile(self) -> None:
        base_url = self.base_url_text().rstrip("/")
        model = self.model.currentText().strip()
        try:
            chat_endpoint(base_url)
            if not model:
                raise ValueError("Model không được để trống.")
            models = list(dict.fromkeys(self.saved_models() + [model]))[:20]
            profile = {
                "base_url": base_url,
                "model": model,
                "models": models,
                "api_key": self.api_key.text().strip(),
                "gemini_web2api": self.gemini_web2api.isChecked(),
            }
            profiles = [
                saved for saved in self.openai_profiles if saved["base_url"] != base_url
            ] + [profile]
            save_openai_profiles(self.settings, profiles)
            self.settings.setValue("openai/base_url", base_url)
            self.settings.setValue("openai/model", model)
            self.settings.setValue("openai/models", models)
            self.settings.setValue("openai/key", protect_secret(profile["api_key"]))
            self.settings.sync()
            self.refresh_openai_profiles(profiles, base_url)
        except Exception as error:
            QMessageBox.warning(self, "OpenAI-compatible profile", str(error))

    def delete_openai_profile(self) -> None:
        base_url = self.base_url_text().rstrip("/")
        profiles = [
            profile for profile in self.openai_profiles if profile["base_url"] != base_url
        ]
        if len(profiles) == len(self.openai_profiles):
            return
        model = self.model.currentText()
        api_key = self.api_key.text()
        save_openai_profiles(self.settings, profiles)
        self.settings.sync()
        self.refresh_openai_profiles(profiles, base_url)
        self.model.setCurrentText(model)
        self.api_key.setText(api_key)

    def load_provider_fields(self, provider: str) -> None:
        self.loading_provider = True
        current_url = self.settings.value(
            "openai/base_url", "https://api.openai.com/v1", str
        ).strip()
        try:
            profiles = load_openai_profiles(self.settings)
        except Exception:
            profiles = []
        self.refresh_openai_profiles(profiles, current_url)
        model_history = self.settings.value(f"{provider}/models", [])
        if isinstance(model_history, str):
            model_history = [model_history]
        current_model = self.settings.value(
            f"{provider}/model", self.provider_default_model(provider), str
        ).strip()
        if provider == "openai":
            active_profile = next(
                (profile for profile in profiles if profile["base_url"] == current_url.rstrip("/")),
                None,
            )
            if active_profile is not None:
                model_history = active_profile["models"]
                current_model = active_profile["model"]
                self.gemini_web2api.setChecked(active_profile["gemini_web2api"])
            else:
                self.gemini_web2api.setChecked(False)
        self.set_model_choices(model_history, current_model)
        self.set_model_test_status("Chưa test model")
        self.api_key.clear()
        self.api_key.setPlaceholderText("")
        if provider == "openai":
            try:
                self.api_key.setText(unprotect_secret(self.settings.value("openai/key", "", str)))
            except Exception:
                self.api_key.setPlaceholderText("Không đọc được key đã lưu; nhập lại")
        elif provider == "gemini":
            try:
                self.set_gemini_keys(load_gemini_keys(self.settings))
            except Exception:
                self.set_gemini_keys([])
                edit = self.gemini_key_tabs.widget(0).findChild(QLineEdit)
                if edit is not None:
                    edit.setPlaceholderText("Không đọc được danh sách key; nhập lại")
        self.loading_provider = False
        self.update_model_action()
        self.update_codex_status()

    def persist_provider_fields(self, provider: str, errors: list[str]) -> None:
        if provider == "openai":
            try:
                base_url = self.base_url_text()
                chat_endpoint(base_url)
                self.settings.setValue("openai/base_url", base_url)
            except Exception as error:
                errors.append(str(error))
        model = self.model.currentText().strip()
        if model:
            self.settings.setValue(f"{provider}/model", model)
        else:
            errors.append("Model không được để trống.")
        self.settings.setValue(f"{provider}/models", list(dict.fromkeys(self.saved_models()))[:20])
        try:
            if provider == "openai":
                self.settings.setValue("openai/key", protect_secret(self.api_key.text().strip()))
                self.sync_active_openai_profile_models()
            elif provider == "gemini":
                save_gemini_keys(self.settings, self.gemini_keys())
                self.settings.remove("gemini/key")
        except Exception as error:
            errors.append(str(error))

    def change_provider(self, _index: int) -> None:
        if self.loading_provider:
            return
        errors: list[str] = []
        self.persist_provider_fields(self.current_provider, errors)
        self.current_provider = self.provider.currentData()
        self.settings.setValue("provider/current", self.current_provider)
        self.load_provider_fields(self.current_provider)
        self.update_provider_visibility()
        self.settings.sync()

    def update_provider_visibility(self) -> None:
        provider = self.current_provider
        for widget in (self.base_url_row, self.form.labelForField(self.base_url_row)):
            if widget is not None:
                widget.setVisible(provider == "openai")
        for widget in (
            self.api_key,
            self.form.labelForField(self.api_key),
            self.gemini_web2api,
            self.form.labelForField(self.gemini_web2api),
        ):
            if widget is not None:
                widget.setVisible(provider == "openai")
        for widget in (self.gemini_key_tabs, self.form.labelForField(self.gemini_key_tabs)):
            if widget is not None:
                widget.setVisible(provider == "gemini")
        for widget in (
            self.codex_status,
            self.form.labelForField(self.codex_status),
            self.codex_action,
            self.form.labelForField(self.codex_action),
        ):
            if widget is not None:
                widget.setVisible(provider == "codex")

    def update_codex_status(self) -> None:
        try:
            bundle = load_codex_bundle(self.settings)
        except Exception:
            bundle = {}
        identity = bundle.get("email") or bundle.get("account_id")
        self.codex_logged_in = bool(identity)
        self.codex_status.setText(f"Đã đăng nhập: {identity}" if identity else "Chưa đăng nhập")
        self.codex_action.setText("Đăng xuất" if identity else "Đăng nhập")
        self.codex_action.setEnabled(self.oauth_worker is None)

    def toggle_codex_session(self) -> None:
        if self.codex_logged_in:
            self.logout_codex()
        else:
            self.start_codex_login()

    def start_codex_login(self) -> None:
        if self.oauth_worker is not None:
            return
        self.oauth_worker = CodexOAuthWorker()
        self.oauth_worker.succeeded.connect(self.codex_login_succeeded)
        self.oauth_worker.failed.connect(self.codex_login_failed)
        self.oauth_worker.finished.connect(self.oauth_worker_finished)
        self.codex_status.setText("Đang chờ đăng nhập trong trình duyệt…")
        self.codex_action.setText("Đang đăng nhập…")
        self.codex_action.setEnabled(False)
        self.oauth_worker.start()

    def codex_login_succeeded(self, bundle: dict) -> None:
        identity = bundle.get("email") or bundle.get("account_id")
        self.codex_status.setText(f"Đã đăng nhập: {identity}")

    def codex_login_failed(self, message: str) -> None:
        self.codex_status.setText("Đăng nhập thất bại")
        QMessageBox.warning(self, "Codex OAuth", message)

    def oauth_worker_finished(self) -> None:
        if self.oauth_worker is not None:
            self.oauth_worker.deleteLater()
        self.oauth_worker = None
        self.update_codex_status()

    def logout_codex(self) -> None:
        self.settings.remove("codex/token_bundle")
        self.settings.sync()
        self.update_codex_status()

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
        self.model_action.setEnabled(bool(model) and self.test_worker is None)
        if self.test_worker is None:
            self.model_test.setText("Test")
            self.model_test.setEnabled(bool(model))

    def select_saved_model(self, index: int) -> None:
        if index < 0:
            return
        model = self.model.itemText(index).strip()
        if model:
            self.settings.setValue(f"{self.current_provider}/model", model)
            self.sync_active_openai_profile_models()
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
        self.settings.setValue(f"{self.current_provider}/models", self.saved_models()[:20])
        self.settings.setValue(f"{self.current_provider}/model", self.model.currentText().strip())
        self.sync_active_openai_profile_models()
        self.settings.sync()
        self.update_model_action()

    def set_model_test_status(self, text: str, style: str = "") -> None:
        self.model_test_animation.stop()
        self.model_test_effect.setOpacity(1.0)
        self.model_test_status.setStyleSheet(style)
        self.model_test_status.setText(text)

    def model_changed(self, _text: str) -> None:
        if not self.loading_provider and self.test_worker is None:
            self.set_model_test_status("Chưa test model")

    def test_current_model(self) -> None:
        if self.test_worker is not None:
            self.test_worker.cancel()
            self.model_test.setEnabled(False)
            self.set_model_test_status("Đã hủy test")
            return
        errors: list[str] = []
        self.persist_provider_fields(self.current_provider, errors)
        if errors:
            self.set_model_test_status("Không thể test: " + " ".join(errors))
            return
        provider = self.current_provider
        model = self.model.currentText().strip()
        try:
            if provider == "openai":
                config = {
                    "endpoint": chat_endpoint(self.base_url_text()),
                    "api_key": self.api_key.text().strip(),
                }
            elif provider == "gemini":
                keys = self.gemini_keys()
                if not keys:
                    raise ValueError("Chưa cấu hình Gemini API key.")
                config = {"api_keys": keys}
            elif provider == "codex":
                bundle = load_codex_bundle(self.settings)
                if not bundle.get("access_token") or not bundle.get("account_id"):
                    raise ValueError("Chưa đăng nhập Codex.")
                config = {"token_bundle": bundle}
            else:
                raise ValueError(f"Provider không hợp lệ: {provider}")
        except Exception as error:
            self.set_model_test_status(f"Không thể test: {error}")
            return
        messages = [{"role": "user", "content": "Reply with exactly: OK"}]
        self.test_worker = ChatWorker(provider, model, messages, config)
        self.test_worker.succeeded.connect(self.model_test_succeeded)
        self.test_worker.failed.connect(self.model_test_failed)
        self.test_worker.finished.connect(self.model_test_finished)
        self.set_model_test_status(f"Đang test {model}…")
        self.provider.setEnabled(False)
        self.base_url.setEnabled(False)
        self.api_key.setEnabled(False)
        self.model.setEnabled(False)
        self.model_test.setText("Hủy test")
        self.model_test.setEnabled(True)
        self.model_action.setEnabled(False)
        self.update_openai_profile_actions()
        self.test_worker.start()

    def model_test_succeeded(self, _text: str) -> None:
        self.set_model_test_status(
            f"✓ Hoạt động: {self.model.currentText().strip()}",
            "color: #55d68b; font-weight: 700;",
        )
        self.model_test_effect.setOpacity(0.0)
        self.model_test_animation.start()

    def model_test_failed(self, message: str) -> None:
        self.set_model_test_status(
            f"Thất bại: {message}", "color: #ff8d9e;"
        )

    def model_test_finished(self) -> None:
        if self.test_worker is not None:
            self.test_worker.deleteLater()
        self.test_worker = None
        self.provider.setEnabled(True)
        self.base_url.setEnabled(True)
        self.api_key.setEnabled(True)
        self.model.setEnabled(True)
        self.update_model_action()
        self.update_openai_profile_actions()

    def change_opacity(self, value: int) -> None:
        self.opacity_value.setText(f"{value}%")
        self.settings.setValue("window/opacity", value / 100)
        if self.overlay is not None:
            self.overlay.set_opacity_percent(value, update_panel=False)

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
            QLineEdit, QPlainTextEdit, QComboBox {{
                background: {field}; border: 1px solid {border}; border-radius: 7px; padding: 6px;
            }}
            QComboBox QAbstractItemView {{ background: {field}; color: {text}; selection-background-color: {border}; }}
            QTabWidget::pane {{ background: transparent; border: 1px solid {border}; border-radius: 7px; }}
            QTabBar::tab {{ background: {field}; border: 1px solid {border}; min-width: 18px; padding: 3px 7px; }}
            QTabBar::tab:first {{ border-top-left-radius: 6px; }}
            QTabBar::tab:last {{ border-top-right-radius: 6px; font-weight: 700; }}
            QTabBar::tab:selected {{ background: {border}; }}
            QTabBar::close-button {{ subcontrol-position: right; }}
            QCheckBox {{ spacing: 7px; }}
            QPushButton {{ background: {field}; border: 1px solid {border}; border-radius: 7px; padding: 7px 12px; }}
            QPushButton:hover {{ background: {border}; }}
            QLabel {{ color: {text}; }}
            """
        )

    def schedule_auto_save(self, *_args) -> None:
        if not self.loading_provider:
            self.autosave_timer.start()

    def choose_image_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            "Chọn folder lưu ảnh đã gửi",
            self.image_folder.text().strip() or os.path.expandvars("%USERPROFILE%\\Pictures"),
        )
        if folder:
            self.image_folder.setText(os.path.normpath(folder))
            self.image_save_toggle.setChecked(True)
            self.update_image_folder_buttons()
            self.schedule_auto_save()

    def open_image_folder(self) -> None:
        folder = self.image_folder.text().strip()
        if not os.path.isdir(folder):
            QMessageBox.warning(self, "Folder lưu ảnh", "Folder đã chọn không còn tồn tại.")
            return
        os.startfile(folder)

    def image_save_toggled(self, _enabled: bool) -> None:
        self.update_image_folder_buttons()
        self.schedule_auto_save()

    def update_image_folder_buttons(self) -> None:
        configured = bool(self.image_folder.text().strip())
        if not configured and self.image_save_toggle.isChecked():
            self.image_save_toggle.setChecked(False)
        self.open_image_folder_button.setEnabled(configured)
        self.image_save_toggle.setEnabled(configured)
        self.image_folder.setEnabled(configured and self.image_save_toggle.isChecked())

    def change_resize_mode(self, allow_tiny: bool) -> None:
        self.settings.setValue("window/allow_tiny_resize", allow_tiny)
        if self.overlay is not None:
            self.overlay.apply_size_settings(reset_to_default=not allow_tiny)
        self.schedule_auto_save()

    def save_settings(self, show_errors: bool = False) -> bool:
        errors: list[str] = []
        self.current_provider = self.provider.currentData()
        self.settings.setValue("provider/current", self.current_provider)
        self.persist_provider_fields(self.current_provider, errors)
        self.settings.setValue("capture/image_prompt", self.image_prompt.toPlainText().strip())
        self.settings.setValue("capture/save_folder", self.image_folder.text().strip())
        self.settings.setValue(
            "capture/save_enabled",
            self.image_save_toggle.isChecked() and bool(self.image_folder.text().strip()),
        )
        self.settings.setValue("window/always_on_top", self.always_on_top.isChecked())
        self.settings.setValue("window/keep_on_top", self.keep_on_top.isChecked())
        self.settings.setValue("capture/hide_overlay", self.hide_during_capture.isChecked())
        self.settings.setValue("capture/show_selection_frame", self.show_selection_frame.isChecked())
        self.settings.setValue("window/show_title", self.show_title.isChecked())
        self.settings.setValue("chat/auto_scroll", self.auto_scroll.isChecked())
        self.settings.setValue("window/allow_tiny_resize", self.allow_tiny_resize.isChecked())
        self.settings.setValue("window/opacity", self.opacity.value() / 100)
        self.settings.setValue("window/theme", self.theme.currentData())

        try:
            hotkeys = []
            identities = []
            for edit in self.hotkey_edits.values():
                text = edit.hotkeyText()
                mouse_parts = mouse_hotkey_parts(text)
                if mouse_parts is None:
                    modifiers, virtual_key = hotkey_to_win(text, allow_repeat=True)
                    identity = ("keyboard", modifiers, virtual_key)
                else:
                    identity = ("mouse", *mouse_parts)
                hotkeys.append(text)
                identities.append(identity)
            if len(set(identities)) != len(identities):
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
            self.overlay.set_opacity_percent(self.opacity.value(), update_panel=False)
        if show_errors and errors:
            QMessageBox.warning(self, "Một số cài đặt chưa hợp lệ", "\n".join(errors))
        return not errors

    def close_with_save(self) -> None:
        if (
            (self.oauth_worker is not None and self.oauth_worker.isRunning())
            or (self.test_worker is not None and self.test_worker.isRunning())
        ):
            QMessageBox.information(
                self, "Tác vụ đang chạy", "Hãy chờ đăng nhập hoặc test model hoàn tất trước khi đóng Cài đặt."
            )
            return
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
        self.session_worker: ConversationCreateWorker | None = None
        self.mouse_hotkey_hook: MouseHotkeyHook | None = None
        self.messages: list[dict] = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
        self.click_through = False
        self.exiting = False
        self.was_visible_before_capture = True
        self.selector: SelectionOverlay | None = None
        self.pending_image: bytes | None = None
        self.hotkey_failures: list[str] = []
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

    def nativeEvent(self, event_type, message):  # noqa: N802 - Qt API
        try:
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_NCHITTEST and int(msg.hWnd) == int(self.winId()) and not self.click_through:
                rect = wintypes.RECT()
                if ctypes.windll.user32.GetWindowRect(int(self.winId()), ctypes.byref(rect)):
                    lparam = int(msg.lParam)
                    x = ctypes.c_short(lparam & 0xFFFF).value
                    y = ctypes.c_short((lparam >> 16) & 0xFFFF).value
                    border = max(6, round(8 * self.devicePixelRatioF()))
                    hit = resize_hit_test(x, y, (rect.left, rect.top, rect.right, rect.bottom), border)
                    if hit:
                        return True, hit
        except (TypeError, ValueError, OverflowError):
            pass
        return super().nativeEvent(event_type, message)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.settings.setValue("window/size", self.size())
        if hasattr(self, "compact_settings_button"):
            self.compact_settings_button.move(self.width() - 34, 8)
            self.compact_settings_button.raise_()
        if hasattr(self, "chat"):
            QTimer.singleShot(0, self.update_chat_message_widths)

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

    def set_opacity_percent(self, percent: int, update_panel: bool = True) -> None:
        percent = min(100, max(5, int(percent)))
        self.setWindowOpacity(percent / 100)
        self.settings.setValue("window/opacity", percent / 100)
        if update_panel and self.settings_panel is not None:
            self.settings_panel.opacity.blockSignals(True)
            self.settings_panel.opacity.setValue(percent)
            self.settings_panel.opacity.blockSignals(False)
            self.settings_panel.opacity_value.setText(f"{percent}%")

    def adjust_opacity(self, delta: float) -> None:
        percent = round(self.windowOpacity() * 100) + round(delta * 100)
        self.set_opacity_percent(percent)
        self.status.setText(f"Độ hiển thị: {min(100, max(5, percent))}%")

    def eventFilter(self, watched, event) -> bool:
        if (
            hasattr(self, "chat")
            and watched is self.chat.viewport()
            and event.type() == QEvent.Type.Resize
        ):
            QTimer.singleShot(0, self.update_chat_message_widths)
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

    def close_settings(self, accepted: bool) -> bool:
        if self.settings_panel is not None and (
            (
                self.settings_panel.oauth_worker is not None
                and self.settings_panel.oauth_worker.isRunning()
            )
            or (
                self.settings_panel.test_worker is not None
                and self.settings_panel.test_worker.isRunning()
            )
        ):
            self.status.setText("Hãy hủy hoặc chờ đăng nhập/test model hoàn tất trước khi chụp")
            return False
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
        if self.mouse_hotkey_hook is not None:
            self.hotkey_failures.extend(self.mouse_hotkey_hook.update_bindings(self.settings))
        self.status.setText(
            ("Đã tự động lưu" if accepted else "Sẵn sàng")
            if not self.hotkey_failures
            else "Phím tắt lỗi: " + ", ".join(self.hotkey_failures)
        )
        self.settings_panel = None
        return True

    def update_chat_message_widths(self) -> None:
        viewport_width = self.chat.viewport().width()
        for message in self.chat_content.findChildren(QLabel):
            role = message.property("chatRole")
            if role not in ("user", "assistant", "error"):
                continue
            ratio = 0.72 if role in ("user", "error") else 1.0
            message.setMaximumWidth(max(80, int(viewport_width * ratio) - 20))

    def append_bubble(self, role: str, text: str, image: bytes | None = None) -> None:
        row = QWidget()
        row.installEventFilter(self)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(2, 0, 2, 0)
        bubble = QFrame()
        bubble.setObjectName(
            "userBubble" if role == "user" else "assistantMessage" if role == "assistant" else "errorBubble"
        )
        bubble.setSizePolicy(
            QSizePolicy.Policy.Expanding if role == "assistant" else QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Preferred,
        )
        content_layout = QVBoxLayout(bubble)
        content_layout.setContentsMargins(10 if role != "assistant" else 2, 7, 10 if role != "assistant" else 2, 7)
        content_layout.setSpacing(5)
        message = QLabel(text if role != "error" else f"Lỗi\n{text}")
        message.setProperty("chatRole", role)
        if role == "assistant":
            message.setTextFormat(Qt.TextFormat.MarkdownText)
            message.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        message.setWordWrap(True)
        message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        ratio = 0.72 if role in ("user", "error") else 1.0
        message.setMaximumWidth(max(80, int(self.chat.viewport().width() * ratio) - 20))
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
        elif role == "assistant":
            row_layout.addWidget(bubble, 1)
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
        if self.session_worker is not None:
            self.status.setText("Đang tạo session Gemini Web2API mới")
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
            provider = self.settings.value("provider/current", "openai", str)
            presets = PROVIDER_MODELS.get(provider, [])
            default_model = presets[0] if presets else "gpt-4o-mini" if provider == "openai" else ""
            model = self.settings.value(f"{provider}/model", default_model, str).strip()
            if not model:
                raise ValueError("Chưa cấu hình model.")
            if provider == "openai":
                config = {
                    "endpoint": chat_endpoint(
                        self.settings.value("openai/base_url", "https://api.openai.com/v1", str)
                    ),
                    "api_key": unprotect_secret(self.settings.value("openai/key", "", str)),
                }
            elif provider == "gemini":
                keys = load_gemini_keys(self.settings)
                if not keys:
                    raise ValueError("Chưa cấu hình Gemini API key.")
                config = {"api_keys": keys}
            elif provider == "codex":
                token_bundle = load_codex_bundle(self.settings)
                if not token_bundle.get("access_token") or not token_bundle.get("account_id"):
                    raise ValueError("Chưa đăng nhập Codex. Mở Cài đặt để đăng nhập bằng ChatGPT.")
                config = {"token_bundle": token_bundle}
            else:
                raise ValueError(f"Provider không hợp lệ: {provider}")
        except Exception as error:
            self.append_bubble("error", str(error))
            if not self.settings_scroll.isVisible():
                self.open_settings()
            return

        save_error = ""
        saved_path = ""
        if image:
            folder = self.settings.value("capture/save_folder", "", str).strip()
            if folder and self.settings.value("capture/save_enabled", bool(folder), bool):
                try:
                    saved_path = save_chat_image(folder, image)
                except Exception as error:
                    save_error = str(error)
                    LOGGER.warning("image save failed type=%s", type(error).__name__)

        self.input.clear()
        self.clear_pending_image()
        self.append_bubble("user", question or image_prompt or "Ảnh đính kèm", image)
        if save_error:
            self.append_bubble("error", "Không lưu được bản sao ảnh: " + save_error)
        if image:
            encoded = base64.b64encode(image).decode("ascii")
            content = [
                {"type": "text", "text": text},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded}"}},
            ]
        else:
            content = text
        self.messages.append({"role": "user", "content": content})
        self.status.setText("AI đang trả lời…" + (f" • đã lưu {os.path.basename(saved_path)}" if saved_path else ""))
        self.worker = ChatWorker(provider, model, list(self.messages), config)
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

    @staticmethod
    def grab_virtual_rect(rect: QRect) -> QPixmap:
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

    def reset_local_session(self) -> None:
        self.messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
        self.clear_pending_image()
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.chat_layout.activate()
        self.status.setText("Đã tạo session mới")

    def new_session(self) -> None:
        if self.worker and self.worker.isRunning():
            self.status.setText("Đang chờ AI trả lời; chưa thể tạo session mới")
            return
        if self.session_worker is not None:
            self.status.setText("Đang tạo session Gemini Web2API mới")
            return
        provider = self.settings.value("provider/current", "openai", str)
        if provider != "openai":
            self.reset_local_session()
            return
        base_url = self.settings.value("openai/base_url", "", str).strip().rstrip("/")
        try:
            profiles = load_openai_profiles(self.settings)
            profile = next(
                (profile for profile in profiles if profile["base_url"] == base_url),
                None,
            )
            if profile is None or not profile["gemini_web2api"]:
                self.reset_local_session()
                return
            endpoint = conversations_endpoint(base_url)
            api_key = profile["api_key"]
        except Exception as error:
            self.status.setText("Không thể tạo session mới: " + str(error))
            return
        self.status.setText("Đang tạo session Gemini Web2API mới…")
        self.session_worker = ConversationCreateWorker(endpoint, api_key)
        self.session_worker.succeeded.connect(self.remote_session_created)
        self.session_worker.failed.connect(self.remote_session_failed)
        self.session_worker.finished.connect(self.remote_session_finished)
        self.session_worker.start()

    def remote_session_created(self) -> None:
        self.reset_local_session()

    def remote_session_failed(self, message: str) -> None:
        self.status.setText("Không tạo được session mới: " + message)

    def remote_session_finished(self) -> None:
        if self.session_worker is not None:
            self.session_worker.deleteLater()
        self.session_worker = None

    def start_capture_from_hotkey(self) -> None:
        if self.settings_scroll.isVisible() and not self.close_settings(False):
            return
        self.start_capture()

    def handle_hotkey(self, hotkey_id: int) -> None:
        if self.settings_scroll.isVisible() and hotkey_id == 6:
            self.status.setText("Gửi nội dung chỉ dùng trong Chat")
            return
        actions = {
            1: self.toggle_click_through,
            2: self.toggle_visible,
            3: lambda: self.adjust_opacity(-0.05),
            4: lambda: self.adjust_opacity(0.05),
            5: self.start_capture_from_hotkey,
            6: self.submit,
            7: self.open_settings,
            8: self.new_session,
        }
        action = actions.get(hotkey_id)
        if action:
            action()

    def quit_app(self) -> None:
        self.exiting = True
        self.tray.hide()
        QApplication.quit()


def register_hotkeys(settings: QSettings) -> list[str]:
    unregister_hotkeys()
    failures = []
    user32 = ctypes.windll.user32
    for hotkey_id, (label, _) in HOTKEYS.items():
        text = hotkey_text(settings, hotkey_id)
        try:
            if mouse_hotkey_parts(text) is not None:
                continue
            modifiers, virtual_key = hotkey_to_win(text, allow_repeat=hotkey_id in (3, 4))
            if not user32.RegisterHotKey(None, hotkey_id, modifiers, virtual_key):
                failures.append(f"{label} ({text})")
        except ValueError:
            failures.append(f"{label} ({text})")
    return failures


def unregister_hotkeys() -> None:
    for hotkey_id in HOTKEYS:
        ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)


def self_check() -> None:
    modifiers, _ = hotkey_to_win("Ctrl+[", allow_repeat=True)
    assert modifiers & MOD_CONTROL and not modifiers & MOD_NOREPEAT
    modifiers, _ = hotkey_to_win("Ctrl+M")
    assert modifiers & MOD_NOREPEAT
    assert resize_hit_test(1, 1, (0, 0, 100, 100), 8) == HTTOPLEFT
    assert resize_hit_test(99, 50, (0, 0, 100, 100), 8) == HTRIGHT
    assert resize_hit_test(50, 50, (0, 0, 100, 100), 8) == 0
    with tempfile.TemporaryDirectory() as folder:
        first = save_chat_image(folder, b"png-one", "20260101_000000_000")
        second = save_chat_image(folder, b"png-two", "20260101_000000_000")
        assert first.endswith("OverlayAI_20260101_000000_000.png")
        assert second.endswith("OverlayAI_20260101_000000_000_1.png")
        with open(first, "rb") as saved:
            assert saved.read() == b"png-one"
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
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    assert pkce_challenge(verifier) == "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
    auth_query = urllib.parse.parse_qs(urllib.parse.urlparse(codex_authorization_url("s", "c")).query)
    assert auth_query["state"] == ["s"] and auth_query["code_challenge"] == ["c"]
    assert oauth_callback_code("/auth/callback?state=s&code=code", "s") == "code"
    try:
        oauth_callback_code("/auth/callback?state=wrong&code=code", "s")
        raise AssertionError("state mismatch was accepted")
    except ValueError:
        pass
    fake_claims = base64url(json.dumps({"email": "a@example.test", "chatgpt_account_id": "acc"}).encode())
    assert token_identity(f"x.{fake_claims}.y") == ("acc", "a@example.test")
    redacted = safe_response_log(
        'Bearer bearer-secret {"access_token":"token-secret","account_id":"account-secret",'
        '"id_token":"eyJh.eyJi.YyJ9"}'
    )
    assert "bearer-secret" not in redacted
    assert "token-secret" not in redacted and "account-secret" not in redacted and "eyJh" not in redacted
    messages = [
        {"role": "system", "content": "system"},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "question"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,AA=="}},
            ],
        },
        {"role": "assistant", "content": "answer"},
    ]
    codex = codex_payload("model", messages)
    assert codex["instructions"] == "system" and codex["input"][0]["content"][1]["type"] == "input_image"
    gemini = gemini_payload(messages)
    assert gemini["systemInstruction"]["parts"][0]["text"] == "system"
    assert gemini["contents"][0]["parts"][1]["inlineData"]["data"] == "AA=="
    assert gemini_text({"candidates": [{"content": {"parts": [{"text": "gemini"}]}}]}) == "gemini"
    sse = 'event: response.output_text.delta\ndata: {"type":"response.output_text.delta","delta":"hel"}\n\n' \
        'data: {"type":"response.output_text.delta","delta":"lo"}\n\n'
    assert codex_sse_text(sse) == ("hello", True)
    assert codex_sse_text('{"output_text":"json fallback"}') == ("json fallback", False)
    assert mouse_hotkey_parts("Mouse4") == (0, "Mouse4")
    assert mouse_hotkey_parts("Ctrl+Mouse4") == (MOD_CONTROL, "Mouse4")
    assert mouse_hotkey_parts("Alt+Shift+Mouse5") == (MOD_ALT | MOD_SHIFT, "Mouse5")
    for invalid_mouse_hotkey in ("Ctrl+Ctrl+Mouse4", "Foo+Mouse5"):
        try:
            mouse_hotkey_parts(invalid_mouse_hotkey)
            raise AssertionError(f"invalid mouse hotkey was accepted: {invalid_mouse_hotkey}")
        except ValueError:
            pass
    assert len(PROVIDER_MODELS["gemini"]) == 8 and PROVIDER_MODELS["gemini"][0] == "gemini-3.7-flash"
    assert "gemini-3.5-flash" in PROVIDER_MODELS["gemini"]
    assert not any(model.startswith("gemini-2.5-") for model in PROVIDER_MODELS["gemini"])
    assert normalize_gemini_keys([" key-1 ", "", "key-2", "key-1"]) == ["key-1", "key-2"]
    assert conversations_endpoint("http://localhost:8081/v1/") == (
        "http://localhost:8081/v1/conversations"
    )
    assert conversations_endpoint("http://localhost:8081/v1/chat/completions") == (
        "http://localhost:8081/v1/conversations"
    )
    assert normalize_openai_profiles(
        [
            {"base_url": " https://one.test/v1/ ", "model": "model-one", "api_key": " key-one "},
            {"base_url": "", "model": "invalid"},
            {
                "base_url": "https://one.test/v1",
                "model": "model-two",
                "api_key": "key-two",
                "gemini_web2api": True,
            },
        ]
    ) == [
        {
            "base_url": "https://one.test/v1",
            "model": "model-two",
            "models": ["model-two"],
            "api_key": "key-two",
            "gemini_web2api": True,
        }
    ]
    rotated = rotated_gemini_keys(["key-1", "key-2", "key-3"])
    assert len(rotated) == 3 and set(rotated) == {"key-1", "key-2", "key-3"}
    assert len(PROVIDER_MODELS["codex"]) == 12 and PROVIDER_MODELS["codex"][0] == "gpt-5.6-sol"
    assert len(set(PROVIDER_MODELS["gemini"] + PROVIDER_MODELS["codex"])) == 20
    with tempfile.TemporaryDirectory() as folder:
        test_settings = QSettings(os.path.join(folder, "settings.ini"), QSettings.Format.IniFormat)
        test_settings.setValue("gemini/models", ["gemini-2.5-pro", "custom-model"])
        test_settings.setValue("gemini/model", "gemini-2.5-pro")
        test_settings.setValue("gemini/key", protect_secret("legacy-key"))
        test_settings.setValue("openai/base_url", "https://legacy.test/v1")
        test_settings.setValue("openai/model", "legacy-model")
        test_settings.setValue("openai/key", protect_secret("legacy-openai-key"))
        migrate_provider_settings(test_settings)
        migrated_models = test_settings.value("gemini/models", [])
        assert "gemini-2.5-pro" not in migrated_models and "custom-model" in migrated_models
        assert migrated_models.count("gemini-3.5-flash") == 1
        assert test_settings.value("gemini/model", "", str) == "gemini-3.7-flash"
        assert load_gemini_keys(test_settings) == ["legacy-key"]
        assert not test_settings.contains("gemini/key")
        assert load_openai_profiles(test_settings) == [
            {
                "base_url": "https://legacy.test/v1",
                "model": "legacy-model",
                "models": ["legacy-model"],
                "api_key": "legacy-openai-key",
                "gemini_web2api": False,
            }
        ]
    print("self-check: ok")


def main() -> int:
    if "--self-check" in sys.argv:
        self_check()
        return 0
    if sys.platform != "win32":
        print("Ứng dụng này chỉ hỗ trợ Windows.", file=sys.stderr)
        return 1

    enable_dpi_awareness()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setQuitOnLastWindowClosed(False)
    settings = QSettings()
    migrate_provider_settings(settings)

    window = OverlayWindow(settings)
    native_filter = HotkeyFilter(window.handle_hotkey)
    app.installNativeEventFilter(native_filter)
    mouse_hook = MouseHotkeyHook(window.handle_hotkey)
    window.mouse_hotkey_hook = mouse_hook
    failures = register_hotkeys(settings)
    failures.extend(mouse_hook.update_bindings(settings))
    window.hotkey_failures = failures
    app.aboutToQuit.connect(unregister_hotkeys)
    app.aboutToQuit.connect(mouse_hook.uninstall)

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
