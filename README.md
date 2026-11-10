# Deploy miễn phí + Phím tắt iPhone

## 1. Deploy lên Render (miễn phí, không cần thẻ)

1. Tạo repo GitHub (private cũng được) chứa: `app.py`, `index.html`, `requirements.txt`, `render.yaml`.
2. Vào render.com → New → **Blueprint** → chọn repo. Render đọc `render.yaml` và tự deploy.
3. Khi xong bạn có địa chỉ dạng `https://tiktok-downloader-xxxx.onrender.com`.
4. Vào tab **Environment** của service, copy giá trị `API_KEY` (Render tự sinh). Đây là mật khẩu của API.

Lưu ý gói free: không dùng 15 phút thì server ngủ, lần gọi đầu mất khoảng 30–50 giây để thức dậy.
Giữ `-w 1` trong lệnh khởi động (đã có sẵn trong `render.yaml`), vì link tải lưu trong bộ nhớ.

### Giữ server luôn thức (UptimeRobot, miễn phí)

1. Đăng ký uptimerobot.com → **Add New Monitor**.
2. Loại **HTTP(s)**, URL: `https://TEN-MIEN.onrender.com/health`, chu kỳ **5 phút**.
3. Xong. Render chỉ ngủ khi 15 phút không có lượt truy cập, nên được gọi mỗi 5 phút thì luôn thức.

Đây là cách lách, Render có thể thay đổi chính sách. Gói free có 750 giờ mỗi tháng, đủ cho một dịch vụ chạy cả tháng, nên đừng tạo thêm dịch vụ khác trên cùng tài khoản.

### Tiết kiệm băng thông (Render free chỉ có 5 GB mỗi tháng)

Thêm trường `mode` = `redirect` vào bước Lấy nội dung của URL (xem mục 3). Khi đó server chỉ trả địa chỉ gốc và iPhone tự tải thẳng từ nguồn, gần như không tốn băng thông. Nếu cách này bị lỗi (tải ra file hỏng hoặc 403), xoá trường `mode` để quay lại chế độ tải qua server.

## 2. API

| Đường dẫn | Việc |
|---|---|
| `/api/v1/video` | Trả thẳng file mp4 không watermark (ưu tiên HD). Thêm `wm=1` để lấy bản có watermark. |
| `/api/v1/info` | Trả JSON: `video_best`, `video_hd`, `video`, `video_watermark`, `music`, `images` (danh sách link qua server, hết hạn sau 15 phút) và `direct` (link gốc từ nguồn, không tốn băng thông). |
| `/health` | Trả `ok`, để UptimeRobot gọi giữ server thức. |

Gửi bằng GET hoặc POST với các tham số `url` và `key` (hoặc header `X-API-Key`).
Với Phím tắt nên dùng **POST + Form** vì link TikTok có dấu `&`, nếu ghép vào đường dẫn sẽ bị cắt.

Thử nhanh trên máy tính:
```
curl -X POST https://TEN-MIEN.onrender.com/api/v1/video \
  -F "url=https://vt.tiktok.com/xxxx/" -F "key=KEY_CUA_BAN" -o video.mp4
```

## 3. Phím tắt iPhone: tải video

Mở app **Phím tắt** → dấu **+** → đặt tên "Tải TikTok", rồi thêm các hành động:

1. **Nhận đầu vào từ Share Sheet**: bật *Hiển thị trong Trang tính chia sẻ* (Show in Share Sheet), loại đầu vào chọn **URL** và **Văn bản**.
2. **Lấy nội dung của URL** (Get Contents of URL):
   - URL: `https://TEN-MIEN.onrender.com/api/v1/video`
   - Bấm *Hiện thêm* → Phương thức: **POST** → Nội dung yêu cầu: **Biểu mẫu** (Form)
   - Thêm trường **Văn bản** `url` = biến *Đầu vào phím tắt* (Shortcut Input)
   - Thêm trường **Văn bản** `key` = key của bạn
   - Thêm trường **Văn bản** `mode` = `redirect` (tiết kiệm băng thông, xem mục 1)
3. **Lưu vào album ảnh** (Save to Photo Album), đầu vào là *Nội dung của URL*.
4. (Tuỳ chọn) **Hiện thông báo**: "Đã lưu video".

Cách dùng: trong TikTok bấm **Chia sẻ → Sao chép liên kết**, hoặc **Chia sẻ → Khác → Tải TikTok**. Nếu chạy từ danh sách phím tắt thì thêm hành động **Lấy clipboard** ở đầu và dùng nó thay cho *Đầu vào phím tắt*.

### Bài ảnh (slideshow)
Dùng `/api/v1/info` thay cho `/api/v1/video`, sau đó:
1. **Lấy giá trị từ từ điển** → khoá `images` → **Lặp lại với từng mục** (Repeat with Each)
2. Trong vòng lặp: **Lấy nội dung của URL** (GET, URL là *Mục lặp lại*) → **Lưu vào album ảnh**.

## 4. Lưu ý

- **Bảo mật:** luôn đặt `API_KEY`. Không có key, ai biết địa chỉ cũng dùng được và làm bạn hết giới hạn băng thông.
- TikTok có thể chặn IP của máy chủ miễn phí. API dùng tikwm nên thường vẫn chạy, nhưng nếu tikwm đổi cách hoạt động thì cần cập nhật `fetch_tikwm`.
- Nút upscale 4K và yt-dlp trên giao diện web cần ffmpeg, mà Render free không có sẵn. Phần đó tự ẩn, còn API và tải thường không bị ảnh hưởng.
