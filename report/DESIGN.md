# DESIGN.md — Thiết kế Giao diện Remote PC Control

---

## 1. Triết lý Thiết kế

Ứng dụng hướng đến phong cách **dark glassmorphism** — tối, sang trọng, tập trung vào dữ liệu. Mọi thành phần đều nhất quán về màu sắc, khoảng cách và kiểu chữ, tạo cảm giác như một công cụ quản trị chuyên nghiệp.

Nguyên tắc cốt lõi:
- **Tối thiểu hoá nhiễu**: ẩn thanh menu và footer mặc định của Streamlit
- **Phản hồi rõ ràng**: mọi hành động đều có spinner, thông báo thành công/lỗi
- **Phân cấp thông tin**: nhãn nhỏ + giá trị lớn, màu phụ cho metadata

---

## 2. Bảng Màu (Color Palette)

| Vai trò | Giá trị | Dùng cho |
|---|---|---|
| Nền chính | `#0f0f1a` → `#1a1a2e` → `#16213e` | Gradient toàn trang (135°) |
| Nền sidebar | `#1a1a2e` → `#0f0f1a` | Gradient dọc |
| Màu nhấn (Indigo) | `#6366f1` | Viền active, tab underline, nút Primary |
| Màu nhấn nhạt | `#a5b4fc` | Tiêu đề section, text nhấn, tab active |
| Text chính | `#e2e8f0` | Nội dung chính |
| Text phụ | `#94a3b8` | Caption, label, tab không hoạt động |
| Text mờ | `#64748b` | Metadata, timestamp |
| Xanh lá (online) | `#22c55e` | Trạng thái kết nối, thành công |
| Đỏ (offline/danger) | `#ef4444` | Ngắt kết nối, cảnh báo xoá |
| Viền card | `rgba(99,102,241, 0.25)` | Mặc định → `0.6` khi hover |
| Nền card | `rgba(255,255,255, 0.04)` | Glassmorphism |

---

## 3. Typography

- **Font**: `Inter` (Google Fonts) — weights 300 / 400 / 500 / 600 / 700
- Áp dụng toàn bộ app qua `html, body, [class*="css"]`
- Không dùng font hệ thống mặc định

| Cấp | Size | Weight | Màu |
|---|---|---|---|
| Tiêu đề trang | `1.6rem` | 700 | `#a5b4fc` |
| Section title | `0.75rem` | 600 | `#a5b4fc`, chữ hoa, letter-spacing 0.1em |
| Body thường | `0.88rem` | 400 | `#e2e8f0` |
| Caption / label | `0.72–0.8rem` | 400–600 | `#64748b` |

---

## 4. Bố cục Tổng thể

```
┌─────────────────── Sidebar (280px) ─┬──────────── Main content ────────────┐
│  🖥️ Remote Control                  │  # 🖥️ Remote PC Control              │
│  ─────────────────────────────────  │  Controlling: VM 1                    │
│  [VM 1 Card]  ● Connected           │                                       │
│  [⚡ Connect / 🔌 Disconnect]        │  ┌─ Tabs ──────────────────────────┐  │
│  [VM 2 Card]  ● Disconnected        │  │ ⚙️ Processes │ 📸 │ ⌨️ │ 📁 │ 🔴│  │
│  ─────────────────────────────────  │  └─────────────────────────────────┘  │
│  ACTIVE VM — TABS                   │  [Tab content area]                   │
│  ○ VM 1  ● VM 2                     │                                       │
│  ─────────────────────────────────  │                                       │
│  SESSION                            │                                       │
│  [🔒 Sign Out]                      │                                       │
└─────────────────────────────────────┴───────────────────────────────────────┘
```

- Layout: `wide` (toàn chiều ngang trình duyệt)
- Sidebar mặc định mở (`initial_sidebar_state="expanded"`)
- Main content không giới hạn chiều rộng

---

## 5. Thành phần Tái sử dụng

### 5.1 Metric Card (`.metric-card`)
```
┌────────────────────────────────┐
│ LABEL NHỎ (0.72rem, #64748b)   │  ← tên VM hoặc tiêu đề
│ Nội dung chính (0.88rem bold)  │
│ ● Trạng thái (màu động)        │
└────────────────────────────────┘
```
- `background: rgba(255,255,255,0.04)` — glassmorphism
- `backdrop-filter: blur(10px)` — hiệu ứng kính mờ
- `border: 1px solid rgba(99,102,241,0.25)` → `0.6` khi hover
- `border-radius: 12px`, `transition: border-color 0.2s`
- Dùng cho: VM status card, card Shutdown/Restart

### 5.2 Section Title (`.section-title`)
- Màu `#a5b4fc`, size `0.75rem`, weight 600
- `text-transform: uppercase`, `letter-spacing: 0.1em`
- Dùng phân cấp các nhóm trong sidebar

### 5.3 Login Card (`.login-wrap`)
- Căn giữa trang, `max-width: 420px`, `margin-top: 6rem`
- `border-radius: 20px`, `backdrop-filter: blur(12px)`
- Chứa `st.form` để hỗ trợ nhấn Enter để đăng nhập

