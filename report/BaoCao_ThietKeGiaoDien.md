# BÁO CÁO: THIẾT KẾ GIAO DIỆN PHẦN MỀM

## 1. Triết lý thiết kế và Ngôn ngữ trực quan
Giao diện của phần mềm "Remote PC Control" được thiết kế theo phong cách **Dark Glassmorphism** (giao diện tối kết hợp hiệu ứng kính mờ). Mục tiêu cốt lõi của thiết kế là mang lại trải nghiệm chuyên nghiệp, trực quan và giảm thiểu tối đa sự phân tâm (nhiễu thị giác) cho người quản trị. 

Các nguyên tắc thiết kế chính bao gồm:
- **Tối giản hóa:** Lược bỏ các thành phần menu không cần thiết của framework để tập trung hoàn toàn vào khu vực điều khiển.
- **Phản hồi rõ ràng (Clear Feedback):** Mọi thao tác của người dùng đều đi kèm với các chỉ báo trạng thái như biểu tượng chờ (spinner) khi đang xử lý, và các thông báo màu sắc khi thành công (xanh lá) hoặc gặp lỗi (đỏ).
- **Phân cấp thông tin:** Các dữ liệu quan trọng như trạng thái kết nối máy chủ được làm nổi bật để dễ dàng quan sát, trong khi các thông tin phụ trợ được hiển thị với kích thước và màu sắc chìm hơn.

## 2. Bảng định dạng (Typography & Colors)
Hệ thống sử dụng bộ phông chữ **Inter** nhằm đảm bảo tính hiện đại và khả năng đọc tốt trên các màn hình kỹ thuật số.

Bảng màu (Color Palette) được quy chuẩn thống nhất:
- **Nền chính:** Sử dụng dải màu gradient tối (nhóm màu indigo đậm) tạo chiều sâu.
- **Màu nhấn (Accent):** Xanh tím (Indigo) được sử dụng cho các nút bấm chính (Primary buttons), viền hộp thoại đang thao tác, và đánh dấu các thẻ (tabs) đang hoạt động.
- **Màu trạng thái:** Xanh lá cây (dành cho trạng thái Online/Thành công) và Đỏ (dành cho trạng thái Offline/Cảnh báo lỗi hoặc thao tác nguy hiểm).
- **Thành phần nổi (Cards):** Áp dụng độ trong suốt và hiệu ứng làm mờ nền (backdrop-filter) để tạo hiệu ứng kính, kết hợp với viền mảnh giúp phân chia rõ ràng các khối thông tin mà không làm thiết kế bị nặng nề.

## 3. Cấu trúc bố cục (Layout Structure)
Ứng dụng sử dụng bố cục toàn màn hình (wide layout) được chia thành 2 phần chính:

* **Thanh điều hướng bên trái (Sidebar):** Quản lý kết nối hệ thống. Hiển thị danh sách các máy ảo (VM) dưới dạng thẻ thông tin (Metric Card) đi kèm trạng thái kết nối theo thời gian thực (Connected/Disconnected). Tại đây, người dùng có thể thực hiện kết nối, ngắt kết nối, chuyển đổi nhanh giữa các máy ảo đang điều khiển, và đăng xuất khỏi phiên làm việc.
* **Khu vực nội dung chính (Main Content):** Chứa màn hình xác thực đăng nhập ban đầu. Khi đã truy cập thành công, khu vực này hiển thị tên máy chủ đang điều khiển và một hệ thống thanh thẻ (Tab Bar) nhằm phân chia các nhóm chức năng khác nhau (Tiến trình, Ảnh màn hình, Keylogger, Truyền tệp, Hệ thống).

## 4. Trải nghiệm người dùng (UX) đối với các chức năng
- **Minh bạch trạng thái:** Các tiến trình tải lâu (như chụp ảnh màn hình hay bắt đầu ghi phím) đều khóa tương tác tạm thời để tránh người dùng thao tác đè, đồng thời có thông báo đang xử lý.
- **Cơ chế an toàn:** Đối với các chức năng thay đổi trạng thái của máy đích (như Tắt máy hoặc Khởi động lại), giao diện luôn yêu cầu người dùng nhấp đúp để xác nhận nhằm tránh các thao tác sai lầm không đáng có.
