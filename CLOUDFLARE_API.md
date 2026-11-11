# API riêng trên Cloudflare Workers (miễn phí, luôn bật)

Giống API trên Render nhưng chạy ở Cloudflare: **không ngủ**, không cần UptimeRobot, IP khác Render (có thể không bị tikwm chặn).
Cùng đường dẫn nên Phím tắt chỉ cần **đổi địa chỉ**.

| Có | Không có (vẫn dùng bản Render) |
|---|---|
| `/api/v1/info`, `/video`, `/music`, `/image`, `/get`, `/health`, `/relay` | AI, ZIP, `fmt=jpg`, bản chất lượng cao yt-dlp, giao diện web |

## Cài đặt (khoảng 5 phút)
1. Tạo tài khoản miễn phí ở cloudflare.com.
2. **Workers & Pages → Create → Create Worker** (mẫu Hello World), đặt tên `beysnap-api` → **Deploy**.
3. Bấm **Edit code**, xoá hết, dán toàn bộ nội dung `cloudflare-api-worker.js` → **Deploy**.
4. **Settings → Variables and Secrets → Add**: loại **Secret**, tên `API_KEY`, giá trị là một chuỗi dài tự đặt (**tạo khoá mới**, đừng dùng lại khoá đã từng gửi cho ai) → **Deploy**.
5. Địa chỉ của bạn có dạng `https://beysnap-api.TEN_BAN.workers.dev`.

## Thử trước khi làm Phím tắt
Mở Safari (hoặc trình duyệt bất kỳ):
```
https://beysnap-api.TEN_BAN.workers.dev/api/v1/info?url=LINK_TIKTOK&key=API_KEY
```
- Ra JSON có `video_best`, `music`… là chạy tốt.
- Ra `HTTP 403 (tikwm chặn IP máy chủ)` là tikwm chặn cả Cloudflare, hãy dùng Phím tắt trực tiếp (`PHIM_TAT_TIKWM_TRUC_TIEP.md`) hoặc đổi máy chủ.

## Sửa Phím tắt
Giữ nguyên mọi thứ (POST, Form, `url`, `key`), chỉ đổi địa chỉ trong **Get Contents of URL**:
`https://tiktok-downloader-ddi5.onrender.com/api/v1/video` → `https://beysnap-api.TEN_BAN.workers.dev/api/v1/video`
Menu video/nhạc/ảnh trong `PROMPT_PHIM_TAT_IPHONE.md` dùng `/api/v1/info` nên cũng chỉ cần đổi địa chỉ.

## Dùng Worker làm cầu nối cho Render (tuỳ chọn)
Nếu muốn giữ web và AI trên Render nhưng tikwm chặn IP Render, thêm trên Render → Environment:
- `TIKWM_RELAY` = `https://beysnap-api.TEN_BAN.workers.dev/relay`
- `RELAY_KEY` = đúng giá trị `API_KEY` đã đặt trong Worker

## Giới hạn gói miễn phí (theo tài liệu Cloudflare)
100.000 yêu cầu mỗi ngày; 10 ms thời gian CPU mỗi yêu cầu (chuyển tiếp file dạng stream không tốn CPU đáng kể); trang tài liệu không nêu giới hạn băng thông cho phản hồi stream. Chỉ dùng cá nhân.
