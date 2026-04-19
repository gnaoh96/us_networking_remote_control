# Kịch bản Thuyết trình (App Demo Speech Flow)

1. Tổng quan -> Tính năng -> Xây dựng -> Công cụ
2. Truy cập URL -> ClouldFlare URL
3. CLoudflare Tunnel
4. Đăng nhập vào app
5. Giới thiệu tổng quan giao diện
6. Triết lý thiết kế
7. Demo các tính năng
8. Demo cả 2 máy so sánh before & after
9. Demo Shutdown, Restart
10. Nêu hạn chế (nói ý thiếu tính năng bật webcam) và close project.


## 0. Tổng quan dự án (Overview)
+ **Giới thiệu:** Xin chào thầy và các bạn, hôm nay nhóm em xin trình bày ứng dụng "Remote PC Control".
+ **Mục đích:** Ứng dụng web giúp quản lý và điều khiển từ xa các máy ảo Windows mà không cần cài đặt thêm phần mềm agent (như TeamViewer) lên máy host. Mọi thứ được xử lý nội bộ qua giao thức SSH chuẩn và deploy lên mạng internet chứ không chỉ localhost.
+ **Quy mô demo:** Hiện tại ứng dụng đang quản lý cùng lúc 2 máy ảo Windows 11.
+ **Các tính năng cơ bản:** Xem và quản lý các tiến trình (Processes), chụp ảnh màn hình từ xa (Screenshot), ghi lại thao tác phím (Keylogger), truyền tệp tin (File Transfer), và điều khiển nguồn hệ thống (Shutdown/Restart).

## 1. Clouldflare tunnel
Câu hỏi: Clouldflare tunnel là gì và sao phải dử dụng cho dự án?
+ Lý do tại sao: Bản chất và điểm yếu của dự án local:
    + Nếu chỉ dùng IP localhost thì chỉ dùng được trong mạng LAN, không thể chia sẻ ứng dụng với thành viên còn lại trong nhóm. Bản chất local app là ứng dụng chạy ở local webserver với giao thức HTTP, ko có chứng chỉ SSL/TLS để mã hóa dữ liệu khi đưa ra internet (HTTPS).
    + Nếu dùng IP public thì phải mở port trên router, dễ bị tấn công, không an toàn, bảo mật thấp.
    + Nếu dùng VPN thì phải cài đặt VPN cho từng thành viên, phức tạp, tốn tài nguyên.
    + Và nhóm kết luận dùng Cloudflare Tunnel là phương án tối ưu nhất.
+ Cloudflare Tunnel là gì?
    + Là ứng dụng hỗ trợ public nhanh chóng local app ra internet mà không cần mở port hoặc cấu hình IP trên router.
    + Cloudflare Tunnel sẽ xử lý các công việc phức tạp như: cấp phát domain, mã hóa HTTPS, public routing, và gia cố bảo mật (defensive security). 
    + Vậy Cloudflare Tunnel hoạt động như thế nào?
        Trình duyệt (Người dùng) => HTTPS => Cloudflare Edge => Tunnel mã hoá => cloudflared (trên Mac) => localhost:8501 (Streamlit app) => Cầu nối SSH nội bộ đến các máy Windows VMs.

## 2. Triết lý Thiết kế Giao diện
+ Nhóm hướng tới trải nghiệm chuẩn mức chuyên nghiệp với phong cách **Dark Glassmorphism** (Giao diện tối, thẻ hiệu ứng kính mờ).
+ **Mục tiêu chính:** Giao diện trực quan, hạn chế tối đa độ nhiễu. Có các thanh thông báo báo hiệu trạng thái (Loading, Success, Error) giúp người quản trị phân biệt dễ dàng. Thiết kế tối ưu để làm nổi bật các dữ liệu trạng thái máy chủ (Online/Offline) trên Sidebar.

## 3. Quản lý Đăng nhập Ứng dụng
+ App sử dụng **Session State Auth** với mật khẩu định sẵn.
+ **Lợi ích thực tiễn:** 
    + Mặc dù Cloudflare che giấu ứng dụng khỏi các quét cổng (port scan), bất kỳ ai có URL vẫn có thể nhìn thấy giao diện.
    + Việc ứng dụng có lớp mật khẩu bảo vệ là chốt chặn cuối cùng ngăn người lạ can thiệp vào máy chủ Windows. Điều này vừa tăng tính bảo mật, vừa giúp thiết kế tinh gọn vì không phụ thuộc vào thư viện bên thứ 3 phức tạp.

## 4. Demo Thao tác & So sánh trên 2 Máy Ảo
*Thao tác luân phiên giữa VM 1 và VM 2 ngay trên Sidebar để mọi người thấy trạng thái thay đổi theo thời gian thực (Real-time). Mọi thao tác chọn mục sẽ nhắm đích vào máy ảo đang active.*

+ **Tab Quản lý Tiến trình (Processes):** 
    + Thử bật một app như `notepad.exe` từ xa.
    + Tìm kiếm tên tiến trình và show cách kill tiến trình.
+ **Tab Chụp màn hình (Screenshot):**
    + Chụp lại màn hình xem sự khác nhau giữa nội dung đang chạy trên VM 1 và VM 2.
+ **Tab Ghi phím (Keylogger):** 
    + Demo cài đặt thời lượng ghi nhanh (5 giây) trên VM đang mở Notepad.
    + Gõ vài chữ trên máy ảo, chờ ứng dụng xuất log về tải xuống để chứng minh độ chính xác.
+ **Tab Truyền tệp (Files):** 
    + Upload 1 tệp văn bản từ máy Host (Mac) thẳng vào `C:\Temp\` của VM. Vừa upload xong, mở máy ảo lên cho thấy file đã hiện diện.

## 5. Demo Hệ thống & Tổng kết
+ **Tab System Controls:** Show nút cảnh báo màu đỏ (Yêu cầu xác nhận hai lần để tránh chạm nhầm).
+ Thao tác nhấn Shutdown trên VM 2. Mọi người để ý trạng thái của VM 2 trên Sidebar sẽ nhảy từ màu xanh (Connected) sang đỏ (Disconnected) khi tiến trình truyền lệnh kết thúc.
+ **Tổng kết:** Trên đây là toàn bộ tính năng cốt lõi của Remote PC Control. Việc kết hợp Streamlit với SSH và Tunnel của Cloudflare đem lại một giải pháp mạnh mẽ, an toàn và dễ sử dụng cho các quản trị viên quản lý máy tính từ xa. Cảm ơn thầy và các bạn đã lắng nghe.