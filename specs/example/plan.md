# Plan: Admin V2 - Approvals List

## 1. Nguyên tắc triển khai
- Nguồn sự thật là legacy page trong `app/admin`.
- Màn admin mới hiện có chỉ là audit target; nếu thiếu parity thì phải vá bổ sung.
- Không để lại "quyết định cần chốt" mở trong lúc triển khai.
- `SearchableTable` là grid chuẩn cho màn list/report/dashboard.

## 2. Luồng triển khai
1. Đọc legacy source và điền bảng parity bằng field/action cụ thể.
2. Tạo hoặc cập nhật `types/`, `api/`, `hooks/` và data snapshot cần thiết.
3. Dựng UI chính cho `/approvals` theo Antd mới và giữ đầy đủ parity.
4. Nối route vào router; chỉ cập nhật menu nếu route đã tồn tại và cần xuất hiện trong navigation.
5. Build `admin` và smoke test luồng chính của màn hình.

## 3. Tích hợp kỹ thuật
- `components/`: màn chính và các block UI con.
- `types/`: type hiển thị, enum, form model.
- `api/`: mock snapshot hoặc adapter bám dữ liệu legacy.
- `hooks/`: orchestration state, CRUD local, filter UI.
- `services/`: chỉ thêm khi có transform nghiệp vụ đáng kể.

## 4. Quy tắc parity đã khóa
- Không tự lược bớt field, action, tab hoặc filter so với legacy.
- Không dùng lại `PageHeader` cũ.
- Giữ filter riêng ngoài bảng nếu legacy có và không trùng filter cột.
- Ghi rõ mọi khác biệt bắt buộc giữa legacy và admin mới trong PR checklist.

## 5. Kiểm thử
- Parity 100% về field và action.
- Route `/approvals` mở được và điều hướng liên quan hoạt động đúng.
- Search/filter/sort/pagination trong bảng hoạt động đúng với `SearchableTable`.
- `npm run build` trong `admin/` pass sau khi hoàn tất.

