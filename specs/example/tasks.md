# Tasks: Admin V2 - Approvals List

## 1. Parity Audit
- [ ] Đọc toàn bộ legacy source: `app/admin/approvals/page.tsx`.
- [ ] Điền bảng parity với đầy đủ field, action, filter, tab/section, trạng thái UI và điều hướng.
- [ ] Nếu feature đã tồn tại trong admin mới, lập danh sách phần thiếu parity cần vá.

## 2. Modeling
- [ ] Tạo hoặc cập nhật `types/` theo nghĩa nghiệp vụ của legacy.
- [ ] Tạo mock data hoặc adapter trong `api/`.
- [ ] Tạo hook quản lý state trong `hooks/`.

## 3. UI Migration
- [ ] Dựng UI chính cho `/approvals` theo card/layout của admin mới.
- [ ] Dùng `SearchableTable` cho grid chính và giữ filter riêng ngoài bảng nếu legacy có.
- [ ] Đồng bộ button, tag, modal, spacing, table density với theme hiện tại.

## 4. Wiring
- [ ] Thêm route vào `admin/src/app/router/index.tsx`.
- [ ] Cập nhật `AdminShell` nếu màn cần xuất hiện trên navigation và route đã sẵn sàng.
- [ ] Kiểm tra import alias `@/` và cấu trúc feature-based.

## 5. Verification
- [ ] Smoke test đầy đủ thao tác chính so với legacy.
- [ ] Xác nhận parity đạt 100% field và action.
- [ ] Chạy `npm run build` trong `admin/`.

