# Overlay AI cho Windows

Ứng dụng overlay desktop viết bằng Python/PySide6, hỗ trợ chat văn bản và ảnh qua API OpenAI-compatible.

> **Tuyên bố sử dụng:** Dự án chỉ phục vụ mục đích học tập. Không được sử dụng trong bất kỳ trường hợp gian lận nào, bao gồm thi cử, kiểm tra và đánh giá.

## Tính năng

- Overlay trong suốt, không viền, always-on-top, click-through và khay hệ thống.
- Resize linh hoạt, điều chỉnh opacity từ `5%` đến `100%` và ba theme Đen/Xám/Trắng.
- Cài đặt nằm trong overlay, responsive và tự động lưu.
- Chụp vùng trên nhiều màn hình; ảnh được đính kèm trước khi gửi.
- Chat văn bản/ảnh qua endpoint `chat/completions` OpenAI-compatible.
- Render câu trả lời bằng Markdown và tự cuộn nội dung.
- Lưu danh sách model và mã hóa API key bằng Windows DPAPI.
- Hỗ trợ bảy phím tắt toàn cục có thể tùy chỉnh.

## Cài đặt và chạy

Yêu cầu Windows 10/11 và Python 3.11 trở lên.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
.\.venv\Scripts\python.exe .\app.py
```

Trong Cài đặt, nhập:

- Base URL, ví dụ `https://api.openai.com/v1`.
- Model hỗ trợ ảnh nếu cần gửi ảnh, ví dụ `gpt-4o-mini`.
- API key.
- Prompt dùng khi gửi ảnh.

Provider phải hỗ trợ OpenAI Chat Completions. Chức năng gửi ảnh cần provider hỗ trợ ảnh dạng data URL.

## Phím tắt mặc định

| Chức năng | Phím |
|---|---|
| Bật/tắt click-through | `Ctrl+M` |
| Ẩn/hiện cửa sổ | `Ctrl+\` |
| Giảm opacity | `Ctrl+[` |
| Tăng opacity | `Ctrl+]` |
| Bật/tắt chọn vùng | `Ctrl+E` |
| Gửi nội dung | `Ctrl+Enter` |
| Mở/đóng Cài đặt | `Ctrl+H` |

Có thể thay đổi các tổ hợp này trong Cài đặt. Mỗi tổ hợp cần ít nhất một modifier `Ctrl`, `Alt`, `Shift` hoặc `Win` và không được trùng nhau.

## Kiểm tra

```powershell
.\.venv\Scripts\python.exe .\app.py --self-check
.\.venv\Scripts\python.exe -m py_compile .\app.py
```

## Đóng gói EXE

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name OverlayAI .\app.py
```

File kết quả nằm tại `dist\OverlayAI.exe`.

## Giới hạn

Ứng dụng chỉ hoạt động trên desktop Windows thông thường và cùng mức đặc quyền. Secure desktop, UAC, nội dung DRM/protected capture hoặc ứng dụng có cơ chế bảo vệ riêng có thể chặn overlay và chụp ảnh. Dự án không vô hiệu hóa hoặc né các cơ chế bảo vệ đó.
