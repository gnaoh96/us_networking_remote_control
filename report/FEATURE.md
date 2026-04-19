# FEATURE.md — Mô tả Tính năng & Luồng Hoạt động

---

## 🌐 Triển khai & Bảo mật Mạng — Cloudflare Tunnel

Ứng dụng được xây dựng theo mô hình **local-first**: Streamlit chạy tại `localhost:8501` trên máy Mac, và các máy ảo Windows chỉ có thể truy cập từ mạng nội bộ.

**Để mở rộng khả năng truy cập ra ngoài Internet và đồng thời bảo đảm an toàn cho mạng nội bộ, giải pháp được đề xuất là sử dụng [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/).**

> **Ý tưởng cốt lõi:**
> **Thay vì mở cổng (port forwarding) trên router — vốn phơi bày địa chỉ IP công khai và tạo lỗ hổng bảo mật — Cloudflare Tunnel tạo một đường hầm mã hoá từ máy Mac đến Cloudflare Edge. Người dùng truy cập ứng dụng qua một URL HTTPS công khai (ví dụ: `https://remote.yourdomain.com`) mà không cần mở bất kỳ cổng nào, không cần IP tĩnh, và toàn bộ lưu lượng được bảo vệ bởi TLS của Cloudflare.**

Lợi ích so với các phương án khác:

| Phương án | Bảo mật | Cài đặt | Chi phí |
|---|---|---|---|
| Port Forwarding trực tiếp | ⚠️ Thấp | Dễ | Miễn phí |
| VPN (WireGuard/OpenVPN) | ✅ Cao | Phức tạp | Miễn phí/trả phí |
| **Cloudflare Tunnel** | **✅ Cao** | **Đơn giản** | **Miễn phí** |
| ngrok | ✅ Trung bình | Dễ | Giới hạn miễn phí |

Cài đặt nhanh:
```bash
# Cài cloudflared
brew install cloudflare/cloudflare/cloudflared

# Xác thực với tài khoản Cloudflare
cloudflared tunnel login

# Tạo tunnel và trỏ đến Streamlit
cloudflared tunnel create remote-control
cloudflared tunnel route dns remote-control remote.yourdomain.com
cloudflared tunnel run --url http://localhost:8501 remote-control
```

Sau đó truy cập `https://remote.yourdomain.com` từ bất kỳ đâu — ứng dụng vẫn yêu cầu mật khẩu đăng nhập trước khi sử dụng.

---

## 🔐 Xác thực (Authentication)

### Mô tả
Cổng bảo vệ toàn bộ ứng dụng bằng mật khẩu trước khi người dùng nhìn thấy bất kỳ tính năng nào.

### Luồng hoạt động
```
Người dùng mở app
  → Kiểm tra st.session_state["authed"]
  → Nếu chưa xác thực → Hiển thị màn hình đăng nhập
      → Nhập mật khẩu → So sánh với APP_PASSWORD trong .env
      → Đúng → session_state["authed"] = True → st.rerun()
      → Sai  → st.error("Incorrect password")
  → Nếu đã xác thực → Hiển thị toàn bộ ứng dụng
```

### Chi tiết kỹ thuật
- Mật khẩu lưu trong `.env` (`APP_PASSWORD`), không hardcode trong code
- Dùng `st.form` → người dùng nhấn **Enter** hoặc click **Sign In** đều hoạt động
- `st.stop()` chặn toàn bộ render bên dưới khi chưa xác thực
- Nút **🔒 Sign Out** xoá toàn bộ `session_state` và ngắt kết nối tất cả VM

---

## 🔌 Quản lý Kết nối SSH

### Mô tả
Sidebar cho phép kết nối/ngắt kết nối độc lập tới từng VM trong danh sách. Khi nhiều VM đã kết nối, người dùng chọn VM đang hoạt động qua radio button — toàn bộ tab bên phải lập tức nhắm đến VM đó.

### Luồng hoạt động — Kết nối
```
Nhấn [⚡ Connect VM x]
  → connect(host, user, key_path)
      → paramiko.SSHClient.connect(timeout=8, key_filename=...)
      → Thành công → lưu client vào session_state["ssh_vmx"]
      → Thất bại   → lưu lỗi vào session_state["err_vmx"]
                   → hiển thị expander Debug info
  → st.rerun() → sidebar cập nhật trạng thái
```

### Luồng hoạt động — Ngắt kết nối
```
Nhấn [🔌 Disconnect VM x]
  → client.close()
  → Xoá session_state["ssh_vmx"] và ["err_vmx"]
  → Nếu VM đó đang là active_vm → xoá active_vm_id
  → st.rerun()
```

### Kiểm tra kết nối của VM khi đang dùng dứng dụng
- `is_connected(client)`: kiểm tra `transport.is_active()` mỗi lần render
- Nếu transport chết (VM tắt đột ngột) → sidebar tự chuyển sang trạng thái Disconnected

