# Bảo trì FME-CAD

## Nguyên tắc vàng

**Mọi thay đổi của FME chỉ nằm trong thư mục `fme/`.**

Các file ngoài `fme/` là CADCraft gốc đã được `fme/rebrand.py` đổi nhận diện. Lần đồng bộ sau, các file này được tạo lại từ CADCraft mới. **Sửa tay ở đó sẽ bị mất.**

| Muốn làm | Đặt ở đâu |
|---|---|
| Đổi tên, màu, ID, kênh cập nhật, website | `fme/brand.toml` |
| Thay logo | `python3 fme/make_icons.py --from-png logo.png`. Icon sinh ra nằm trong `fme/assets/app-icon/` |
| Thêm file mới, ví dụ crate tính năng riêng | `fme/overlay/<đường dẫn như trong repo>`, ví dụ `fme/overlay/crates/fme-autodim/`. Workspace tự nhận mọi thư mục `crates/*` |
| Sửa một file của CADCraft | Tạo patch: sửa file, chạy `git diff > fme/patches/010-ten.patch`, rồi khôi phục file. `rebrand.py` áp các patch theo thứ tự tên |
| Đổi cách thay tên hoặc patch đích | `fme/rebrand.py` |

## Cập nhật theo CADCraft

**Tự động:** workflow `FME sync CADCraft` chạy mỗi thứ Hai, hoặc chạy tay từ tab Actions. Khi CADCraft có bản mới, workflow:
1. tạo nhánh `sync/upstream-<sha>`;
2. áp nhận diện FME;
3. chạy `cargo check`;
4. mở pull request vào `main`.

Người phụ trách xem và merge pull request đó.

**Chạy tay:**

```bash
git checkout main
```

```bash
bash fme/sync.sh
```

```bash
cargo check --workspace
```

Sau đó đẩy nhánh `sync/upstream-...` lên và mở pull request.

**Vì sao không bao giờ xung đột merge:**
- `sync.sh` tạo cây mới bằng công thức "CADCraft mới + `fme/`", rồi dùng `git merge -s ours` để nối lịch sử FME vào.
- Cây mới luôn sạch, lịch sử vẫn giữ đủ.

**Khi `rebrand.py` báo lỗi "patch không còn khớp":** CADCraft đã sửa đúng đoạn mã mà FME patch. Mở `fme/rebrand.py` (hoặc `fme/patches/`), cập nhật đoạn `old` theo mã mới, rồi chạy lại. Script cố ý dừng chứ không đổi sai một cách im lặng.

## Những gì được đổi (và những gì cố ý giữ)

| Đổi sang FME | Giữ nguyên (để file bản vẽ tương thích hai chiều với CADCraft) |
|---|---|
| Tên hiển thị "CADCraft" thành "FME-CAD" ở menu, tiêu đề, hộp thoại, 19 ngôn ngữ, bộ cài | Tên crate và thư mục mã (`cadcraft-*`) |
| Icon ứng dụng | Font `CADCraft Stroke`, thiết bị in `CADCraft PNG/PDF/SVG` (được ghi vào file bản vẽ) |
| App ID `com.fme.fmecad` (Windows, macOS, Linux) | Biến môi trường `CADCRAFT_*` |
| Thư mục cấu hình riêng (`%APPDATA%\FME-CAD`, `~/.config/fme-cad`) | Tên file chạy `cadcraft(.exe)` (workflow build đổi tên thành `FME-CAD.exe`) |
| Hộp thoại About: FME, kèm dòng "Based on CADCraft" | `AGENTS.md` và tài liệu kỹ thuật trong `docs/` |
| Kênh **tự cập nhật** trỏ sang GitHub Releases của FME (`release_repo`), không bao giờ tải bản ArtCraft đè lên | |
| Gỡ logo ArtCraft (`docs/brand/`). Đây là nhãn hiệu, không được dùng trong bản phân phối của bên khác | |
| Gỡ workflow cần secret của ArtCraft (sonarcloud, release, coderabbit...) | |

## Dùng nội bộ hay phát hành ra ngoài

Cấu hình hiện tại trong `fme/brand.toml` **đủ để dùng nội bộ**:
- App ID `com.fme.fmecad` chỉ cần duy nhất, không cần là tên miền thật.
- Website, trang hỗ trợ để trống, nên dòng liên kết và mục menu tương ứng được ẩn.
- Email người bảo trì chỉ xuất hiện trong gói `.deb` cho Linux.

Chỉ cần điền các giá trị thật khi **phát hành ra ngoài công ty**: tên pháp nhân đầy đủ, website, trang hỗ trợ.

**Tự cập nhật:** ứng dụng kiểm tra GitHub Releases của `release_repo`. Nếu repo để riêng tư, máy người dùng không đọc được (cần đăng nhập), nên bản cài chỉ báo "Could not check for updates". Khi đó phát hành nội bộ qua tab Actions (workflow **FME build**) hoặc ổ chia sẻ của công ty.

**Giấy phép:** MIT/Apache chỉ đặt nghĩa vụ khi phân phối. Dùng nội bộ vẫn giữ nguyên `NOTICE` và `LICENSE-*`, và chúng đã có sẵn trong bản build.
