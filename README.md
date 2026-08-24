# Overlay AI cho Windows

Ứng dụng overlay desktop viết bằng Python/PySide6, hỗ trợ chat văn bản và ảnh qua OpenAI-compatible, Gemini API và Codex OAuth thử nghiệm.

> **Tuyên bố sử dụng:** Dự án chỉ phục vụ mục đích học tập. Không được sử dụng trong bất kỳ trường hợp gian lận nào, bao gồm thi cử, kiểm tra và đánh giá.

## Tính năng

- Overlay trong suốt, không viền, always-on-top, click-through và khay hệ thống.
- Resize từ bốn cạnh/bốn góc, điều chỉnh opacity từ `5%` đến `100%` và ba theme Đen/Xám/Trắng. Thanh trượt và phím tắt đồng bộ theo thời gian thực.
- Cài đặt nằm trong overlay, responsive và tự động lưu.
- Chụp vùng trên nhiều màn hình; ảnh được đính kèm trước khi gửi và có thể lưu bản sao vào folder đã chọn. `Ctrl+E` trong Cài đặt tự lưu, chuyển về Chat rồi mở vùng chụp.
- Chat văn bản/ảnh qua OpenAI-compatible, Gemini API hoặc Codex OAuth thử nghiệm.
- Render câu trả lời bằng Markdown và tự cuộn nội dung.
- Lưu model riêng theo provider; mã hóa API key, danh sách Gemini API key và phiên Codex bằng Windows DPAPI.
- Hỗ trợ bảy phím tắt toàn cục có thể tùy chỉnh.

## Cài đặt và chạy

Yêu cầu Windows 10/11 và Python 3.11 trở lên.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
.\.venv\Scripts\python.exe .\app.py
```

Trong Cài đặt, chọn provider rồi cấu hình:

- **OpenAI-compatible:** Base URL, model và API key. Provider phải hỗ trợ Chat Completions; gửi ảnh cần hỗ trợ data URL.
- **Gemini API:** chọn model gợi ý hoặc nhập model khác. Mỗi tab số chứa một API key từ Google AI Studio; tab `+` luôn nằm sát tab số cuối để thêm key và `×` xóa tab. Ứng dụng xoay vòng key theo request và thử key kế tiếp khi Gemini trả `401`, `403` hoặc `429`.
- **Codex OAuth (thử nghiệm):** chọn model gợi ý hoặc nhập model khác, bấm **Đăng nhập**, hoàn tất trong trình duyệt rồi quay lại ứng dụng. Nút đổi thành **Đăng xuất** khi có phiên và xóa phiên cục bộ khi bấm.
- Nút **Test** gửi prompt tối thiểu qua model đang chọn và hiển thị kết quả trong Cài đặt; request này không được thêm vào lịch sử chat. Trong khi request chạy, nút đổi thành **Hủy test**.
- **Folder lưu ảnh đã gửi** cho phép chọn bằng nút icon folder, mở và bật/tắt lưu bằng công tắc có animation. Toàn bộ công tắc nhận click. Tắt lưu vẫn giữ folder để bật lại nhanh. Chỉ ảnh thực sự được gửi mới được sao chép; lỗi ghi file không chặn request chat.
- Prompt dùng khi gửi ảnh áp dụng cho cả ba provider.

Cấu hình OpenAI-compatible cũ được chuyển một lần sang vùng cấu hình provider mới. Mỗi provider có danh sách model riêng; mọi model gợi ý đều có thể xóa và model tự nhập có thể lưu lại. Danh sách gợi ý không bảo đảm model đang tồn tại hoặc account hiện tại có quyền sử dụng; dùng **Test** để kiểm tra qua provider thật.

### Cảnh báo Codex OAuth

Codex dùng Authorization Code + PKCE, callback `http://localhost:1455/auth/callback`, public client ID của Codex CLI và backend ChatGPT Codex nội bộ. Đây không phải OAuth app được cấp riêng cho Overlay AI và API này không phải public contract của OpenAI.

Tích hợp có thể bị thay đổi, chặn hoặc thu hồi; một số account, workspace hoặc model có thể trả `401`/`403` dù đăng nhập thành công. Overlay AI gửi danh tính riêng, không giả phiên bản Codex CLI. Không dùng provider này cho production hoặc enterprise.

API key và token bundle được mã hóa bằng Windows DPAPI cho tài khoản Windows hiện tại. Đăng xuất chỉ xóa phiên khỏi máy; ứng dụng không khẳng định đã revoke token phía server. Bản đầu không hỗ trợ nhiều tài khoản Codex hoặc tự dò danh sách model.

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

Có thể thay đổi các tổ hợp này trong Cài đặt. Mỗi tổ hợp cần ít nhất một modifier `Ctrl`, `Alt`, `Shift` hoặc `Win` và không được trùng nhau. Có thể giữ phím giảm/tăng opacity để thay đổi liên tục theo keyboard repeat của Windows; các hotkey khác vẫn chống lặp. Khi Cài đặt đang mở, phím chụp tự lưu cấu hình và chuyển về Chat; phím gửi vẫn bị chặn để tránh gửi ngoài ý muốn.

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