### Chọn VM đang hoạt động
```
connected_vms = [vm đã kết nối]
Nếu len > 0 → hiện st.radio để chọn active_vm_id
Tất cả tab đọc: client = session_state["ssh_{active_vm_id}"]
```

---

## ⚙️ Quản lý Tiến trình

### Tính năng con

#### 1. Liệt kê tiến trình
```
[🔄 Refresh] → xoá cache session_state["proc_list"]
  → list_processes(client)
      → tasklist /FO CSV /NH
      → Parse từng dòng CSV → [{name, pid, session, mem_kb}]
  → Hiển thị DataFrame: Name | PID | Memory(KB) | Session
```
- Kết quả cache trong `session_state["proc_list"]` để tránh gọi SSH mỗi lần render
- Cache tự xoá khi người dùng đổi VM hoặc nhấn Refresh

#### 2. Tìm kiếm / Lọc
```
[🔍 Filter input] → filter = search.lower()
  → filtered = [p for p in procs if filter in p["name"].lower()]
  → Nếu filtered rỗng → st.info("Không tìm thấy")
  → Nếu có → Render DataFrame với kết quả lọc
```

#### 3. Kill tiến trình
```
Nhập tên tiến trình → Nhấn [💀 Kill]
  → kill_process(client, name)
      → taskkill /IM <name> /F
      → Thành công nếu "SUCCESS" trong output
  → True  → st.success + xoá proc_list cache + st.rerun()
  → False → st.error với thông báo từ Windows
```

#### 4. Khởi động ứng dụng
```
Nhập exe_path → Nhấn [▶️ Launch]
  → start_process(client, exe_path)
      → Tạo Scheduled Task (LogonType=Interactive, RunLevel=Highest)
      → Task kích hoạt sau 2 giây → chạy exe trong Session 1
      → Chờ 4 giây → Kiểm tra tiến trình có trong tasklist không
  → True  → st.success
  → False → st.warning (lệnh đã gửi nhưng tiến trình không thấy)
```
**Lý do dùng Task Scheduler**: `exec_command` SSH chạy trong Session 0 (không có màn hình) → ứng dụng khởi động nhưng vô hình. Task Scheduler với `LogonType=Interactive` đưa tiến trình vào Session 1 (màn hình thực của người dùng).

---

## 📸 Chụp Màn hình

### Mô tả
Chụp ảnh màn hình thực của VM và trả về file PNG hiển thị ngay trên trình duyệt.

### Luồng hoạt động
```
Nhấn [📸 Take Screenshot]
  → screenshot(client)
      1. Tạo C:\Temp\ nếu chưa có
      2. SFTP upload _screenshot.ps1 (PowerShell + System.Windows.Forms)
      3. SFTP upload _screenshot.vbs (VBScript wrapper — chạy ẩn)
      4. Đăng ký Scheduled Task "RCShot":
            Execute: wscript.exe
            Argument: C:\Temp\_screenshot.vbs
            Trigger: sau 2 giây, một lần
            Principal: user hiện tại, LogonType=Interactive
      5. Start-Sleep 7 giây (đợi task hoàn thành)
      6. Unregister task
      7. SFTP download C:\Temp\screenshot.png
      8. time.sleep(0.5) để flush
  → Trả về bytes PNG
  → st.image(bytes, use_container_width=True)
  → st.download_button("⬇️ Download PNG")
```

### Chuỗi thực thi trên VM (ẩn hoàn toàn)
```
Task Scheduler
  → wscript.exe _screenshot.vbs          (không có cửa sổ)
    → VBS: Run("powershell -WindowStyle Hidden -File _screenshot.ps1", 0, True)
      → PowerShell (ẩn, chặn đến khi xong)
        → CopyFromScreen toàn màn hình → lưu screenshot.png
```

### Vì sao phức tạp như vậy?
SSH Process → Session 0 (không display) → `CopyFromScreen` trả về ảnh đen.
Task Scheduler Interactive → Session 1 (màn hình thực) → ảnh đúng.
VBScript → ẩn cửa sổ PowerShell hoàn toàn trước khi chụp.

---

## ⌨️ Ghi Phím (Keylogger)

### Mô tả
Ghi toàn bộ phím bấm trên VM trong khoảng thời gian nhất định và trả về log văn bản.

### Luồng hoạt động
```
Chọn thời lượng (5–60 giây) → Nhấn [▶️ Start Keylog Capture]
  → keylog(client, duration_sec)
      1. Tạo C:\Temp\
      2. Xoá keylog.txt cũ (nếu có)
      3. Unregister task RCKeylog cũ (dọn dẹp phiên trước)
      4. SFTP upload _keylogger.py (pynput listener)
      5. Phân giải đường dẫn python.exe:
            Get-Command python → full path
            Fallback: where.exe python
      6. Tạo _keylogger.vbs động với path và duration
      7. SFTP upload _keylogger.vbs
      8. Đăng ký Scheduled Task "RCKeylog":
            Execute: wscript.exe
            Argument: C:\Temp\_keylogger.vbs
            Principal: LogonType=Interactive
            ExecutionTimeLimit: duration + 30s
      9. Start-Sleep (duration + 8 giây)
      10. Unregister task
      11. time.sleep(1)
      12. Test-Path keylog.txt → nếu không có → FileNotFoundError
      13. SFTP download C:\Temp\keylog.txt
  → Hiển thị st.code(log)
  → st.download_button("⬇️ Download log")
```