### 5.4 Tab Bar
- Tab không active: `#94a3b8`, weight 500
- Tab active: `#a5b4fc` + `border-bottom: #6366f1`
- Override CSS trực tiếp trên `[data-testid="stTabs"] button`

### 5.5 DataFrame
- `border-radius: 10px`, `overflow: hidden`
- Ẩn index (`hide_index=True`), chiều cao cố định 380px cho danh sách tiến trình

---

## 6. Màn hình Đăng nhập

```
[Trang trắng với nền gradient]

        ┌─────────────────────────────┐
        │  🖥️ Remote PC Control       │
        │  Enter your access password  │
        │                             │
        │  [••••••••••••••••]         │  ← st.text_input type=password
        │  [ Sign In →  ]             │  ← st.form_submit_button, Primary
        └─────────────────────────────┘
```

- Card `.login-wrap` nổi giữa trang
- Dùng `st.form` → nhấn **Enter** hoặc click **Sign In** đều hoạt động
- Sai mật khẩu: `st.error` hiển thị ngay trong form

---

## 7. Sidebar — Quản lý Kết nối

Cấu trúc từ trên xuống:

```
🖥️ Remote Control
───────────────────
[VM 1 Card]
  VM 1
  ● Connected / ● Disconnected
[⚡ Connect VM 1]  hoặc  [🔌 Disconnect VM 1]
  └── Nếu lỗi: st.error + expander 🔍 Debug info

[VM 2 Card]
  ...
───────────────────
ACTIVE VM — TABS
  ○ VM 1  ● VM 2      ← st.radio, chỉ hiện khi ≥1 VM connected
───────────────────
SESSION
[🔒 Sign Out]
───────────────────
Remote Control v0.2 · Local Build  (footer mờ)
```

**Logic hiển thị:**
- Nút Connect (Primary, màu đầy) khi VM chưa kết nối
- Nút Disconnect (Secondary, outline) khi VM đã kết nối
- Radio selector chỉ xuất hiện khi có ít nhất 1 VM connected
- Chuyển VM qua radio → tất cả tab tức thì nhắm đến VM mới

---

## 8. Tab Content — Chi tiết Từng Tab

### ⚙️ Processes
```
### ⚙️ Process Manager

▸ [Expander: 🚀 Launch Application / Process]  (mặc định mở)
    [Executable input 4/5 width] [▶️ Launch 1/5 width]

─ danh sách tiến trình ─
🔍 Filter by name: [text input]
[DataFrame: Name | PID | Memory(KB) | Session]   height=380

─── Kill a Process ───
[Process name input] [💀 Kill  ← Primary, 1/4 width]
```

### 📸 Screenshot
```
[📸 Take Screenshot  ← Primary button]

[Ảnh PNG full width khi có kết quả]
[timestamp caption]
[⬇️ Download PNG button]
```

### ⌨️ Keylogger
```
[st.warning: Requires pynput]
[st.slider: 5–60s, bước 5]
[▶️ Start Keylog Capture ← Primary]

[st.code: nội dung log]
[⬇️ Download log button]
```

### 📁 File Transfer
```
[col Upload 50%] | [col Download 50%]
  ⬆️ Upload        |   ⬇️ Download
  [file_uploader]  |   [text_input: filename]
  [Upload to VM]   |   [Download from VM]
```

### 🔴 System Controls
```
[st.error: cảnh báo không thể hoàn tác]

[col Shutdown 50%] | [col Restart 50%]
  [metric-card: ⏻ Shutdown]
  [⏻ Shutdown VM]      ← click 1: warning xác nhận
                        ← click 2: thực thi + disconnect
```

---

## 9. Trạng thái & Phản hồi

| Trạng thái | Component | Màu |
|---|---|---|
| Đang xử lý | `st.spinner("…")` | Mặc định Streamlit |
| Thành công | `st.success("✅ …")` | Xanh lá |
| Cảnh báo / xác nhận | `st.warning("⚠️ …")` | Vàng |
| Lỗi | `st.error("❌ …")` | Đỏ |
| Thông tin | `st.info("🔍 …")` | Xanh dương |
| Kết nối | `● Connected` — `#22c55e` | Xanh lá |
| Ngắt kết nối | `● Disconnected` — `#ef4444` | Đỏ |

---

## 10. Nguyên tắc Thêm Tính năng Mới

1. **Tab mới** → thêm vào tuple `st.tabs([...])`, viết block `with tab_x:` riêng
2. **Card mới** → dùng class `.metric-card` với HTML thủ công qua `st.markdown(..., unsafe_allow_html=True)`
3. **Màu sắc** → chỉ lấy từ bảng màu mục 2, không dùng màu ad-hoc
4. **Hành động nguy hiểm** → luôn dùng pattern xác nhận 2 lần (`confirm_*` trong session_state)
5. **Loading** → luôn bọc thao tác SSH trong `with st.spinner("…")`
