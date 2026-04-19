# BÁO CÁO: GIẢI PHÁP CÔNG NGHỆ

## 1. Ngôn ngữ và Thư viện Lập trình
Dự án được xây dựng hoàn toàn bằng ngôn ngữ lập trình **Python**, tận dụng hệ sinh thái thư viện mạnh mẽ để xử lý cả giao diện Web và giao tiếp hạ tầng mạng:
- **Streamlit:** Thư viện framework chính dùng để xây dựng nhanh giao diện đồ họa dưới dạng Web App, quản lý các thẻ chức năng, biểu mẫu và duy trì trạng thái phiên làm việc (Session state).
- **Paramiko:** Thư viện Python cung cấp chuẩn giao thức SSH/SFTP (Secure Shell), đóng vai trò thiết lập kênh truyền tải lệnh và tập tin đến máy ảo Windows một cách mã hóa và an toàn. Khóa xác thực sử dụng chuẩn `Ed25519`.
- **Pynput:** Được cài đặt trên máy đích (Windows VM) nhằm phục vụ chức năng lắng nghe và ghi nhận các sự kiện phần cứng từ bàn phím.
- **Python-dotenv:** Dùng để nạp và quản lý các tham số môi trường bí mật (IP máy chủ, Mật khẩu, Đường dẫn khóa vòng) tách biệt khỏi mã nguồn.

## 2. Giải pháp Mạng và Đảm bảo Bảo mật (Cloudflare Tunnel)
Để giải quyết bài toán ứng dụng local (tại máy nội bộ) không thể chia sẻ ra ngoài Internet mà không gây rủi ro về an ninh (khi mở cổng Router), dự án áp dụng giải pháp **Cloudflare Tunnel**:
- **Cơ chế hoạt động:** Một agent (daemon) tên là `cloudflared` chạy ngầm trên máy vận hành ứng dụng. Agent này tạo một đường hầm mã hóa (outbound tunnel) kết nối trực tiếp đến hạ tầng Edge của Cloudflare. 
- **Bảo mật:** Nhờ kết nối là một chiều (từ trong ra ngòai), Router nội bộ mạng không cần mở bất kỳ Port nào (Zero inbound ports). Mọi lưu lượng từ ngoài vào đều phải đi qua tên miền cung cấp bởi Cloudflare, qua chuẩn HTTPS mã hóa chứng chỉ tự động, chống lại các hình thức quét cổng (Port scan), sau đó mới tới ứng dụng web Streamlit.
- Do đó máy điều khiển cục bộ được bảo vệ an toàn trong khi máy ảo vẫn được kết nối thông qua SSH nội bộ.

## 3. Luồng xử lý Cốt lõi (Workflow)
Quy trình giao tiếp xuyên suốt của hệ thống đi từ: 
`Trình duyệt -> URL (Cloudflare) -> Streamlit App -> Giao thức SSH nội bộ -> Windows đích`.

Thiết kế kiến trúc hệ thống áp dụng một phương pháp giải quyết vấn đề đặc biệt để vượt qua rào cản nền tảng cốt lõi của hệ điều hành Windows (**Session 0 Isolation**).

### Xử lý rào cản Windows Session 0 Isolation
Theo kiến trúc Windows, khi thực thi lệnh thông qua luồng SSH, các tiến trình sẽ được chạy trong **Session 0** (phiên dành riêng cho dịch vụ và chạy ngầm, hoàn toàn không có đồ họa hiển thị GUI màn hình). 
Nếu chạy các lệnh chụp màn hình, bật ứng dụng, hay ghi nhận phím nhấn từ Session 0, kết quả thu được sẽ thất bại (ví dụ: ảnh màu đen) do không có giao tiếp vật lý. 

**Giải pháp đề xuất và luồng thực thi như sau:**
1. Streamlit thông qua `Paramiko` đẩy một nhóm lệnh (scripts) qua SFTP vào thư mục trung gian trên máy tính Windows.
2. Ứng dụng chạy lệnh kích hoạt một Nhiệm vụ Lập lịch của Windows (**Scheduled Task**) do mã nguồn tự động cấp phát, kèm theo cờ cấu hình `LogonType=Interactive`.
3. Nhờ chuẩn định dạng Interactive, Task Scheduler này sẽ làm cầu nối đưa tập lệnh từ Session 0 vượt qua và thực thi ở **Session 1** (nơi màn hình nền thực và các thao tác của người dùng đang hiện diện).
4. Để khắc phục lỗi viền cửa sổ CMD/PowerShell hiện lên bất chợt ở Session 1 khi chụp xuất hình ảnh, tiến trình bọc thêm một lớp **VBScript** với cấu hình thuộc tính màn hình ẩn hoàn toàn (`WindowStyle Hidden / Run(0)`).
5. Sau khi thu ảnh hoặc file xong, ảnh/log tiếp tục được lấy ngược về Streamlit thông qua SFTP và hiển thị cho người xem.
