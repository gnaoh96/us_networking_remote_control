# BÁO CÁO: MÔ TẢ CÁC CHỨC NĂNG

Ứng dụng "Remote PC Control" cung cấp một bộ công cụ toàn diện giúp người quản trị điều khiển và giám sát các máy ảo (Virtual Machines - VM) chạy hệ điều hành Windows từ xa thông qua một giao diện web tập trung. Chi tiết các chức năng cốt lõi như sau:

## 1. Cổng Xác thực và Quản lý phiên (Authentication)
Trước khi truy cập vào hệ thống điều khiển, ứng dụng yêu cầu người dùng xác thực thông qua một mật khẩu bảo vệ.
- **Đăng nhập:** Người dùng nhập mật khẩu định sẵn. Nếu chính xác, hệ thống khởi tạo phiên làm việc (Session) thông qua cơ chế lưu trạng thái.
- **Đăng xuất:** Người dùng có thể chủ động đóng phiên làm việc, ứng dụng sẽ lập tức ngắt toàn bộ kết nối SSH đang khả dụng tới các máy ảo và đưa giao diện về màn hình khóa ban đầu.

## 2. Quản lý Kết nối máy tính từ xa
- **Kết nối/Ngắt kết nối độc lập:** Người dùng có thể khởi tạo hoặc đóng đường truyền mã hóa đến từng máy tính đích một cách độc lập thông qua thanh điều hướng bên trái. Hệ thống sẽ có thông báo nếu gặp lỗi kết nối (ví dụ: máy đích tắt mạng).
- **Chuyển đổi màn hình điều khiển:** Khi duy trì kết nối với nhiều máy cùng lúc, ứng dụng cho phép người dùng chọn xem và thao tác tương tác với tính năng của từng máy ảo thay đổi theo thời gian thực.

## 3. Quản lý Tiến trình (Process Manager)
- **Danh sách tiến trình:** Liệt kê toàn bộ các phần mềm và tác vụ đang chạy trên máy đích (gồm Tên tiến trình, Mã PID, Bộ nhớ sử dụng). Cung cấp thanh tìm kiếm để lọc nhanh thông tin.
- **Kết thúc tiến trình (Kill):** Cho phép người dùng nhập tên tiến trình và ép đóng các phần mềm đang bị treo hoặc không mong muốn.
- **Khởi chạy ứng dụng (Launch):** Hỗ trợ nhập đường dẫn hoặc tên tệp thực thi (ví dụ: `notepad.exe`) để kích hoạt ứng dụng. Phần mềm sẽ hiển thị trực tiếp trên màn hình vật lý/màn hình tương tác của máy đích.

## 4. Chụp Màn hình (Screenshot)
- Người dùng có thể ra lệnh chụp lại toàn bộ màn hình giao diện hiện tại của máy đích. Kết quả sẽ được tải về qua mạng và hiển thị trực tiếp trên trình duyệt, kèm thời gian chụp. Người dùng có tùy chọn tải hình ảnh này về máy cục bộ.

## 5. Giám sát thao tác phím (Keylogger)
- Cung cấp chức năng ghi lại lịch sử thao tác bàn phím trên máy đích trong một khoảng thời gian được thiết lập trước (từ 5 đến 60 giây). Khi quá trình ghi hoàn tất, kết quả văn bản sẽ được hiển thị trên giao diện và cho phép trích xuất thành tệp văn bản (`.txt`). Tính năng phục vụ cho mục đích kiểm tra và đo lường hệ thống.

## 6. Truyền Tải Tệp tin (File Transfer)
Hỗ trợ trao đổi dữ liệu hai chiều giữa máy điều khiển và máy đích.
- **Tải lên (Upload):** Người dùng dùng giao diện chọn file từ máy cục bộ đẩy sang thư mục cấu hình sẵn (`C:\Temp\`) trên máy Windows.
- **Tải xuống (Download):** Người dùng nhập tên tệp đang tồn tại trên máy Windows và nhận tệp về thông qua hộp thoại tải tài liệu của trình duyệt.

## 7. Điều khiển Nguồn Hệ thống (System Controls)
- Cung cấp hai nút lệnh cấp độ hệ thống là **Tắt máy (Shutdown)** và **Khởi động lại (Restart)**.
- Quá trình thực hiện yêu cầu xác nhận 2 lần để đảm bảo tính an toàn. Lệnh sẽ gửi trực tiếp đến hệ điều hành đích để tắt máy ngay lập tức và tự động ngắt kết nối làm việc hiện hành.
