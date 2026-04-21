# Spec: Admin V2 - Approvals List

## 1. Bối cảnh
Trang legacy tương ứng trong `app/admin/approvals/page.tsx` chưa được migrate hoàn chỉnh sang workspace `admin/` dùng Ant Design. Cần tạo hoặc cập nhật màn tương ứng trong admin mới theo kiến trúc feature-based hiện tại.

## 2. Mục tiêu
- Migrate màn `/approvals` sang UI Antd mới.
- Nguồn sự thật nội dung là legacy page trong `app/admin`, không phải màn admin mới đã có sẵn.
- Giữ lại đầy đủ field, action, filter, tab/section và điều hướng cốt lõi từ trang cũ.

## 3. Nguồn tham chiếu
### Legacy source of truth
- [app/admin/approvals/page.tsx](/C:/Users/ThangHoang/Documents/court-management/app/admin/approvals/page.tsx)

### Điểm neo admin mới
- [AppRouter](/C:/Users/ThangHoang/Documents/court-management/admin/src/app/router/index.tsx)
- [AdminShell](/C:/Users/ThangHoang/Documents/court-management/admin/src/shared/components/layout/AdminShell.tsx)
- [SearchableTable](/C:/Users/ThangHoang/Documents/court-management/admin/src/shared/components/table/SearchableTable.tsx)
- [VenuesMain.tsx](/C:/Users/ThangHoang/Documents/court-management/admin/src/features/venues/components/VenuesMain.tsx)

## 4. Phạm vi bắt buộc
- Tạo hoặc cập nhật feature tương ứng trong `admin/src/features`.
- Tạo route mới cho `/approvals` trong admin workspace hoặc audit route hiện có nếu màn đã tồn tại.
- Migrate UI, state, mock data và action cần thiết của màn cũ.
- Đồng bộ layout, spacing, filter, table, form theo chuẩn admin mới nhưng không làm mất nghiệp vụ legacy.

## 5. Bảng parity bắt buộc
| Hạng mục | Yêu cầu tối thiểu | Đã đối chiếu |
| --- | --- | --- |
| Legacy route | `app/admin/approvals/page.tsx` | [ ] |
| Target route | `/approvals` | [ ] |
| Field hiển thị | Liệt kê đầy đủ field/column/card/summary từ legacy trước khi code | [ ] |
| Thao tác | Liệt kê đủ create/edit/delete/view/export/approve/navigation từ legacy | [ ] |
| Filter/Search | Liệt kê đủ search, filter, tab, date-range, trạng thái | [ ] |
| Tab/Section | Liệt kê đủ section, card, bảng con, panel, tab | [ ] |
| Trạng thái UI | Ghi rõ empty/loading/error/disabled và điều kiện hiển thị | [ ] |
| Điều hướng liên quan | Ghi rõ link sang create/edit/detail/schedule/report nếu legacy có | [ ] |

## 6. Functional Requirements
1. Không được bắt đầu code khi bảng parity chưa được điền bằng field/action cụ thể từ legacy.
2. Không được tự ý bỏ field hoặc action chỉ để giao diện gọn hơn.
3. Grid chính phải dùng `SearchableTable`; nếu legacy có filter riêng ngoài bảng và không trùng filter cột thì phải giữ lại.
4. Nếu feature đã tồn tại trong admin mới, phải audit lại và vá phần thiếu parity thay vì xem như hoàn tất.
5. Action chính đặt trong vùng card/action của bố cục hiện tại, không thêm lại `PageHeader` cũ.

## 7. UI Requirements
- Bố cục mặc định dùng card chính của admin mới và shell hiện tại.
- Typography, spacing, button size, tag, table row height phải theo theme Antd hiện tại.
- Không tái sử dụng Webix/Tailwind UI từ `app/admin`.

## 8. Data Mapping
- Map field legacy sang type/component mới theo nghĩa nghiệp vụ tương đương.
- Chuẩn hóa tên field, enum, trạng thái hiển thị và action payload nếu cần.
- Ghi rõ field nào bị gộp, biến đổi hoặc không migrate được và lý do.

## 9. Acceptance Criteria
1. Khi mở route `/approvals`, giao diện hiển thị đúng màn hình tương ứng trong admin mới.
2. Người dùng có thể thực hiện đầy đủ action cốt lõi như trang cũ.
3. Bảng parity đạt 100% field và action so với legacy.
4. UI đồng bộ với shell mới và không còn phụ thuộc layout cũ trong `app/admin`.
5. Build `admin` pass sau khi migrate.

## 10. Technical Notes
- Loại màn: List
- Route đích: `/approvals`
- Mặc định đã khóa: route riêng cho create/edit/detail/schedule; list/report dùng `SearchableTable`; menu chỉ cập nhật khi route đã tồn tại.