### Chuỗi thực thi trên VM (ẩn hoàn toàn)
```
Task Scheduler
  → wscript.exe _keylogger.vbs      (không có cửa sổ)
    → VBS: Run("python.exe _keylogger.py 15", 0, True)
                                      ↑ ẩn  ↑ chặn (đồng bộ)
      → Python: pynput keyboard.Listener
          → Ghi phím trong {duration} giây
          → Lưu C:\Temp\keylog.txt
```

### Tại sao phân giải python.exe tại runtime?
Task Scheduler dùng PATH khác với terminal. `python` có thể không tìm thấy. Dùng `Get-Command python` từ SSH session (nơi PATH đúng) → lấy đường dẫn tuyệt đối → hardcode vào VBS.

---

## 📁 Truyền Tệp

### Mô tả
Tải tệp từ Mac lên VM và từ VM xuống Mac. Tất cả tệp đi qua `C:\Temp\` trên VM.

### Luồng Upload (Mac → VM)
```
Chọn file qua st.file_uploader → Nhấn [Upload to VM]
  → Ghi file vào tempfile tạm trên Mac
  → sftp_upload_file(client, tmp_path, filename)
      → SFTP.put(local, "C:\\Temp\\{filename}")
  → os.unlink(tmp) — xoá file tạm
  → st.success("Uploaded to C:\Temp\{filename}")
```

### Luồng Download (VM → Mac)
```
Nhập tên file trong C:\Temp\ → Nhấn [Download from VM]
  → sftp_download_bytes(client, "C:\\Temp\\{filename}")
      → SFTP.open(remote) → io.BytesIO.read()
  → st.download_button(data=bytes, file_name=filename)
      → Trình duyệt hiển thị hộp thoại lưu file
```

---

## 🔴 Điều khiển Hệ thống

### Mô tả
Tắt nguồn hoặc khởi động lại VM từ xa. Yêu cầu xác nhận hai lần để tránh thao tác nhầm.

### Luồng Shutdown
```
Nhấn [⏻ Shutdown VM] lần 1
  → session_state["confirm_shutdown"] = True
  → st.warning("Nhấn lại để xác nhận")

Nhấn [⏻ Shutdown VM] lần 2
  → shutdown(client) → powershell "shutdown /s /t 0"
  → disconnect_vm(active_vm_id) → đóng SSH session
  → session_state["confirm_shutdown"] = False
  → st.success("Shutdown command sent")
```

### Luồng Restart
Tương tự Shutdown, thay `shutdown /s /t 0` bằng `shutdown /r /t 0`.

### Lưu ý quan trọng
- SSH bị ngắt ngay sau khi gửi lệnh (VM sắp tắt, giữ kết nối vô nghĩa)
- `shutdown /t 0` = không có thời gian chờ, tắt ngay lập tức
- Sidebar tự cập nhật trạng thái Disconnected sau khi `st.rerun()`

---

## 🔄 Luồng Dữ liệu Tổng thể

```
Người dùng (Trình duyệt)
  ↕  HTTP (localhost hoặc qua Cloudflare Tunnel)
Streamlit Server (Mac)
  ↕  SSH exec_command / SFTP (paramiko, port 22)
Windows VM (Session 0)
  ↕  Windows Task Scheduler (LogonType=Interactive)
Windows VM (Session 1 — Màn hình thực)
  └── PowerShell / Python / wscript.exe (chạy ẩn)
        └── Output → C:\Temp\ → SFTP → Streamlit → Trình duyệt
```

---

## 📋 Bảng Tóm tắt Kỹ thuật

| Tính năng | Lệnh Windows | Session | Phương thức trả về |
|---|---|---|---|
| List processes | `tasklist /FO CSV /NH` | 0 (SSH) | JSON dict list |
| Kill process | `taskkill /IM name /F` | 0 (SSH) | bool + message |
| Launch app | Task Scheduler | 1 (Interactive) | bool + verify |
| Screenshot | PS `CopyFromScreen` qua VBS | 1 (Interactive) | PNG bytes (SFTP) |
| Keylogger | `pynput` qua VBS | 1 (Interactive) | TXT string (SFTP) |
| Upload | SFTP `put` | — | success/error |
| Download | SFTP `open + read` | — | bytes |
| Shutdown | `shutdown /s /t 0` | 0 (SSH) | Ngắt kết nối |
| Restart | `shutdown /r /t 0` | 0 (SSH) | Ngắt kết nối |
